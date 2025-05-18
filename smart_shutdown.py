import requests
import time
import subprocess
import os
from dotenv import load_dotenv

load_dotenv()

# Load env vars
TOKEN_SERVER_URL = os.getenv("SMARTTHINGS_TOKEN_SERVER_URL")
VIRTUAL_SWITCH_ID = os.getenv("VIRTUAL_SWITCH_ID")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 5))
SHUTDOWN_DELAY = int(os.getenv("SHUTDOWN_DELAY", 10))

MAX_RETRIES = 5
RETRY_DELAY = 3  # seconds

def fetch_token_info():
    if not TOKEN_SERVER_URL:
        raise ValueError("SMARTTHINGS_TOKEN_SERVER_URL is not set.")
    
    delay = RETRY_DELAY
    for attempt in range(1, 100 + 1):
        try:
            response = requests.get(TOKEN_SERVER_URL, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[Attempt {attempt}] Failed to fetch token info: {e}")
            if attempt == 100:
                raise
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

def get_access_token():
    token_info = fetch_token_info()
    access_token = token_info.get("access_token")
    if not access_token:
        raise ValueError("access_token not found in token info.")
    return access_token

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
                print("Unauthorized (401) - token may be invalid.")
            r.raise_for_status()
            return r
        except Exception as e:
            print(f"[Attempt {attempt}] Request failed: {e}")
            if attempt == MAX_RETRIES:
                print("Max retries reached, giving up.")
                return None
            time.sleep(RETRY_DELAY)
    return None

def get_switch_state(device_id):
    url = f"https://api.smartthings.com/v1/devices/{device_id}/status"
    r = safe_request("GET", url)
    if r:
        try:
            return r.json()["components"]["main"]["switch"]["switch"]["value"]
        except Exception as e:
            print(f"Error parsing switch state: {e}")
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
    try:
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
    except KeyboardInterrupt:
        print("Interrupted by user, exiting.")
        break
    except Exception as e:
        print(f"Unexpected error: {e}")
        time.sleep(POLL_INTERVAL)
