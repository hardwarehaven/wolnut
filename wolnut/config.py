from dataclasses import dataclass, field
import yaml
import logging
import os
import sys

from wolnut.utils import validate_mac_format, resolve_mac_from_host

logger = logging.getLogger("wolnut")


@dataclass
class NutConfig:
    ups: str
    hostname: str = "localhost"
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
    poll_interval: int = 10
    wake_on: WakeOnConfig = field(default_factory=WakeOnConfig)
    clients: list[ClientConfig] = field(default_factory=list)
    log_level: str = "INFO"


def load_config(path: str = None) -> WolnutConfig:

    if path is None:
        # Prefer /config/config.yaml if it exists
        default_path = "/config/config.yaml"
        if os.path.exists(default_path):
            path = default_path
        else:
            path = "config.yaml"

    try:
        with open(path, "r") as f:
            raw = yaml.safe_load(f)
        validate_config(raw)
    except FileNotFoundError:
        logger.error("Config file not found at '%s'.", path)
        sys.exit(1)
    except Exception as e:
        logger.error("Failed to load or parse config file: %s", e)
        sys.exit(1)

    # LOGGING...
    nut = NutConfig(**raw["nut"])

    # get wake_on or use defaults
    wake_on = WakeOnConfig(**raw.get("wake_on", {}))

    # LOGGING...

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
        log_level=raw.get("log_level", "INFO").upper(),
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
