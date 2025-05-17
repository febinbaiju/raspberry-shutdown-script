import requests
import time
import subprocess
import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# Get config from environment
SMARTTHINGS_PAT = os.getenv("SMARTTHINGS_PAT")
VIRTUAL_SWITCH_ID = os.getenv("VIRTUAL_SWITCH_ID")
REAL_PLUG_ID = os.getenv("REAL_PLUG_ID")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 5))
SHUTDOWN_DELAY = int(os.getenv("SHUTDOWN_DELAY", 10))
MAX_RETRIES = 5
RETRY_DELAY = 3  # seconds

HEADERS = {
    "Authorization": f"Bearer {SMARTTHINGS_PAT}",
    "Content-Type": "application/json"
}


def get_switch_state(device_id):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            url = f"https://api.smartthings.com/v1/devices/{device_id}/status"
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            return r.json()["components"]["main"]["switch"]["switch"]["value"]
        except Exception as e:
            print(f"[Attempt {attempt}] Error getting switch state: {e}")
            time.sleep(RETRY_DELAY)
    print("Failed to get switch state after retries.")
    return None


def send_command(device_id, command):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            url = f"https://api.smartthings.com/v1/devices/{device_id}/commands"
            payload = {
                "commands": [{
                    "component": "main",
                    "capability": "switch",
                    "command": command
                }]
            }
            r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
            r.raise_for_status()
            print(f"Command '{command}' sent to device {device_id}")
            return True
        except Exception as e:
            print(f"[Attempt {attempt}] Error sending command: {e}")
            time.sleep(RETRY_DELAY)
    print(f"Failed to send '{command}' command to device {device_id} after retries.")
    return False


def schedule_shutdown():
    print("Shutting down now...")
    subprocess.call(['sudo', 'shutdown', 'now'])


# MAIN LOOP
print("Monitoring SmartThings virtual switch for shutdown command...")

while True:
    state = get_switch_state(VIRTUAL_SWITCH_ID)
    if state == "on":
        print("Shutdown trigger detected!")

        print(f"Waiting {SHUTDOWN_DELAY} seconds before turning off the virtual switch...")
        
        time.sleep(SHUTDOWN_DELAY)
        send_command(VIRTUAL_SWITCH_ID, "off")  # Reset switch first

        print(f"Waiting {SHUTDOWN_DELAY} seconds before shutting down the system...")
        time.sleep(SHUTDOWN_DELAY)

        schedule_shutdown()
        break

    time.sleep(POLL_INTERVAL)
