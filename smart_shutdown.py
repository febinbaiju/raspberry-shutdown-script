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

HEADERS = {
    "Authorization": f"Bearer {SMARTTHINGS_PAT}",
    "Content-Type": "application/json"
}

def get_switch_state(device_id):
    url = f"https://api.smartthings.com/v1/devices/{device_id}/status"
    r = requests.get(url, headers=HEADERS)
    try:
        return r.json()["components"]["main"]["switch"]["switch"]["value"]
    except:
        return None

def send_command(device_id, command):
    url = f"https://api.smartthings.com/v1/devices/{device_id}/commands"
    payload = {
        "commands": [{
            "component": "main",
            "capability": "switch",
            "command": command
        }]
    }
    r = requests.post(url, headers=HEADERS, json=payload)
    return r.ok

def schedule_shutdown():
    print("Shutting down now...")
    subprocess.call(['sudo', 'shutdown', 'now'])

# MAIN LOOP
print("Monitoring SmartThings virtual switch for shutdown command...")

while True:
    state = get_switch_state(VIRTUAL_SWITCH_ID)
    if state == "on":
        print("Shutdown trigger detected!")

        print(f"Waiting {SHUTDOWN_DELAY} seconds before turning off smart plug...")
        time.sleep(SHUTDOWN_DELAY)
        send_command(VIRTUAL_SWITCH_ID, "off")
        time.sleep(SHUTDOWN_DELAY)
        schedule_shutdown()
        break

    time.sleep(POLL_INTERVAL)
