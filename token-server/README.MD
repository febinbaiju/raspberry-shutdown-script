# SmartThings Token Server

A lightweight Python service to automate SmartThings OAuth token refresh, solving the issue of frequently changing Personal Access Tokens (PAT). It uses a seed refresh token to fetch new access tokens, saves them to a file, and serves the latest token over HTTP for easy integration in home automation or custom apps.

---

## Features

- Automatically refreshes SmartThings OAuth tokens at configurable intervals  
- Serves the current token via a simple HTTP server (`/token_info.json`)  
- Docker-ready for easy deployment anywhere  
- Minimal dependencies and lightweight design  

---

## Getting Started

### Prerequisites

- Python 3.8+ (if running locally)  
- Docker (optional, recommended for easy deployment)  
- SmartThings OAuth credentials:
  - `SMARTTHINGS_CLIENT_ID`
  - `SMARTTHINGS_CLIENT_SECRET`
  - `REFRESH_TOKEN` (seed refresh token)

---

### Environment Variables

The server requires the following environment variables:

| Variable                 | Description                           |
|--------------------------|-------------------------------------|
| `SMARTTHINGS_CLIENT_ID`     | Your SmartThings OAuth client ID       |
| `SMARTTHINGS_CLIENT_SECRET` | Your SmartThings OAuth client secret   |
| `REFRESH_TOKEN`              | Your seed refresh token                 |

---

### Running Locally

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/smartthings-token-server.git
    cd smartthings-token-server
    ```

2. Install dependencies:

    ```bash
    pip3 install -r requirements.txt
    ```

3. Set environment variables (Linux/macOS):

    ```bash
    export SMARTTHINGS_CLIENT_ID="your_client_id"
    export SMARTTHINGS_CLIENT_SECRET="your_client_secret"
    export REFRESH_TOKEN="your_seed_refresh_token"
    ```

4. Run the server:

    ```bash
    python3 smartthings_token_server.py
    ```

5. Access the current token at:

    ```
    http://localhost:5165/token_info.json
    ```

---

### Running with Docker

1. Create a `docker-compose.yml` file with the required environment variables (see example below).

2. Start the container:

    ```bash
    docker-compose up -d
    ```

3. Access the token at:

    ```
    http://localhost:5165/token_info.json
    ```

4. To stop the container:

    ```bash
    docker-compose down
    ```

---

### Example `docker-compose.yml`

```yaml
version: "3.8"

services:
  token-server:
    image: python:3.13-slim
    container_name: smartthings_token_server
    volumes:
      - ./token_data:/tmp
      - ./smartthings_token_server.py:/app/smartthings_token_server.py:ro
    working_dir: /app
    environment:
      SMARTTHINGS_CLIENT_ID: your_client_id
      SMARTTHINGS_CLIENT_SECRET: your_client_secret
      REFRESH_TOKEN: your_seed_refresh_token
    command: ["python3", "smartthings_token_server.py"]
    ports:
      - "5165:5165"
