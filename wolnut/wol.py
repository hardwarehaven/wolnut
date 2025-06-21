import logging
from wakeonlan import send_magic_packet
from wolnut.apprise import apprise_notifier

logger = apprise_notifier("wolnut")


def send_wol_packet(mac_address: str, broadcast_ip: str = "255.255.255.255") -> bool:
    """
    Sends a Wake-on-LAN (WOL) packet to the specified MAC address.

    Args:
        mac (str): The MAC address of the target device.

    Returns:
        bool: True if the packet was sent successfully, False otherwise.
    """
    try:
        logger.debug("Sending WOL packet to %s", mac_address)
        send_magic_packet(mac_address, ip_address=broadcast_ip)
        return True
    except Exception as e:
        logger.error("Failed to send WOL packet to %s: %s", mac_address, e)
        return False
