from __future__ import annotations

import importlib.util
import inspect
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, TypedDict

import requests
from rich.console import Console

from gauge import settings
from gauge.cli.console import log_error, log_task


class DeployType(TypedDict):
    module: str | None
    reference: str
    function: str
    python_version: str
    dependencies: list[str]


DeployConfigType = Dict[str, DeployType]


class DeployHandler:
    def __init__(
            self,
            file_paths: list[str],
            api_url: str | None = None,
            client_secret: str | None = None
        ) -> None:
        self.file_paths = {Path(file_path) for file_path in file_paths}
        self.deploy_url = (api_url or settings.GAUGE_API_URL) + "/deploy"
        self.client_secret = client_secret or settings.CLIENT_SECRET

    @property
    def headers(self) -> dict[str, str]:
        return {"X-Client-Secret": self.client_secret}

    def validate_file_paths(self) -> None:
        errored = False
        for file_path in self.file_paths:
            if not file_path.exists():
                errored = True
                log_error(f"{file_path} does not exist")
            elif not file_path.is_file():
                errored = True
                log_error(f"{file_path} is not a file")
            elif file_path.suffix.lower() != ".py":
                errored = True
                log_error(f"{file_path} is not a python file")
        if errored:
            sys.exit(1)

    def bundle(self, temp_dir: str) -> Path:
        with log_task(start_message="Bundling...", end_message="Project bundled"):
            zip_filename = "gauge_project_bundle.zip"
            zip_path = Path(temp_dir) / zip_filename

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in self.file_paths:
                    zipf.write(file_path)
        return zip_path

    def upload(self, zip_path: Path, deployments: DeployConfigType) -> None:
        with log_task(
            start_message="Uploading bundle...", end_message="Bundle uploaded"
        ):
            with open(zip_path, "rb") as zip_file:
                files = {"file": zip_file, "json_data": (None, json.dumps(deployments))}
                resp = requests.post(
                    self.deploy_url,
                    headers=self.headers,
                    files=files,
                )
            if resp.status_code != 200:
                log_error("Failed to trigger the deploy")
                sys.exit(1)

    def register_deployments(self) -> DeployConfigType:
        results = {}
        for file_path in self.file_paths:
            module_name = str(file_path).replace(os.path.sep, ".").replace(".py", "")
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for name, obj in inspect.getmembers(module):
                    if inspect.isfunction(obj) and hasattr(obj, "_gauge_register"):
                        try:
                            name, config = obj._gauge_register()  # type: ignore
                            if name in results:
                                raise ValueError(f"Duplicate endpoint {name}")
                            results[name] = {
                                "module": module_name,
                                "reference": f"{module_name}:{config['function']}",
                                **config,
                            }

                        except Exception as e:
                            print(f"Error calling _gauge_register on {name}: {e}")
                            break
            else:
                print(f"Couldn't load module from {file_path}")
        return results  # type: ignore

    def deploy(self):
        console = Console()
        console.print(
            f"[bold white]Deploying...[/bold white]",
        )
        self.validate_file_paths()
        deployments = self.register_deployments()
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = self.bundle(temp_dir)
            self.upload(zip_path, deployments)
        console.print("[bold green]Deployed![/bold green]")
