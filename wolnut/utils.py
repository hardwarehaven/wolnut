import subprocess
import re
import logging
from wolnut.apprise import apprise_notifier

logger = apprise_notifier("wolnut")


def validate_mac_format(mac: str) -> bool:
    """
    Validates that a given MAC address is va;id.

    Args:
        mac (str): MAC address.

    Returns:
        bool: True if valid.
    """
    pattern = re.compile(r"^([0-9A-Fa-f]{2}[:\-]){5}([0-9A-Fa-f]{2})$")
    return bool(pattern.match(mac))


def resolve_mac_from_host(host: str) -> str | None:
    """
    Attempts to resolve MAC address with provided hostname or IP.

    Args:
        host (str): IP or Hostname.

    Returns:
        str | None: The MAC address as a colon-separated string if found, 
        otherwise None.
    """
    # Send a ping to ensure the ARP cache is populated
    try:
        subprocess.run(["ping", "-c", "1", host],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        logger.warning("Failed to ping: %s: %s", host, e)
        return None

    # Read the ARP table
    try:
        result = subprocess.run(
            ["arp", "-n", host], capture_output=True, text=True)
        match = re.search(
            r"(([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2})", result.stdout)
        if match:
            return match.group(0)
    except Exception as e:
        logger.warning("Failed to resolve ARP for: %s: %s", host, e)

    return None
