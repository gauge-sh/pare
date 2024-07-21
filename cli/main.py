from __future__ import annotations

import argparse

from cli.deploy import DeployHandler


def setup() -> None:
    """Setup the environment."""
    print("Setting up the environment...")
    print("Setup complete")


def deploy(file_path_str: str) -> None:
    file_paths = [path.strip() for path in file_path_str.split(",")]
    DeployHandler(bucket_name="yee", file_paths=file_paths, deploy_name="test").deploy()


def status() -> None:
    """Check the status of the application."""
    print("Checking the status of the application...")
    print("Status checked")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A CLI tool with setup, deploy, and status commands."
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    subparsers.add_parser("setup", help="Setup the environment.")

    parser_deploy = subparsers.add_parser("deploy", help="Deploy the application.")
    parser_deploy.add_argument(
        "file_paths", type=str, help="A comma-separated list of file paths to deploy."
    )

    subparsers.add_parser("status", help="Check the status of the application.")

    return parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()
    if args.command == "setup":
        setup()
    elif args.command == "deploy":
        deploy(args.file_paths)
    elif args.command == "status":
        status()
    else:
        print("Unknown command")
        parser.print_help()


if __name__ == "__main__":
    main()
