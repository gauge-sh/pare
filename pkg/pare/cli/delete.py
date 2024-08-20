from __future__ import annotations

import sys

import requests

from pare import settings
from pare.console import log_error


def delete_function(function_name: str, git_hash: str) -> None:
    headers = {settings.PARE_API_KEY_HEADER: settings.PARE_API_KEY}
    if git_hash:
        headers[settings.PARE_ATOMIC_DEPLOYMENT_HEADER] = git_hash

    try:
        response = requests.delete(
            f"{settings.PARE_API_URL}/{settings.PARE_API_VERSION}{settings.PARE_API_DELETE_URL_PATH}{function_name}/",
            headers=headers,
        )
        response.raise_for_status()
    except requests.HTTPError as e:
        log_error(f"Failed to delete function. Status code: {e.response.status_code}")
        sys.exit(1)
    except Exception as e:
        log_error(f"Failed to delete function due to error: {e}")
        sys.exit(1)
