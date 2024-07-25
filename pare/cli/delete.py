from __future__ import annotations

import sys

import requests

from pare import settings
from pare.cli.console import log_error


def delete_function(function_name: str) -> None:
    try:
        response = requests.delete(
            settings.GAUGE_API_URL + f"/delete/{function_name}/",
            headers={"X-Client-Secret": settings.CLIENT_SECRET},
        )
        response.raise_for_status()
    except requests.HTTPError as e:
        log_error(f"Failed to delete function. Status code: {e.response.status_code}")
        sys.exit(1)
    except Exception as e:
        log_error(f"Failed to delete function due to error: {e}")
        sys.exit(1)
