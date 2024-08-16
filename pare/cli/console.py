from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from collections.abc import Generator


@contextmanager
def log_task(start_message: str, end_message: str = "") -> Generator[None, None, None]:
    console = Console()
    with console.status(
        f"      {start_message}", spinner="aesthetic", spinner_style="blue"
    ):
        try:
            # Before entering the block
            yield
        finally:
            if end_message:
                # After exiting the block
                # Format the current time to include leading zeros (HH:MM:SS)
                timestamp_str = datetime.now().strftime("[%H:%M:%S]")
                console.print(
                    f"{timestamp_str} [bright_green]✓[/bright_green] {end_message}",
                    highlight=False,
                )


def log_error(message: str) -> None:
    console = Console()
    console.print(f"[bright_red]✗ Error[/bright_red]: {message}")


def log_warning(message: str) -> None:
    console = Console()
    console.print(f"[yellow] Warning[/yellow]: {message}")
