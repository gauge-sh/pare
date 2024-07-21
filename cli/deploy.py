from __future__ import annotations

import os
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path
from time import sleep

import boto3
import requests
from rich.console import Console

from cli.console import log_error, log_task

API_URL = "https://api.bridge-cli.com/api/v0.1/deploy"
DEMO_URL = "demo.bridge-cli.com"


class DeployHandler:
    def __init__(
        self, bucket_name: str, file_paths: list[str], deploy_name: str = ""
    ) -> None:
        self.bucket_name = bucket_name
        self.file_paths = file_paths
        if not deploy_name:
            deploy_name = str(uuid.uuid4())
        self.deploy_name = deploy_name

    def validate_file_paths(self) -> None:
        errored = False
        for file_path in self.file_paths:
            if not Path(file_path).exists():
                errored = True
                log_error(f"{file_path} does not exist")
            if not Path(file_path).is_file():
                errored = True
                log_error(f"{file_path} is not a file")
            if file_path[-3:] != ".py":
                errored = True
                print(file_path[-3:])
                log_error(f"{file_path} is not a python file")
        if errored:
            sys.exit(1)

    def bundle(self, temp_dir: tempfile.TemporaryDirectory[str]) -> Path:
        with log_task(start_message="Bundling...", end_message="Project bundled"):
            zip_filename = f"{self.deploy_name}.zip"
            zip_path = Path(temp_dir) / zip_filename

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in self.file_paths:
                    zipf.write(file_path)
        return zip_path

    def upload(self, zip_path: Path) -> str:
        with log_task(
            start_message="Uploading bundle...", end_message="Bundle uploaded"
        ):
            try:
                s3_client = boto3.client("s3")
                destination_key = f"deploys/{self.deploy_name}.zip"
                s3_client.upload_file(str(zip_path), self.bucket_name, destination_key)
            except:
                pass
            public_url = (
                f"https://{self.bucket_name}.s3.amazonaws.com/{destination_key}"
            )
            return public_url

    def trigger(self, project_name: str, source_url: str):
        with log_task(
            start_message="Triggering deploy...", end_message="Deploy triggered"
        ):
            data = {
                "name": self.deploy_name[:8],
                "project_name": project_name,
                "source_url": source_url,
            }
            gauge_client_id = os.environ.get(
                "GAUGE_CLIENT_ID", input("Input your GAUGE_CLIENT_ID")
            )
            resp = requests.post(
                API_URL, json=data, headers={"GAUGE_CLIENT_ID": gauge_client_id}
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

    def deploy(self):
        console = Console()
        console.print(
            f"Deploying [bold white]"
            f"[bold green] as [bold white]{self.deploy_name[:8]}[bold green]...",
        )
        self.validate_file_paths()
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = self.bundle(temp_dir)
            url = self.upload(zip_path)
        console.print(f"[bold white]{self.deploy_name[:8]} [bold green]deployed!")
        console.print(f"[blue]https://{DEMO_URL}")
