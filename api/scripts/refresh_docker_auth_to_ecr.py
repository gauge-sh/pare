from __future__ import annotations

import base64
import subprocess
import sys
from dataclasses import dataclass

import boto3


@dataclass
class AuthInfo:
    username: str
    password: str
    proxy_endpoint: str
    expires_at: str


def get_ecr_auth_token(region: str = "us-east-1") -> AuthInfo:
    ecr_client = boto3.client("ecr", region_name=region)  # type: ignore

    try:
        response = ecr_client.get_authorization_token()

        # The response includes authorization data
        auth_data = response["authorizationData"][0]

        # Extract the base64 encoded token
        encoded_token = auth_data["authorizationToken"]

        # Decode the token
        decoded_token = base64.b64decode(encoded_token).decode()

        # Split the decoded token into username and password
        username, password = decoded_token.split(":")

        # Get the proxy endpoint
        proxy_endpoint = auth_data["proxyEndpoint"]

        return AuthInfo(
            username=username,
            password=password,
            proxy_endpoint=proxy_endpoint,
            expires_at=auth_data["expiresAt"],
        )
    except Exception as e:
        print(f"Error getting ECR authorization token: {str(e)}")
        sys.exit(1)


def refresh_docker_auth(auth_info: AuthInfo):
    command = f"docker login -u {auth_info.username} -p {auth_info.password} {auth_info.proxy_endpoint}"
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"Error refreshing Docker auth: {result.stderr}")
        sys.exit(1)

    print("Docker auth refreshed successfully")


if __name__ == "__main__":
    auth_info = get_ecr_auth_token()
    refresh_docker_auth(auth_info)
