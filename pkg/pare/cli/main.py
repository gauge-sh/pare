from __future__ import annotations

import argparse

from rich.console import Console

from pare.cli.delete import delete_function
from pare.cli.deploy import DeployHandler
from pare.cli.status import show_status
from pare.client import get_current_git_hash
from pare.login import login


def parse_env_vars(env_vars: list[str]) -> dict[str, str]:
    environment_variables: dict[str, str] = {}
    try:
        for env_var in env_vars:
            key, value = env_var.split("=")
            environment_variables[key] = value
    except ValueError:
        raise ValueError("Environment variables must be in the format KEY=VALUE")
    return environment_variables


def deploy(file_paths: list[str], env_vars: list[str]) -> None:
    environment_variables = parse_env_vars(env_vars)
    DeployHandler(
        file_paths=file_paths, environment_variables=environment_variables
    ).deploy()


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
    show_status()


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
    parser_deploy.add_argument(
        "-e",
        "--env",
        action="append",
        dest="env_vars",
        help="Specify an environment variable in the format KEY=VALUE. Can be used multiple times.",
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
        deploy(args.file_paths, env_vars=args.env_vars)
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
