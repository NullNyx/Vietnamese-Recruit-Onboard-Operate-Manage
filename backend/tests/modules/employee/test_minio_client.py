"""Tests for MinIO client adapter."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.employee.infrastructure.config import EmployeeSettings
from src.modules.employee.infrastructure.minio_client import MinIOClient


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch) -> EmployeeSettings:
    monkeypatch.setenv("EMPLOYEE_MINIO_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("EMPLOYEE_MINIO_ACCESS_KEY", "testkey")
    monkeypatch.setenv("EMPLOYEE_MINIO_SECRET_KEY", "testsecret")
    monkeypatch.setenv("EMPLOYEE_MINIO_BUCKET", "test-bucket")
    return EmployeeSettings()


@pytest.fixture
def client(settings: EmployeeSettings) -> MinIOClient:
    return MinIOClient(settings)


class TestMinIOClientInit:
    """Verify MinIOClient initialization."""

    def test_endpoint_url_uses_http_prefix(self, client: MinIOClient) -> None:
        assert client._endpoint_url == "http://localhost:9000"

    def test_stores_settings(self, client: MinIOClient, settings: EmployeeSettings) -> None:
        assert client._settings is settings


class TestMinIOClientUpload:
    """Verify upload_file behavior."""

    async def test_upload_file_returns_path(self, client: MinIOClient) -> None:
        mock_s3 = AsyncMock()
        mock_s3.head_bucket = AsyncMock()
        mock_s3.upload_fileobj = AsyncMock()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_context.__aexit__ = AsyncMock(return_value=False)

        with patch.object(client, "_client_context", return_value=mock_context):
            result = await client.upload_file(
                "employees/123/cccd/front.jpg", b"file-data", "image/jpeg"
            )

        assert result == "employees/123/cccd/front.jpg"

    async def test_upload_file_calls_upload_fileobj(self, client: MinIOClient) -> None:
        mock_s3 = AsyncMock()
        mock_s3.head_bucket = AsyncMock()
        mock_s3.upload_fileobj = AsyncMock()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_context.__aexit__ = AsyncMock(return_value=False)

        with patch.object(client, "_client_context", return_value=mock_context):
            await client.upload_file("path/to/file.pdf", b"data", "application/pdf")

        mock_s3.upload_fileobj.assert_called_once()
        call_args = mock_s3.upload_fileobj.call_args
        assert call_args[0][1] == "test-bucket"
        assert call_args[0][2] == "path/to/file.pdf"
        assert call_args[1]["ExtraArgs"] == {"ContentType": "application/pdf"}

    async def test_upload_creates_bucket_if_not_exists(self, client: MinIOClient) -> None:
        mock_s3 = AsyncMock()
        mock_s3.exceptions = MagicMock()
        mock_s3.exceptions.ClientError = Exception
        mock_s3.head_bucket = AsyncMock(side_effect=Exception("Not found"))
        mock_s3.create_bucket = AsyncMock()
        mock_s3.upload_fileobj = AsyncMock()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_context.__aexit__ = AsyncMock(return_value=False)

        with patch.object(client, "_client_context", return_value=mock_context):
            await client.upload_file("path/file.txt", b"data", "text/plain")

        mock_s3.create_bucket.assert_called_once_with(Bucket="test-bucket")


class TestMinIOClientDownload:
    """Verify download_file behavior."""

    async def test_download_file_returns_bytes(self, client: MinIOClient) -> None:
        mock_body = AsyncMock()
        mock_body.read = AsyncMock(return_value=b"file-content")

        mock_s3 = AsyncMock()
        mock_s3.get_object = AsyncMock(return_value={"Body": mock_body})

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_context.__aexit__ = AsyncMock(return_value=False)

        with patch.object(client, "_client_context", return_value=mock_context):
            result = await client.download_file("employees/123/cccd/front.jpg")

        assert result == b"file-content"

    async def test_download_file_uses_correct_bucket_and_key(
        self, client: MinIOClient
    ) -> None:
        mock_body = AsyncMock()
        mock_body.read = AsyncMock(return_value=b"data")

        mock_s3 = AsyncMock()
        mock_s3.get_object = AsyncMock(return_value={"Body": mock_body})

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_context.__aexit__ = AsyncMock(return_value=False)

        with patch.object(client, "_client_context", return_value=mock_context):
            await client.download_file("some/path/doc.pdf")

        mock_s3.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="some/path/doc.pdf"
        )


class TestMinIOClientDelete:
    """Verify delete_file behavior."""

    async def test_delete_file_calls_delete_object(self, client: MinIOClient) -> None:
        mock_s3 = AsyncMock()
        mock_s3.delete_object = AsyncMock()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_context.__aexit__ = AsyncMock(return_value=False)

        with patch.object(client, "_client_context", return_value=mock_context):
            await client.delete_file("employees/123/cccd/front.jpg")

        mock_s3.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="employees/123/cccd/front.jpg"
        )

    async def test_delete_file_returns_none(self, client: MinIOClient) -> None:
        mock_s3 = AsyncMock()
        mock_s3.delete_object = AsyncMock()

        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_context.__aexit__ = AsyncMock(return_value=False)

        with patch.object(client, "_client_context", return_value=mock_context):
            result = await client.delete_file("path/to/file.txt")

        assert result is None
