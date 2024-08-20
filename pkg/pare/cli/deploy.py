from __future__ import annotations

import importlib.util
import inspect
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import cast

import requests
from rich.console import Console

from pare import settings
from pare.client import get_current_git_hash
from pare.console import log_error, log_task
from pare.constants import PYTHON_VERSION
from pare.models import DeployConfig, ServiceConfig, ServiceRegistration


class DeployHandler:
    def __init__(
        self,
        file_paths: list[str],
        environment_variables: dict[str, str] | None = None,
    ) -> None:
        self.file_paths = {Path(file_path) for file_path in file_paths}
        self.environment_variables = environment_variables or {}
        self.deploy_url = f"{settings.PARE_API_URL}/{settings.PARE_API_VERSION}{settings.PARE_API_DEPLOY_URL_PATH}"

    @property
    def headers(self) -> dict[str, str]:
        return {
            settings.PARE_API_KEY_HEADER: settings.PARE_API_KEY,
        }

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
            zip_filename = "pare_project_bundle.zip"
            zip_path = Path(temp_dir) / zip_filename

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in self.file_paths:
                    zipf.write(file_path)
        return zip_path

    def upload(self, zip_path: Path, deploy_config: DeployConfig) -> None:
        with log_task(
            start_message="Uploading bundle...", end_message="Bundle uploaded"
        ):
            with open(zip_path, "rb") as zip_file:
                files = {
                    "file": zip_file,
                    "json_data": (None, deploy_config.model_dump_json()),
                }
                resp = requests.post(
                    self.deploy_url,
                    headers=self.headers,
                    files=files,
                )
            if resp.status_code != 200:
                log_error("Failed to trigger the deploy")
                sys.exit(1)

    def register_services(self) -> list[ServiceConfig]:
        services: list[ServiceConfig] = []
        service_names: set[str] = set()
        for file_path in self.file_paths:
            module_name = str(file_path).replace(os.path.sep, ".").replace(".py", "")
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for name, obj in inspect.getmembers(module):
                    if inspect.isfunction(obj) and hasattr(obj, "_pare_register"):
                        try:
                            service_registration = cast(
                                ServiceRegistration,
                                obj._pare_register(),  # type: ignore
                            )
                            if name in service_names:
                                raise ValueError(f"Duplicate endpoint {name}")
                            service_names.add(name)
                            services.append(
                                ServiceConfig(
                                    name=service_registration.name,
                                    path=f"{module_name}:{service_registration.function}",
                                    requirements=service_registration.dependencies,
                                )
                            )
                        except Exception as e:
                            print(f"Error calling _pare_register on {name}: {e}")
                            break
            else:
                print(f"Couldn't load module from {file_path}")
        return services

    def deploy(self):
        console = Console()
        console.print(
            "[bold white]Deploying...[/bold white]",
        )
        self.validate_file_paths()
        services = self.register_services()
        deploy_config = DeployConfig(
            git_hash=get_current_git_hash(),
            python_version=PYTHON_VERSION,
            services=services,
            environment_variables=self.environment_variables,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = self.bundle(temp_dir)
            self.upload(zip_path, deploy_config=deploy_config)
        console.print("[bold green]Deployed![/bold green]")
