import requests
from requests.auth import HTTPBasicAuth
import logging
import time

logger = logging.getLogger("wolnut")

POWER_ACTION_URI = "/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset"
POWER_STATE_URI = "/redfish/v1/Systems/System.Embedded.1"

def get_idrac_power_state(ipmi_host, username, password, verify_ssl):
    url = f"https://{ipmi_host}{POWER_STATE_URI}"

    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(username, password),
            verify=verify_ssl,
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("PowerState", None)
    except Exception as e:
        logger.warning("Could not get iDRAC power state for %s: %s", ipmi_host, e)
    return None


def power_on_idrac_client(ipmi_host, username, password, verify_ssl, retries=3, delay=5):
    for attempt in range(1, retries + 1):
        state = get_idrac_power_state(ipmi_host, username, password, verify_ssl)
        if state == "On":
            logger.info("iDRAC %s already powered on", ipmi_host)
            return True

        url = f"https://{ipmi_host}{POWER_ACTION_URI}"
        payload = {"ResetType": "On"}

        try:
            response = requests.post(
                url,
                json=payload,
                auth=HTTPBasicAuth(username, password),
                verify=verify_ssl,
                timeout=10
            )

            if response.status_code in [200, 202, 204]:
                logger.info("Power ON command sent to iDRAC %s (attempt %d)", ipmi_host, attempt)
                return True
            else:
                logger.warning("Failed to power on iDRAC %s (attempt %d): %s",
                               ipmi_host, attempt, response.text)
        except Exception as e:
            logger.warning("iDRAC error on attempt %d for %s: %s", attempt, ipmi_host, e)

        if attempt < retries:
            logger.info("Retrying iDRAC %s in %s seconds...", ipmi_host, delay)
            time.sleep(delay)

    logger.error("All attempts failed to power on iDRAC client %s", ipmi_host)
    return False
