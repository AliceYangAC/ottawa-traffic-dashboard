import requests
import os
from dotenv import load_dotenv

load_dotenv()

KEYCLOAK_TOKEN_URL = os.getenv("KEYCLOAK_TOKEN_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")  # Optional, depending on Keycloak config
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

def get_eda_access_token():
    payload = {
        "client_id": CLIENT_ID,
        "username": USERNAME,
        "password": PASSWORD,
        "grant_type": "password"
    }

    # Include client_secret if required
    if CLIENT_SECRET:
        payload["client_secret"] = CLIENT_SECRET

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(KEYCLOAK_TOKEN_URL, data=payload, headers=headers)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        print("Access token retrieved successfully.")
        return access_token
    else:
        print(f"Failed to retrieve token: {response.status_code} - {response.text}")
        return None

# Example usage
token = get_eda_access_token()
if token:
    print(f"Bearer token: {token[:50]}...")  # Print first 50 chars for brevity