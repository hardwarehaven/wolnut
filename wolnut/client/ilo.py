import logging
import time

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger("wolnut")

POWER_ACTION_URI = "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset"
POWER_STATE_URI = "/redfish/v1/Systems/1"


def get_ilo_power_state(
    ipmi_host: str, username: str, password: str, verify_ssl: bool
) -> str | None:
    url = f"https://{ipmi_host}{POWER_STATE_URI}"
    try:
        response = requests.get(
            url, auth=HTTPBasicAuth(username, password), verify=verify_ssl, timeout=10
        )
        if response.status_code == 200:
            return response.json().get("PowerState", None)
    except Exception as e:
        logger.warning(f"Could not get ILO power state for {ipmi_host}: {e}")
    return None


def power_on_ilo_client(
    ipmi_host: str,
    username: str,
    password: str,
    verify_ssl: bool,
    retries: int = 3,
    delay: int = 5,
) -> bool:
    for attempt in range(1, retries + 1):
        state = get_ilo_power_state(ipmi_host, username, password, verify_ssl)
        if state == "On":
            logger.info(f"ILO {ipmi_host} already powered on")
            return True

        url = f"https://{ipmi_host}{POWER_ACTION_URI}"
        payload = {"ResetType": "On"}

        try:
            response = requests.post(
                url,
                json=payload,
                auth=HTTPBasicAuth(username, password),
                verify=False,
                timeout=10,
            )
            if response.status_code in [200, 202, 204]:
                logger.info(
                    f"Power ON command sent to ILO {ipmi_host} (attempt {attempt})"
                )
                return True
            else:
                logger.warning(
                    f"Failed to power on ILO {ipmi_host} (attempt {attempt}): {response.text}"
                )
        except Exception as e:
            logger.warning(f"ILO error on attempt {attempt} for {ipmi_host}: {e}")

        if attempt < retries:
            logger.info(f"Retrying ILO {ipmi_host} in {delay} seconds...")
            time.sleep(delay)

    logger.error(f"All attempts failed to power on ILO client {ipmi_host}")
    return False
