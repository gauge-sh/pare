from __future__ import annotations

import subprocess
import sys
from functools import lru_cache

from pare import settings
from pare.console import log_error, log_warning

# TODO: build a Client singleton to handle all requests


@lru_cache(maxsize=1)
def get_current_git_hash() -> str:
    if settings.PARE_GIT_HASH:
        if len(settings.PARE_GIT_HASH) > 7:
            log_warning(
                "PARE_GIT_HASH is longer than 7 characters. Using the first 7 characters."
            )
        return settings.PARE_GIT_HASH[:7]

    # if the git hash is not provided, we will try to get it from the current git state
    try:
        # verify we are in a clean git state
        subprocess.check_call(["git", "diff", "--quiet"])
    except subprocess.CalledProcessError:
        log_warning("Git state is not clean. Using the last commit hash.")

    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()[:7]
        )
    except subprocess.CalledProcessError:
        log_error("Pare failed to get the current git hash.")
        sys.exit(1)


def get_client_headers() -> dict[str, str]:
    headers = {settings.PARE_API_KEY_HEADER: settings.PARE_API_KEY}
    if settings.PARE_ATOMIC_DEPLOYMENT_ENABLED:
        headers[settings.PARE_ATOMIC_DEPLOYMENT_HEADER] = get_current_git_hash()
    return headers
