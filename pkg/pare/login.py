from __future__ import annotations

import sys
from pathlib import Path
from time import sleep
from typing import Any

import requests

from pare import settings
from pare.console import log_task
from pare.constants import GITHUB_CLIENT_ID


def parse_response(response: requests.Response) -> dict[str, Any]:
    if response.status_code in [200, 201]:
        return response.json()
    elif response.status_code == 401:
        print("Authorization failed.")
        sys.exit(1)
    else:
        print(response)
        print(response.text)
        sys.exit(1)


def request_device_code() -> dict[str, Any]:
    url = "https://github.com/login/device/code"
    params = {"client_id": GITHUB_CLIENT_ID}
    headers = {"Accept": "application/json"}
    response = requests.post(url, data=params, headers=headers)
    return parse_response(response)


def request_token(device_code: str) -> dict[str, Any]:
    url = "https://github.com/login/oauth/access_token"
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    }
    headers = {"Accept": "application/json"}
    response = requests.post(url, data=params, headers=headers)
    return parse_response(response)


def poll_for_token(device_code: str, interval: int) -> str:
    error_message: str = ""
    with log_task(start_message="Polling for token..."):
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
                    error_message = (
                        "The device code has expired. Please run `login` again."
                    )
                    break
                elif error == "access_denied":
                    error_message = "Login cancelled by user."
                    break
                else:
                    error_message = "An unknown error occurred."
                    break
            elif access_token:
                break

    if error_message:
        print(error_message)
        sys.exit(1)

    return access_token


def login_to_pare(token: str) -> str:
    url = f"{settings.PARE_API_URL}/login-with-github/"
    headers = {"Content-Type": "application/json"}
    data = {"token": token}
    response = requests.post(url, json=data, headers=headers)
    response = parse_response(response)
    try:
        api_key = response["api_key"]
    except KeyError:
        print("Login failed.")
        sys.exit(1)
    print("Successfully logged in!")
    return api_key


def stash_api_key(api_key: str) -> None:
    api_key_path = Path(settings.PARE_API_KEY_FILE)
    api_key_path.parent.mkdir(parents=True, exist_ok=True)
    api_key_path.write_text(api_key)


def check_already_has_api_key() -> bool:
    api_key_path = Path(settings.PARE_API_KEY_FILE)
    return api_key_path.exists() and bool(api_key_path.read_text())


def login():
    if check_already_has_api_key():
        confirm = input(
            f"You already have an API key (at '{settings.PARE_API_KEY_FILE}'). Do you want to overwrite it? (y/n): "
        )
        if confirm.lower() != "y":
            print("Exiting...")
            sys.exit(0)

    device_code_response = request_device_code()
    verification_uri = device_code_response["verification_uri"]
    user_code = device_code_response["user_code"]
    device_code = device_code_response["device_code"]
    interval = device_code_response["interval"]

    print(f"Please visit: {verification_uri}")
    print(f"and enter code: {user_code}")

    token = poll_for_token(device_code, interval)
    api_key = login_to_pare(token)
    stash_api_key(api_key)
    print("Successfully authenticated!")
