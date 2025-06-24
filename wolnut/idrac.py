# idrac.py
import requests
from requests.auth import HTTPBasicAuth
import logging

logger = logging.getLogger("wolnut")

POWER_ACTION_URI = "/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset"
POWER_STATE_URI = "/redfish/v1/Systems/System.Embedded.1"

def power_on_idrac_client(host, username, password, verify_ssl=False):
    url = f"https://{host}{POWER_ACTION_URI}"
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
            logger.info("iDRAC Power ON command sent to %s", host)
            return True
        else:
            logger.error("Failed to power on iDRAC client %s: %s", host, response.text)
            return False
    except Exception as e:
        logger.error("iDRAC error for %s: %s", host, e)
        return False

def get_idrac_power_state(host, username, password, verify_ssl=False):
    url = f"https://{host}{POWER_STATE_URI}"

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
        logger.error("Could not get iDRAC power state for %s: %s", host, e)

    return None
