from __future__ import annotations

import pytest

from cli.main import create_parser


def test_parser_setup():
    parser = create_parser()
    args = parser.parse_args(["setup"])
    assert args.command == "setup"


def test_parser_deploy():
    parser = create_parser()
    args = parser.parse_args(["deploy", "test_file.txt"])
    assert args.command == "deploy"
    assert args.file == "test_file.txt"


def test_parser_deploy_no_file(capsys):
    parser = create_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["deploy"])
    assert exc.value.code == 2

    captured = capsys.readouterr()
    assert "the following arguments are required: file" in captured.err


def test_parser_status():
    parser = create_parser()
    args = parser.parse_args(["status"])
    assert args.command == "status"
