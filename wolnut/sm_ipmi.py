import subprocess
import logging

logger = logging.getLogger("wolnut")

def power_on_sm_ipmi_client(ipmi_host, username, password):
    try:
        result = subprocess.run([
            "ipmitool", "-I", "lanplus", "-H", ipmi_host,
            "-U", username, "-P", password,
            "chassis", "power", "on"
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            logger.info("Supermicro IPMI: Powered on %s", ipmi_host)
            return True
        else:
            logger.error("Supermicro IPMI: Failed to power on %s: %s", ipmi_host, result.stderr.strip())
            return False
    except Exception as e:
        logger.error("Supermicro IPMI error for %s: %s", ipmi_host, e)
        return False