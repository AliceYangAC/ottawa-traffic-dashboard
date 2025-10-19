
import requests
# Helper function to request token to access Nokia EDA API
def get_eda_access_token(token_url, client_id, client_secret, username, password):
    payload = {
        "client_id": client_id,
        "username": username,
        "password": password,
        "client_secret": client_secret,
        "grant_type": "password"
    }
    
    print("This is the access payload", payload)
    # if client_secret:
    #     payload["client_secret"] = client_secret

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        # DO NOT DISABLE SSL IN PRODUCTION
        response = requests.post(token_url, data=payload, headers=headers, verify=False)
        response.raise_for_status()
        token_data = response.json()
        print("This is the response token data", token_data)
        access_token = token_data.get("access_token")
        print("Successfully retrieved EDA access token.")
        return access_token
    except Exception as e:
        print(f"Failed to retrieve EDA token: {str(e)}")
        return None