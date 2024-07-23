from __future__ import annotations

import argparse

from gauge.cli.deploy import DeployHandler


def deploy(file_path_str: str) -> None:
    file_paths = [path.strip() for path in file_path_str.split(",")]
    DeployHandler(file_paths=file_paths).deploy()


def status() -> None:
    """Check the status of the application."""
    print("Checking the status of the application...")
    print("Status checked")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A CLI tool to deploy python lambdas with a single command"
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    parser_deploy = subparsers.add_parser("deploy", help="Deploy the application.")
    parser_deploy.add_argument(
        "file_paths", type=str, help="A comma-separated list of file paths to deploy."
    )

    subparsers.add_parser("status", help="Check the status of the application.")

    return parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()
    if args.command == "deploy":
        deploy(args.file_paths)
    elif args.command == "status":
        status()
    else:
        print("Unknown command")
        parser.print_help()


if __name__ == "__main__":
    main()
