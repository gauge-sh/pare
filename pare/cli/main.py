from __future__ import annotations

import argparse

from rich.console import Console

from pare.cli.delete import delete_function
from pare.cli.deploy import DeployHandler
from pare.login import login


def deploy(file_path_str: str) -> None:
    file_paths = [path.strip() for path in file_path_str.split(",")]
    DeployHandler(file_paths=file_paths).deploy()


def delete(function_name: str) -> None:
    console = Console()
    if (
        console.input(
            f"You are about to delete your deployed function called [bold red]'{function_name}'[/bold red]. "
            "Type the function name to confirm: "
        )
        == function_name
    ):
        delete_function(function_name)
        console.print(f"[bold red]'{function_name}' deleted.[/bold red]")
    else:
        console.print("[bold white]Operation cancelled.[/bold white]")


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

    subparsers.add_parser("login", help="Authenticate with github.")

    parser_deploy = subparsers.add_parser("deploy", help="Deploy the application.")
    parser_deploy.add_argument(
        "file_paths", type=str, help="A comma-separated list of file paths to deploy."
    )

    subparsers.add_parser("status", help="Check the status of the application.")

    parser_delete = subparsers.add_parser("delete", help="Delete a deployed function.")
    parser_delete.add_argument(
        "function_name", type=str, help="The name of the function to delete."
    )

    return parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()
    if args.command == "deploy":
        deploy(args.file_paths)
    elif args.command == "status":
        status()
    elif args.command == "delete":
        delete(args.function_name)
    elif args.command == "login":
        login()
    else:
        print("Unknown command")
        parser.print_help()


if __name__ == "__main__":
    main()
