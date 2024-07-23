from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

PIP_PLATFORM = "manylinux2014_x86_64"


def install_deps_to_dir(
    dependencies: list[str], python_version: str, output_dir: Path
) -> None:
    dependencies.append("gauge-serverless")
    output_dir.mkdir(parents=True, exist_ok=True)

    pip_command = [
        sys.executable,
        "-m",
        "uv",
        "pip",
        "install",
        "--python-platform",
        PIP_PLATFORM,
        "--python-version",
        python_version,
        "--only-binary",
        ":all:",
        "--target",
        str(output_dir),
        "--upgrade",
    ]
    pip_command.extend(dependencies)

    try:
        subprocess.run(pip_command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error installing dependencies. Error Output:\n{e.stderr}")
