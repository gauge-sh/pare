from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pare.cli.deploy import DeployHandler


@pytest.fixture
def deploy_handler() -> DeployHandler:
    return DeployHandler(["test_file.py"], "test_deploy")


def test_init() -> None:
    handler = DeployHandler(["file1.py", "file2.py"], "test_deploy")
    assert len(handler.file_paths) == 2
    assert handler.deploy_name == "test_deploy"

    handler_no_name = DeployHandler(["file1.py"])
    assert len(handler_no_name.file_paths) == 1
    assert len(handler_no_name.deploy_name) == 36  # UUID4 length


def test_validate_file_paths(deploy_handler: DeployHandler) -> None:
    with patch("pathlib.Path.exists", return_value=True), patch(
        "pathlib.Path.is_file", return_value=True
    ):
        deploy_handler.validate_file_paths()  # Should not raise any exception

    with pytest.raises(SystemExit):
        with patch("pathlib.Path.exists", return_value=False):
            deploy_handler.validate_file_paths()

    with pytest.raises(SystemExit):
        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.is_file", return_value=False
        ):
            deploy_handler.validate_file_paths()

    with pytest.raises(SystemExit):
        deploy_handler.file_paths = {Path("test_file.txt")}
        deploy_handler.validate_file_paths()


def test_bundle(deploy_handler: DeployHandler) -> None:
    with patch("zipfile.ZipFile") as mock_zipfile:
        result = deploy_handler.bundle("/tmp")
        assert isinstance(result, Path)
        assert result.name == f"{deploy_handler.deploy_name}.zip"
        mock_zipfile.assert_called_once()


@patch.object(DeployHandler, "validate_file_paths")
@patch.object(DeployHandler, "register_deployments")
@patch.object(DeployHandler, "bundle")
@patch.object(DeployHandler, "upload")
def test_deploy(
    mock_upload: MagicMock,
    mock_bundle: MagicMock,
    mock_register: MagicMock,
    mock_validate: MagicMock,
    deploy_handler: DeployHandler,
) -> None:
    mock_register.return_value = {"test_endpoint": {"function": "test_func"}}
    mock_bundle.return_value = Path("test.zip")

    deploy_handler.deploy()

    mock_validate.assert_called_once()
    mock_register.assert_called_once()
    mock_bundle.assert_called_once()
    mock_upload.assert_called_once()
