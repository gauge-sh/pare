from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass


@dataclass
class ProcessResult:
    exit_code: int
    stdout: bytes
    stderr: bytes


async def run_async_subprocess(command: str):
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=os.environ.copy(),
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode is None:
        proc.terminate()
        raise Exception(f"Process '{command!r}' was terminated")

    return ProcessResult(
        exit_code=proc.returncode,
        stdout=stdout,
        stderr=stderr,
    )
