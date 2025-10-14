import logging
import platform
import subprocess
from typing import TYPE_CHECKING

try:
    from PyNUT import PyNUTClient, PyNUTError
except ImportError:
    PyNUTClient = None
    PyNUTError = Exception

if TYPE_CHECKING:
    from wolnut.config import NutConfig

logger = logging.getLogger("wolnut")


def get_ups_status(nut_config: "NutConfig") -> dict:
    """
    Get UPS status using PyNUTClient.

    Args:
        nut_config: NutConfig object containing connection details

    Returns:
        Dictionary of UPS variables (str -> str), or empty dict on error
    """
    if PyNUTClient is None:
        logger.error("PyNUTClient is not available. Please install: pip install PyNUTClient")
        return {}

    try:
        # Connect to NUT server
        client = PyNUTClient(
            host=nut_config.host,
            port=nut_config.port,
            login=nut_config.username,
            password=nut_config.password,
            timeout=nut_config.timeout
        )

        # Get all variables for the UPS
        raw_vars = client.GetUPSVars(nut_config.ups)

        # Convert byte strings to regular strings (Python 3 compatibility)
        status = {}
        for key, value in raw_vars.items():
            # Decode bytes to strings
            str_key = key.decode('utf-8') if isinstance(key, bytes) else key
            str_value = value.decode('utf-8') if isinstance(value, bytes) else value
            status[str_key] = str_value

        return status

    except PyNUTError as e:
        logger.error("PyNUT error: %s", e)
        return {}
    except Exception as e:
        logger.error("Failed to get UPS status: %s", e)
        return {}


def is_client_online(host: str) -> bool:
    try:
        count_flag = "-n" if platform.system().lower() == "windows" else "-c"
        result = subprocess.run(
            ["ping", count_flag, "1", host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        logger.debug("Host: %s Online: %s", host, result.returncode == 0)
        return result.returncode == 0
    except Exception as e:
        logger.warning("Failed to ping %s: %s", host, e)
        return False
