from __future__ import annotations

import importlib.util
import inspect
import os
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path
from time import sleep

import requests
from pydantic import BaseModel
from rich.console import Console

from cli.console import log_error, log_task

API_URL = os.environ.get("GAUGE_API_URL", "http://localhost:8000")


class DeployHandler:
    def __init__(self, file_paths: list[str], deploy_name: str = "") -> None:
        self.file_paths = {Path(file_path) for file_path in file_paths}
        if not deploy_name:
            deploy_name = str(uuid.uuid4())
        self.deploy_name = deploy_name

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
            zip_filename = f"{self.deploy_name}.zip"
            zip_path = Path(temp_dir) / zip_filename

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in self.file_paths:
                    zipf.write(file_path)
        return zip_path

    def upload(self, zip_path: Path, endpoint_references: dict[str, BaseModel]) -> None:
        gauge_client_id = os.environ.get(
            "GAUGE_CLIENT_ID", input("Input your GAUGE_CLIENT_ID: ")
        )
        with log_task(
            start_message="Uploading bundle...", end_message="Bundle uploaded"
        ):
            data = {"name": self.deploy_name, "endpoints": endpoint_references}

            with open(zip_path, "rb") as f:
                files = {"zip": f}
                resp = requests.post(
                    API_URL,
                    json=data,
                    headers={"GAUGE_CLIENT_ID": gauge_client_id},
                    files=files,
                    timeout=1,
                )
            if resp.status_code != 200:
                print(resp.status_code, resp.content)
                log_error("Failed to trigger the deploy")
                sys.exit(1)

    def retrieve(self):
        with log_task(
            start_message="Checking deploy status...", end_message="Status updated"
        ):
            status = "pending"
            while status == "pending":
                resp = requests.get(API_URL)
                sleep(0.1)
                if resp.status_code == 200:
                    deployment_data = resp.json()
                    for deployment in deployment_data["deployments"]:
                        if deployment["name"] == self.deploy_name[:8]:
                            status = deployment["status"]
                            if status == "error":
                                log_error(deployment["debug"])
                            elif status == "deployed":
                                return deployment.get("deploy_url", "[deployment_url]")
                            break
                else:
                    sleep(3)

    def build_references(self) -> dict[str, dict[str, str | list[str]]]:
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
                            name, config = obj._gauge_register()
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
        return results

    def deploy(self):
        console = Console()
        console.print(
            f"Deploying [bold white]"
            f"[bold green] as [bold white]{self.deploy_name}[bold green]...",
        )
        self.validate_file_paths()
        endpoint_references = self.build_references()
        print(endpoint_references)
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = self.bundle(temp_dir)
            self.upload(zip_path, endpoint_references)
        console.print(f"[bold white]{self.deploy_name[:8]} [bold green]deployed!")
