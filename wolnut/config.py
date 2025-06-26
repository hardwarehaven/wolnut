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
    type: str  # e.g., "wol", "idrac", "ilo", "sm_ipmi"
    host: str
    ipmi_host: str | None = None
    mac: str | None = None         # Only for WOL
    username: str | None = None    # Only for idrac/ilo
    password: str | None = None
    verify_ssl: bool = False       # Optional for idrac/ilo



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
            client_type = raw_client.get("type")
            if client_type == "wol":
                mac = raw_client.get("mac")
                if mac == "auto":
                    logger.info("Resolving MAC for %s at %s...", raw_client['name'], raw_client['host'])
                    resolved_mac = resolve_mac_from_host(raw_client["host"])
                    if not resolved_mac:
                        raise ValueError(f"Could not resolve MAC for {raw_client['name']}")
                    raw_client["mac"] = resolved_mac
                    logger.info("MAC for %s: %s", raw_client['name'], resolved_mac)
                elif not validate_mac_format(mac):
                    raise ValueError(f"Invalid MAC format for {raw_client['name']}: {mac}")

            clients.append(ClientConfig(**raw_client))
        except Exception as e:
            logger.error("Failed to load client %s: %s", raw_client.get("name", "?"), e)

    wolnut_config = WolnutConfig(
        nut=nut,
        poll_interval=raw.get("poll_interval", 10),
        wake_on=wake_on,
        clients=clients,
        log_level=raw.get("log_level", "INFO").upper()
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

    for i, client in enumerate(raw.get("clients", [])):
        if "name" not in client or "host" not in client or "type" not in client:
            raise ValueError(f"Client #{i} is missing 'name', 'host', or 'type'")
        if client["type"] == "wol":
            if "mac" not in client:
                raise ValueError(f"WOL client '{client['name']}' is missing 'mac'")
        elif client["type"] in ["idrac", "ilo", "sm_ipmi"]:
            for key in ["username", "password"]:
                if key not in client:
                    raise ValueError(f"{client['type']} client '{client['name']}' is missing '{key}'")
            if "ipmi_host" not in client:
                    raise ValueError(f"Client '{client['name']}' of type {client['type']} must have 'ipmi_host'")
        else:
            raise ValueError(f"Unsupported client type: {client['type']}")

