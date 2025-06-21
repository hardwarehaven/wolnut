import subprocess
import logging
import platform
from typing import Optional
from wolnut.apprise_logging import apprise_notifier

logger = apprise_notifier("wolnut")


def get_ups_status(ups_name: str, username: Optional[str] = None, password: Optional[str] = None) -> dict:
    env = None

    if username and password:
        env = {
            **subprocess.os.environ,
            "USERNAME": username,
            "PASSWORD": password
        }

    try:
        result = subprocess.run(
            ["upsc", ups_name],
            capture_output=True,
            text=True,
            env=env,
            timeout=5,
            check=False
        )

        if result.returncode != 0:
            logger.error(f"upsc returned error: {result.stderr.strip()}")
            return {}

        status = {}
        for line in result.stdout.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                status[key.strip()] = value.strip()

        return status

    except Exception as e:
        logger.error(f"Failed to get UPS status: {e}")
        return {}


def is_client_online(host: str) -> bool:
    try:
        count_flag = "-n" if platform.system().lower() == "windows" else "-c"
        result = subprocess.run(
            ["ping", count_flag, "1", host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        logger.debug(f"Host: {host} Online: {result.returncode == 0}")
        return result.returncode == 0
    except Exception as e:
        logger.warning(f"Failed to ping {host}: {e}")
        return False
