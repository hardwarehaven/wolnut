import logging
import yaml

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from wolnut.state import DEFAULT_STATE_FILEPATH
from wolnut.utils import validate_mac_format, resolve_mac_from_host

logger = logging.getLogger("wolnut")

DEFAULT_CONFIG_FILEPATHS = ["/config/config.yaml", "./config.yaml"]
DEFAULT_LOG_LEVEL = "INFO"


@dataclass
class NutConfig:
    ups: str
    port: int = 3493
    timeout: int = 5
    username: str | None = None
    password: str | None = None


@dataclass
class WakeOnConfig:
    restore_delay_sec: int = 30
    min_battery_percent: int = 20
    client_timeout_sec: int = 360
    reattempt_delay: int = 30


@dataclass
class ClientConfig:
    name: str
    host: str
    mac: str  # "auto" supported


@dataclass
class WolnutConfig:
    nut: NutConfig
    status_file: str
    poll_interval: int = 10
    wake_on: WakeOnConfig = field(default_factory=WakeOnConfig)
    clients: list[ClientConfig] = field(default_factory=list)
    log_level: str = "INFO"


def find_state_file(state_file: Optional[str] = None) -> str:
    """Find an existing state file or return a writable default path."""
    path = Path(state_file or DEFAULT_STATE_FILEPATH)
    if not state_file:
        logger.warning("No state file specified, using default: %s", path)

    # Ensure the parent directory exists
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error("Could not create directory for state file '%s': %s", path, e)
        # Depending on desired behavior, you might want to exit or raise here.

    return str(path)


def load_config(
    config_path: str, status_path: str = None, verbose: bool = False
) -> Optional[WolnutConfig]:
    try:
        with open(config_path, "r") as f:
            raw = yaml.safe_load(f)
        validate_config(raw)
    except FileNotFoundError:
        logger.error("Config file not found at '%s'.", config_path)
        return None
    except Exception:
        logger.exception("Failed to load or parse config file: '%s'.\n", config_path)
        return None

    # LOGGING...
    nut = NutConfig(**raw["nut"])

    # get wake_on or use defaults
    wake_on = WakeOnConfig(**raw.get("wake_on", {}))

    # Determine status file path: CLI arg > config file > default
    final_status_path = status_path or raw.get("status_file")
    # find_state_file will handle None and also ensure the directory exists
    final_status_path = find_state_file(final_status_path)

    clients = []
    for raw_client in raw["clients"]:
        try:
            mac = raw_client["mac"]
            if mac == "auto":
                logger.info(
                    "Resolving MAC for %s at %s...",
                    raw_client["name"],
                    raw_client["host"],
                )
                resolved_mac = resolve_mac_from_host(raw_client["host"])
                if not resolved_mac:
                    raise ValueError(
                        f"Could not resolve MAC address for {raw_client['name']} ({raw_client['host']})"
                    )
                raw_client["mac"] = resolved_mac
                logger.info("MAC for %s: %s", raw_client["name"], resolved_mac)

            clients.append(ClientConfig(**raw_client))
        except ValueError as e:
            logger.error("Failed to load client %s: %s", raw_client.get("name", "?"), e)

    wolnut_config = WolnutConfig(
        nut=nut,
        poll_interval=raw.get("poll_interval", 10),
        wake_on=wake_on,
        clients=clients,
        log_level=raw.get("log_level", DEFAULT_LOG_LEVEL).upper(),
        status_file=final_status_path,
    )
    logger.info("Config Imported Successfully")
    for client in wolnut_config.clients:
        logger.info("Client: %s at MAC: %s", client.name, client.mac)

    return wolnut_config


def validate_config(raw: dict):
    if "clients" not in raw or not isinstance(raw["clients"], list):
        raise ValueError("Missing or invalid 'clients' list")

    if "nut" not in raw or "ups" not in raw["nut"]:
        raise ValueError("Missing required field: 'nut.ups'")

    if "status_file" not in raw:
        logger.warning("No 'status_file' specified in config, using default.")

    for i, client in enumerate(raw["clients"]):
        if "name" not in client:
            raise ValueError(f"Client #{i} is missing required field: 'name'")
        if "host" not in client:
            raise ValueError(
                f"Client '{client.get('name', '?')}' is missing required field: 'host'"
            )
        if "mac" not in client:
            raise ValueError(
                f"Client '{client['name']}' is missing required field: 'mac'"
            )

        mac = client["mac"]
        if not isinstance(mac, str):
            raise ValueError(
                f"Client '{client['name']}' has invalid mac format (should be string or 'auto')"
            )
        if mac != "auto" and not validate_mac_format(mac):
            raise ValueError(
                f"Client '{client['name']}' has invalid MAC address format: {mac}"
            )
