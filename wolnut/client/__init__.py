"""
A module defining various client configurations for different types of clients
such as WOL, iDRAC, iLO, and Supermicro IPMI.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union, override

from wolnut.client.idrac import power_on_idrac_client
from wolnut.client.ilo import power_on_ilo_client
from wolnut.client.sm_ipmi import power_on_sm_ipmi_client
from wolnut.client.wol import send_wol_packet
from wolnut.utils import resolve_mac_from_host, validate_mac_format

logger = logging.getLogger("wolnut")


# Base client config for common fields
@dataclass
class BaseClientConfig(ABC):
    name: str

    @property
    @abstractmethod
    def type(self) -> str:
        """Return the type of client"""
        ...

    @classmethod
    def validate_raw(cls, raw: dict, i: int | None = None) -> None:
        """Validate a raw client configuration"""
        cls.__validate_shared_fields(raw, i)
        # determine what kind of client this is
        match raw.get("type"):
            case "wol" | None:
                WolClientConfig._validate_subclass_fields(raw)
            case "idrac":
                IdracClientConfig._validate_subclass_fields(raw)
            case "ilo":
                IloClientConfig._validate_subclass_fields(raw)
            case "sm_ipmi":
                SmIpmiClientConfig._validate_subclass_fields(raw)
            case unsupported_type:
                raise ValueError(
                    f"Client {raw['name']} has an unknown or unsupported type: {unsupported_type}"
                )

    @classmethod
    def __validate_shared_fields(cls, raw: dict, i: int | None = None) -> None:
        """Validate shared fields across all client types"""
        if i is not None:
            prefix = f"Client #{i} is missing required field: "
        else:
            prefix = "Client is missing required field: "

        if "name" not in raw or not raw["name"]:
            raise ValueError(f"{prefix} name")

    @classmethod
    @abstractmethod
    def _validate_subclass_fields(cls, raw: dict) -> None:
        """Validate a specific raw client configuration - implemented by subclasses"""
        ...

    def post_process(self) -> None:
        """Post-process the client configuration after validation"""
        return

    def description(self) -> str:
        """Return a human-readable description of the client configuration"""
        return f"{self.type} Client: {self.name}"

    @abstractmethod
    def send_power_on_signal(self) -> bool:
        """Send the power-on signal to the client"""
        ...


@dataclass
class WolClientConfig(BaseClientConfig):
    host: str
    mac: str

    @property
    def type(self) -> str:
        return "wol"

    @override
    @classmethod
    def _validate_subclass_fields(cls, raw: dict) -> None:
        # Validate WOL specific fields
        if "host" not in raw or not raw["host"]:
            raise ValueError(
                f"WOL client '{raw['name']}' is missing required field: host"
            )
        if "mac" not in raw or not raw["mac"]:
            raise ValueError(
                f"WOL client '{raw['name']}' is missing required field: mac"
            )
        validate_mac_format(raw["mac"])

    @override
    def description(self) -> str:
        """Return a human-readable description of the WOL client configuration"""
        return (
            f"WOL Client: {self.name} at {self.host} with MAC {self.mac}"
            if self.mac
            else f"WOL Client: {self.name} at {self.host} (MAC not set)"
        )

    @override
    def post_process(self) -> None:
        """
        Post-process the WOL client configuration after validation.
        - if the MAC address is set to "auto", resolve it from the host.
        - validate the MAC address format if it is not "auto".
        """
        # Resolve MAC address if set to "auto"
        if self.mac == "auto":
            logger.info(
                f"Resolving MAC for {self.name} at {self.host}...",
            )
            resolved_mac = resolve_mac_from_host(self.host)
            if not resolved_mac:
                raise ValueError(
                    f"Could not resolve MAC for {self.name} at {self.host}"
                )
            self.mac = resolved_mac
            logger.info(f"Resolved MAC for {self.name}: {self.mac}")
        # Validate MAC address format otherwise
        elif not validate_mac_format(self.mac):
            raise ValueError(f"Invalid MAC format for {self.name}: {self.mac}")

    @override
    def send_power_on_signal(self) -> bool:
        """
        Send a Wake-on-LAN packet to the client.

        Returns:
            bool: True if the packet was sent successfully, False otherwise.
        """
        return send_wol_packet(self.mac, self.host)


@dataclass
class IdracClientConfig(BaseClientConfig):
    host: str
    ipmi_host: str
    username: str
    password: str
    verify_ssl: bool = False

    @property
    def type(self) -> str:
        return "idrac"

    @override
    @classmethod
    def _validate_subclass_fields(cls, raw: dict) -> None:
        # Validate iDRAC specific fields
        if "host" not in raw or not raw["host"]:
            raise ValueError(
                f"iDRAC client '{raw['name']}' is missing required field: host"
            )
        if "ipmi_host" not in raw or not raw["ipmi_host"]:
            raise ValueError(
                f"iDRAC client '{raw['name']}' is missing required field: ipmi_host"
            )
        if "username" not in raw or not raw["username"]:
            raise ValueError(
                f"iDRAC client '{raw['name']}' is missing required field: username"
            )
        if "password" not in raw or not raw["password"]:
            raise ValueError(
                f"iDRAC client '{raw['name']}' is missing required field: password"
            )

    @override
    def send_power_on_signal(self) -> bool:
        # Send power on signal via iDRAC
        return power_on_idrac_client(
            self.ipmi_host, self.username, self.password, self.verify_ssl
        )


@dataclass
class IloClientConfig(BaseClientConfig):
    host: str
    ipmi_host: str
    username: str
    password: str
    verify_ssl: bool = False

    @property
    def type(self) -> str:
        return "ilo"

    @override
    @classmethod
    def _validate_subclass_fields(cls, raw: dict) -> None:
        # Validate iLO specific fields
        if "host" not in raw or not raw["host"]:
            raise ValueError(
                f"iLO client '{raw['name']}' is missing required field: host"
            )
        if "ipmi_host" not in raw or not raw["ipmi_host"]:
            raise ValueError(
                f"iLO client '{raw['name']}' is missing required field: ipmi_host"
            )
        if "username" not in raw or not raw["username"]:
            raise ValueError(
                f"iLO client '{raw['name']}' is missing required field: username"
            )
        if "password" not in raw or not raw["password"]:
            raise ValueError(
                f"iLO client '{raw['name']}' is missing required field: password"
            )

    @override
    def send_power_on_signal(self) -> bool:
        """
        Send a power-on signal to the iLO client.

        Returns:
            bool: True if the power-on command was sent successfully, False otherwise.
        """
        return power_on_ilo_client(
            self.ipmi_host,
            self.username,
            self.password,
            self.verify_ssl,
        )


@dataclass
class SmIpmiClientConfig(BaseClientConfig):
    host: str
    ipmi_host: str
    username: str
    password: str

    @property
    def type(self) -> str:
        return "sm_ipmi"

    @override
    @classmethod
    def _validate_subclass_fields(cls, raw: dict) -> None:
        # Validate Supermicro IPMI specific fields
        if "host" not in raw or not raw["host"]:
            raise ValueError(
                f"Supermicro IPMI client '{raw['name']}' is missing required field: host"
            )
        if "ipmi_host" not in raw or not raw["ipmi_host"]:
            raise ValueError(
                f"Supermicro IPMI client '{raw['name']}' is missing required field: ipmi_host"
            )
        if "username" not in raw or not raw["username"]:
            raise ValueError(
                f"Supermicro IPMI client '{raw['name']}' is missing required field: username"
            )
        if "password" not in raw or not raw["password"]:
            raise ValueError(
                f"Supermicro IPMI client '{raw['name']}' is missing required field: password"
            )

    @override
    def send_power_on_signal(self) -> bool:
        """
        Send a power-on signal to the Supermicro IPMI client.

        Returns:
            bool: True if the power-on command was sent successfully, False otherwise.
        """
        return power_on_sm_ipmi_client(
            self.ipmi_host,
            self.username,
            self.password,
        )


# Tagged union type for all client configurations
ClientConfig = Union[
    WolClientConfig, IdracClientConfig, IloClientConfig, SmIpmiClientConfig
]


def create_client_config(raw: dict) -> ClientConfig:
    """Create a client configuration based on the raw data provided."""
    # determine the type of client from the raw data
    client_type = raw.get("type")
    # Copy the raw data to avoid modifying the original
    raw_copy = raw.copy()
    # remove the type field from raw to avoid passing it to the dataclass
    raw_copy.pop("type", None)
    BaseClientConfig.validate_raw(raw)
    match client_type:
        case "wol" | None:
            return WolClientConfig(**raw_copy)
        case "idrac":
            return IdracClientConfig(**raw_copy)
        case "ilo":
            return IloClientConfig(**raw_copy)
        case "sm_ipmi":
            return SmIpmiClientConfig(**raw_copy)
        case _:
            raise ValueError(f"Unknown client type: {client_type}")
