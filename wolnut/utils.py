from subprocess import Popen, PIPE
import re
import logging
from typing import Optional

_MAC_ADDRESS_PATTERN = re.compile(r"([0-9A-Fa-f]{2}[:\-]){5}([0-9A-Fa-f]{2})")
logger = logging.getLogger("wolnut")


def validate_mac_format(mac: str) -> bool:
    """
    Validates that a given MAC address is va;id.

    Args:
        mac (str): MAC address.

    Returns:
        bool: True if valid.
    """
    return _MAC_ADDRESS_PATTERN.fullmatch(mac) is not None


def resolve_mac_from_host(host: str) -> Optional[str]:
    """
    Attempts to resolve MAC address with provided hostname or IP.

    Args:
        host (str): IP or Hostname.

    Returns:
        Optional[str]: The MAC address as a colon-separated string if found,
        otherwise None.
    """
    # FIXME: is it really necessary to ping before running ARP? 
    # if cache is not populated, it should be resolved correctly; if not this hints at a deeper bug

    # Send a ping to ensure the ARP cache is populated
    try:
        Popen(["ping", "-c", "1", host]).communicate()
    except Exception as e:
        logger.warning("Failed to ping: %s: %s", host, e)
        return

    # Read the ARP table
    try:
        out = Popen(["arp", "-n", host], text=True, stdout=PIPE).communicate()
        if (match := _MAC_ADDRESS_PATTERN.search(out)):
            return match.group(0)
    except Exception as e:
        logger.warning("Failed to resolve ARP for: %s: %s", host, e)
