from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from gauge.cli.main import create_parser

if TYPE_CHECKING:
    from pytest import CaptureFixture


def test_parser_deploy():
    parser = create_parser()
    args = parser.parse_args(["deploy", "test_file.py"])
    assert args.command == "deploy"
    assert args.file_paths == "test_file.py"


def test_parser_deploy_no_file(capsys: CaptureFixture[str]):
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
