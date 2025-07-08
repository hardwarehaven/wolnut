import subprocess
import logging

logger = logging.getLogger("wolnut")


def power_on_sm_ipmi_client(ipmi_host: str, username: str, password: str):
    try:
        result = subprocess.run(
            [
                "ipmitool",
                "-I",
                "lanplus",
                "-H",
                ipmi_host,
                "-U",
                username,
                "-P",
                password,
                "chassis",
                "power",
                "on",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            logger.info(f"Supermicro IPMI: Powered on {ipmi_host}")
            return True
        else:
            logger.error(
                f"Supermicro IPMI: Failed to power on {ipmi_host}: {result.stderr.strip()}"
            )
            return False
    except Exception as e:
        logger.error(f"Supermicro IPMI error for {ipmi_host}: {e}")
        return False
