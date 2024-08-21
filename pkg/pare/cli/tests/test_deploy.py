from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pare.cli.deploy import DeployHandler
from pare.models import ServiceConfig


@pytest.fixture
def temp_directory(tmp_path) -> Path:
    # Create temporary files
    (tmp_path / "file1.py").touch()
    (tmp_path / "file2.py").touch()
    return tmp_path


@pytest.fixture
def deploy_handler(temp_directory):
    return DeployHandler([str(temp_directory / "*.py")])


def test_init(temp_directory):
    handler = DeployHandler([str(temp_directory / "*.py")])
    assert len(handler.file_paths) == 2
    assert all(file.name in ["file1.py", "file2.py"] for file in handler.file_paths)


def test_bundle(deploy_handler, tmp_path):
    with patch("zipfile.ZipFile") as mock_zipfile:
        result = deploy_handler.bundle(tmp_path)
        assert isinstance(result, Path)
        assert result.name.endswith(".zip")
        mock_zipfile.assert_called_once()


@patch.object(DeployHandler, "register_services")
@patch.object(DeployHandler, "bundle")
@patch.object(DeployHandler, "upload")
def test_deploy(
    mock_upload: MagicMock,
    mock_bundle: MagicMock,
    mock_register: MagicMock,
    deploy_handler: DeployHandler,
) -> None:
    mock_register.return_value = [
        ServiceConfig(name="test", path="test", requirements=[])
    ]
    mock_bundle.return_value = Path("test.zip")

    deploy_handler.deploy()

    mock_register.assert_called_once()
    mock_bundle.assert_called_once()
    mock_upload.assert_called_once()
