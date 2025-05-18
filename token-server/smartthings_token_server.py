def get_token(token_file_path, client_id, client_secret, seed_refresh_token):
    """
    Function to obtain a new access token using a refresh token. If the refresh token does not exist,
    a seed refresh token is used. The updated refresh and access tokens are stored in a file.

    Args:
        token_file_path (str): Path to the file where token information is stored.
        client_id (str): OAuth client ID.
        client_secret (str): OAuth client secret.
        seed_refresh_token (str): Initial seed refresh token if no token file exists.
    """
    try:
        # Try to read the refresh token from the token file
        with open(token_file_path, 'rt') as infile:
            refresh_token = json.loads(infile.read()).get('refresh_token')
            if not refresh_token:  # If no refresh token exists, raise an exception
                raise FileNotFoundError
    except FileNotFoundError:
        # Use the seed refresh token if no token file exists or refresh_token is invalid
        refresh_token = seed_refresh_token

    print(f"[CURRENT] refresh_token: {refresh_token}")

    # SmartThings API endpoint for obtaining a new token
    url = "https://api.smartthings.com/oauth/token"

    # Prepare the payload for the API request
    payload = f'grant_type=refresh_token&client_id={client_id}&client_secret=&refresh_token={refresh_token}'

    # Prepare the headers, including the base64-encoded client_id and client_secret
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {base64.b64encode(f"{client_id}:{client_secret}".encode()).decode("utf-8")}',
    }

    # Send a POST request to the SmartThings API to get a new token
    response = requests.request("POST", url, headers=headers, data=payload, timeout=30)

    # Check if the response was successful
    if response.status_code == 200:
        # Parse and pretty-print the response JSON
        response_dict = response.json()
        response_dict['issued_at'] = datetime.datetime.now(pytz.timezone('UTC')).isoformat(timespec="seconds").replace('+00:00', 'Z')
        response_json = json.dumps(response_dict, indent=4)
        print(f" [NEW] [{datetime.datetime.now()}] {response_json}")

        # Write the new token information to the file
        with open(token_file_path, 'wt') as outfile:
            outfile.write(response_json)
    else:
        # Exit the script if the token request fails
        sys.exit(response.text)


if __name__ == "__main__":
    # Import required libraries
    import datetime
    import base64
    import time
    import json
    import sys
    import subprocess
    import os
    import socket


    # Helper function to install Python packages dynamically
    def install(package):
        subprocess.check_call(["pip3", "install", package])


    # Install required third-party packages
    install('python-dotenv')
    install('schedule')
    install('requests')
    install('pytz')

    # Importing installed modules
    import requests
    import schedule
    import pytz
    from dotenv import load_dotenv

    # Check if running on Windows
    windows = (os.name == 'nt')

    # Set the path for the OAuth token file (specific to OS)
    if windows:
        oauth_token_file_path = 'token_info.json'
    else:
        oauth_token_file_path = '/tmp/token_info.json'
        # Note: Set up a Persistent Volume Claim (PVC) for /tmp if needed.




    # Load .env file
    load_dotenv()

    # Define client credentials and seed refresh token
    oauth_client_id = os.getenv('SMARTTHINGS_CLIENT_ID')
    oauth_client_secret = os.getenv('SMARTTHINGS_CLIENT_SECRET')
    seed_oauth_refresh_token = os.getenv('REFRESH_TOKEN')

    if not all([oauth_client_id, oauth_client_secret, seed_oauth_refresh_token]):
        sys.exit("Missing SMARTTHINGS_CLIENT_ID, SMARTTHINGS_CLIENT_SECRET, or REFRESH_TOKEN in environment variables.")


    # Define the token refresh interval and HTTP server configurations
    num_minutes = 960  # Number of minutes between each token refresh
    host = '0.0.0.0'  # HTTP server host
    port = '5165'  # HTTP server port

    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    if is_port_in_use(int(port)):
         sys.exit(f"Port {port} is already in use. Exiting.")
         

    # Start the HTTP server to serve files on the specified port
    if windows:
        # Start the HTTP server on Windows
        subprocess.Popen(
            ['python3', '-m', 'http.server', '--bind', host, port],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True
        )
    else:
        # Start the HTTP server on non-Windows systems
        subprocess.Popen(
            ['python3', '-m', 'http.server', '--bind', host, '--directory', '/tmp', port],
            start_new_session=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"STARTING HTTP SERVER LISTENING AT {host} ON PORT {port}.")

        get_token(
    oauth_token_file_path,
    oauth_client_id,
    oauth_client_secret,
    seed_oauth_refresh_token
)


    # Schedule the token refresh process to run every num_minutes
    schedule.every(num_minutes).minutes.do(
        get_token,
        oauth_token_file_path,
        oauth_client_id,
        oauth_client_secret,
        seed_oauth_refresh_token
    )

    print(f"STARTING TOKEN OBTAIN PROCESS RUNNING EVERY {num_minutes} MINUTES.")

    # Run the scheduled tasks in a loop
    while True:
        schedule.run_pending()
        time.sleep(1)  # Sleep briefly to avoid busy-waiting