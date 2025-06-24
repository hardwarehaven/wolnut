
import requests
from requests.auth import HTTPBasicAuth
import logging
import time

logger = logging.getLogger("wolnut")

POWER_ACTION_URI = "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset"
POWER_STATE_URI = "/redfish/v1/Systems/1"

def get_ilo_power_state(host, username, password):
    url = f"https://{host}{POWER_STATE_URI}"
    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(username, password),
            verify=False,
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("PowerState", None)
    except Exception as e:
        logger.warning("Could not get ILO power state for %s: %s", host, e)
    return None

def power_on_ilo_client(host, username, password, retries=3, delay=5):
    for attempt in range(1, retries + 1):
        state = get_ilo_power_state(host, username, password)
        if state == "On":
            logger.info("ILO %s already powered on", host)
            return True

        url = f"https://{host}{POWER_ACTION_URI}"
        payload = {"ResetType": "On"}

        try:
            response = requests.post(
                url,
                json=payload,
                auth=HTTPBasicAuth(username, password),
                verify=False,
                timeout=10
            )
            if response.status_code in [200, 202, 204]:
                logger.info("Power ON command sent to ILO %s (attempt %d)", host, attempt)
                return True
            else:
                logger.warning("Failed to power on ILO %s (attempt %d): %s", host, attempt, response.text)
        except Exception as e:
            logger.warning("ILO error on attempt %d for %s: %s", attempt, host, e)

        if attempt < retries:
            logger.info("Retrying ILO %s in %s seconds...", host, delay)
            time.sleep(delay)

    logger.error("All attempts failed to power on ILO client %s", host)
    return False
