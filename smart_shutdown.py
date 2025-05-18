import requests
import time
import subprocess
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Load env vars
CLIENT_ID = os.getenv("SMARTTHINGS_CLIENT_ID")
CLIENT_SECRET = os.getenv("SMARTTHINGS_CLIENT_SECRET")
VIRTUAL_SWITCH_ID = os.getenv("VIRTUAL_SWITCH_ID")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 5))
SHUTDOWN_DELAY = int(os.getenv("SHUTDOWN_DELAY", 10))
TOKEN_FILE = os.getenv("SMARTTHINGS_TOKEN_FILE", "tokens.json")

MAX_RETRIES = 5
RETRY_DELAY = 3

def load_tokens():
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)

def save_tokens(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f)

def refresh_token():
    tokens = load_tokens()
    data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": tokens["refresh_token"]
    }
    response = requests.post("https://auth-global.api.smartthings.com/oauth/token", data=data)
    response.raise_for_status()
    new_tokens = response.json()
    save_tokens(new_tokens)
    return new_tokens["access_token"]

def get_access_token():
    tokens = load_tokens()
    return tokens["access_token"]

def get_headers():
    token = get_access_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def safe_request(method, url, **kwargs):
    for attempt in range(1, MAX_RETRIES + 1):
        headers = get_headers()
        try:
            r = requests.request(method, url, headers=headers, timeout=10, **kwargs)
            if r.status_code == 401:
                print("Access token expired, refreshing...")
                new_token = refresh_token()
                headers["Authorization"] = f"Bearer {new_token}"
                r = requests.request(method, url, headers=headers, timeout=10, **kwargs)
            r.raise_for_status()
            return r
        except Exception as e:
            print(f"[Attempt {attempt}] Request failed: {e}")
            time.sleep(RETRY_DELAY)
    return None

def get_switch_state(device_id):
    url = f"https://api.smartthings.com/v1/devices/{device_id}/status"
    r = safe_request("GET", url)
    if r:
        return r.json()["components"]["main"]["switch"]["switch"]["value"]
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
    r = safe_request("POST", url, json=payload)
    if r:
        print(f"Command '{command}' sent to {device_id}")
        return True
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

        send_command(VIRTUAL_SWITCH_ID, "off")

        print(f"Waiting another {SHUTDOWN_DELAY} seconds before shutting down...")
        time.sleep(SHUTDOWN_DELAY)

        schedule_shutdown()
        break

    time.sleep(POLL_INTERVAL)
