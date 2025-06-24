import requests
from requests.auth import HTTPBasicAuth

# === Configuration ===
IDRAC_HOST = "https://10.20.20.8"   # Replace with your iDRAC IP
USERNAME = "root"                     # Default iDRAC username
PASSWORD = "yourpassword"                   # Default iDRAC password
VERIFY_SSL = False                    # Set to True if using valid cert

# === Redfish endpoint to power on system ===
POWER_ACTION_URI = "/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset"
POWER_PAYLOAD = {
    "ResetType": "On"
}

def power_on_server():
    url = f"{IDRAC_HOST}{POWER_ACTION_URI}"

    try:
        response = requests.post(
            url,
            json=POWER_PAYLOAD,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            verify=VERIFY_SSL,
            timeout=10
        )

        if response.status_code in [200, 202, 204]:
            print("✅ Power on command sent successfully.")
        else:
            print(f"❌ Failed to power on. Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    power_on_server()
