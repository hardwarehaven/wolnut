from dataclasses import dataclass, field
from typing import Union
import yaml
import logging
import os
import sys

from wolnut.client import (
    BaseClientConfig,
    ClientConfig,
    create_client_config,
)
from wolnut.client import WolClientConfig
from wolnut.client import IdracClientConfig
from wolnut.client import IloClientConfig
from wolnut.client import SmIpmiClientConfig

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
class WolnutConfig:
    nut: NutConfig
    poll_interval: int = 10
    wake_on: WakeOnConfig = field(default_factory=WakeOnConfig)
    clients: list[ClientConfig] = field(default_factory=list)
    log_level: str = "INFO"


def load_config(path: str | None = None) -> WolnutConfig:
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

    clients: list[ClientConfig] = []
    for raw_client in raw["clients"]:
        try:
            client = create_client_config(raw_client)
            client.post_process()  # Post-process client config
            clients.append(client)
        except Exception as e:
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
        logger.info(client.description())

    logger.info("WOLnut is ready to go!")

    return wolnut_config


def validate_config(raw: dict):
    if "clients" not in raw or not isinstance(raw["clients"], list):
        raise ValueError("Missing or invalid 'clients' list")

    if "nut" not in raw or "ups" not in raw["nut"]:
        raise ValueError("Missing required field: 'nut.ups'")

    for i, client in enumerate(raw.get("clients", [])):
        BaseClientConfig.validate_raw(client)
