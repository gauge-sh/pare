from __future__ import annotations

import argparse

from rich.console import Console

from pare.cli.delete import delete_function
from pare.cli.deploy import DeployHandler
from pare.client import get_current_git_hash
from pare.login import login


def deploy(file_paths: list[str]) -> None:
    DeployHandler(file_paths=file_paths).deploy()


def delete(function_name: str, git_hash: str = "", force: bool = False) -> None:
    console = Console()
    if not force and (
        console.input(
            f"You are about to delete your deployed function called [bold red]'{function_name}'[/bold red]. "
            "Type the function name to confirm: "
        )
        != function_name
    ):
        console.print("[bold white]Operation cancelled.[/bold white]")
        return

    if not git_hash:
        git_hash = get_current_git_hash()
    delete_function(function_name, git_hash=git_hash)
    console.print(
        f"[bold red]'{function_name}' (git hash: '{git_hash}') deleted.[/bold red]"
    )


def status() -> None:
    # how should this work?
    # hit list API for services
    # show a table using Rich
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
        "file_paths", nargs="+", type=str, help="One or more file paths to deploy."
    )

    subparsers.add_parser("status", help="Check the status of your deployed functions.")

    parser_delete = subparsers.add_parser("delete", help="Delete a deployed function.")
    parser_delete.add_argument(
        "function_name", type=str, help="The name of the function to delete."
    )
    parser_delete.add_argument(
        "-g",
        "--git-hash",
        nargs="?",
        type=str,
        help="The git hash of the function to delete.",
    )
    parser_delete.add_argument(
        "--force",
        action="store_true",
        help="Skip the confirmation prompt and delete the function.",
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
        delete(args.function_name, git_hash=args.git_hash, force=args.force)
    elif args.command == "login":
        login()
    else:
        print("Unknown command")
        parser.print_help()


if __name__ == "__main__":
    main()
