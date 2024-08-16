from __future__ import annotations

import sys
from time import sleep

import requests

from pare.cli.constants import GITHUB_CLIENT_ID


def parse_response(response: requests.Response) -> dict | None:
    if response.status_code in [200, 201]:
        return response.json()
    elif response.status_code == 401:
        print("You are not authorized. Run the `login` command.")
        sys.exit(1)
    else:
        print(response)
        print(response.text)
        sys.exit(1)


def request_device_code() -> str | None:
    url = "https://github.com/login/device/code"
    params = {"client_id": GITHUB_CLIENT_ID}
    headers = {"Accept": "application/json"}
    response = requests.post(url, data=params, headers=headers)
    return parse_response(response)


def request_token(device_code: str) -> dict | None:
    url = "https://github.com/login/oauth/access_token"
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    }
    headers = {"Accept": "application/json"}
    response = requests.post(url, data=params, headers=headers)
    return parse_response(response)


def poll_for_token(device_code: str, interval: int):
    while True:
        response = request_token(device_code)
        error = response.get("error", "")
        access_token = response.get("access_token", "")

        if error:
            if error == "authorization_pending":
                sleep(interval)
                continue
            elif error == "slow_down":
                sleep(interval + 2)
                continue
            elif error == "expired_token":
                print("The device code has expired. Please run `login` again.")
                sys.exit(1)
            elif error == "access_denied":
                print("Login cancelled by user.")
                sys.exit(1)
            else:
                print(response)
                sys.exit(1)

        with open(".token", "w") as f:
            f.write(access_token)
        break


def login():
    device_code_response = request_device_code()
    verification_uri = device_code_response["verification_uri"]
    user_code = device_code_response["user_code"]
    device_code = device_code_response["device_code"]
    interval = device_code_response["interval"]

    print(f"Please visit: {verification_uri}")
    print(f"and enter code: {user_code}")

    poll_for_token(device_code, interval)
    print("Successfully authenticated!")


def whoami():
    url = "https://api.github.com/user"
    try:
        with open(".token") as f:
            token = f.read().strip()
    except FileNotFoundError:
        print("You are not authorized. Run the `login` command.")
        sys.exit(1)

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(url, headers=headers)
    parsed_response = parse_response(response)
    print(f"You are {parsed_response['login']}")
