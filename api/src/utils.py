from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass


@dataclass
class ProcessResult:
    exit_code: int
    stdout: str
    stderr: str


async def run_async_subprocess(command: str):
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,  # This makes the output strings instead of bytes
    )

    # Use asyncio to wait for the process to complete
    loop = asyncio.get_running_loop()
    stdout, stderr = await loop.run_in_executor(None, process.communicate)

    if process.returncode is None:
        process.terminate()
        raise Exception(f"Process '{command!r}' was terminated")

    return ProcessResult(
        exit_code=process.returncode,
        stdout=stdout,
        stderr=stderr,
    )
