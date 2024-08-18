from __future__ import annotations

from datetime import datetime
from typing import Any

import requests
from rich.console import Console
from rich.table import Table

from pare import settings


def show_status():
    list_url = f"{settings.PARE_API_URL}/{settings.PARE_API_VERSION}{settings.PARE_API_SERVICES_URL_PATH}"
    headers = {settings.PARE_API_KEY_HEADER: settings.PARE_API_KEY}
    try:
        response = requests.get(list_url, headers=headers)
        display_status_table(response.json())
    except Exception as e:
        console = Console()
        console.print(f"[bold red]Error: {e}[/bold red]")


def display_status_table(status_data: list[dict[str, Any]]):
    table = Table(title="Deployment Data")

    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Git Hash", style="magenta")
    table.add_column("Created At", style="yellow")

    for item in status_data:
        name = item["name"]
        git_hash = item["deployment"]["git_hash"]
        created_at = datetime.fromisoformat(item["created_at"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        table.add_row(name, git_hash, created_at)

    console = Console()
    console.print(table)
