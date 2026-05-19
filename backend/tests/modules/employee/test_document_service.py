"""Unit tests for DocumentService."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.employee.application.document_service import (
    ALLOWED_MIME_TYPES,
    DocumentService,
)
from src.modules.employee.domain.entities import Employee, EmployeeDocument
from src.modules.employee.domain.exceptions import (
    EmployeeError,
    EmployeeNotFoundError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from src.modules.employee.infrastructure.config import EmployeeSettings


@pytest.fixture
def document_repo() -> AsyncMock:
    """Create a mock DocumentRepository."""
    return AsyncMock()


@pytest.fixture
def employee_repo() -> AsyncMock:
    """Create a mock EmployeeRepository."""
    return AsyncMock()


@pytest.fixture
def minio_client() -> AsyncMock:
    """Create a mock MinIOClient."""
    return AsyncMock()


@pytest.fixture
def settings() -> EmployeeSettings:
    """Create EmployeeSettings with default test values."""
    return EmployeeSettings(
        minio_endpoint="localhost:9000",
        minio_access_key="minioadmin",
        minio_secret_key="minioadmin",
        minio_bucket="employee-documents",
        max_file_size_mb=10,
    )


@pytest.fixture
def service(
    document_repo: AsyncMock,
    employee_repo: AsyncMock,
    minio_client: AsyncMock,
    settings: EmployeeSettings,
) -> DocumentService:
    """Create a DocumentService with mocked dependencies."""
    return DocumentService(
        document_repository=document_repo,
        employee_repository=employee_repo,
        minio_client=minio_client,
        settings=settings,
    )


class TestListDocuments:
    """Tests for DocumentService.list_documents."""

    async def test_returns_documents_when_employee_exists(
        self, service: DocumentService, employee_repo: AsyncMock, document_repo: AsyncMock
    ) -> None:
        """list_documents returns documents when employee is found."""
        emp_id = uuid4()
        employee_repo.get_by_id.return_value = MagicMock(spec=Employee)
        mock_docs = [MagicMock(spec=EmployeeDocument), MagicMock(spec=EmployeeDocument)]
        document_repo.list_by_employee.return_value = mock_docs

        result = await service.list_documents(emp_id)

        employee_repo.get_by_id.assert_called_once_with(emp_id)
        document_repo.list_by_employee.assert_called_once_with(emp_id)
        assert result == mock_docs

    async def test_raises_not_found_when_employee_missing(
        self, service: DocumentService, employee_repo: AsyncMock
    ) -> None:
        """list_documents raises EmployeeNotFoundError when employee doesn't exist."""
        employee_repo.get_by_id.return_value = None

        with pytest.raises(EmployeeNotFoundError):
            await service.list_documents(uuid4())


class TestUploadDocument:
    """Tests for DocumentService.upload_document."""

    async def test_successful_upload(
        self,
        service: DocumentService,
        employee_repo: AsyncMock,
        minio_client: AsyncMock,
        document_repo: AsyncMock,
    ) -> None:
        """upload_document stores file in MinIO and creates metadata record."""
        emp_id = uuid4()
        employee_repo.get_by_id.return_value = MagicMock(spec=Employee)
        minio_client.upload_file.return_value = f"employees/{emp_id}/cccd/id_card.pdf"
        mock_doc = MagicMock(spec=EmployeeDocument)
        document_repo.create.return_value = mock_doc

        result = await service.upload_document(
            employee_id=emp_id,
            document_type="cccd",
            file_name="id_card.pdf",
            file_data=b"fake pdf content",
            content_type="application/pdf",
        )

        expected_path = f"employees/{emp_id}/cccd/id_card.pdf"
        minio_client.upload_file.assert_called_once_with(
            expected_path, b"fake pdf content", "application/pdf"
        )
        document_repo.create.assert_called_once()
        created_doc = document_repo.create.call_args[0][0]
        assert created_doc.employee_id == emp_id
        assert created_doc.document_type == "cccd"
        assert created_doc.file_name == "id_card.pdf"
        assert created_doc.storage_path == expected_path
        assert created_doc.file_size == len(b"fake pdf content")
        assert created_doc.mime_type == "application/pdf"
        assert result == mock_doc

    async def test_raises_not_found_when_employee_missing(
        self, service: DocumentService, employee_repo: AsyncMock
    ) -> None:
        """upload_document raises EmployeeNotFoundError when employee doesn't exist."""
        employee_repo.get_by_id.return_value = None

        with pytest.raises(EmployeeNotFoundError):
            await service.upload_document(
                employee_id=uuid4(),
                document_type="cccd",
                file_name="id.pdf",
                file_data=b"data",
                content_type="application/pdf",
            )

    async def test_raises_file_too_large(
        self, service: DocumentService, employee_repo: AsyncMock
    ) -> None:
        """upload_document raises FileTooLargeError when file exceeds max size."""
        employee_repo.get_by_id.return_value = MagicMock(spec=Employee)
        # 10MB + 1 byte
        oversized_data = b"x" * (10 * 1024 * 1024 + 1)

        with pytest.raises(FileTooLargeError):
            await service.upload_document(
                employee_id=uuid4(),
                document_type="cccd",
                file_name="big_file.pdf",
                file_data=oversized_data,
                content_type="application/pdf",
            )

    async def test_allows_exact_max_size(
        self,
        service: DocumentService,
        employee_repo: AsyncMock,
        minio_client: AsyncMock,
        document_repo: AsyncMock,
    ) -> None:
        """upload_document allows files exactly at the max size limit."""
        employee_repo.get_by_id.return_value = MagicMock(spec=Employee)
        document_repo.create.return_value = MagicMock(spec=EmployeeDocument)
        # Exactly 10MB
        exact_data = b"x" * (10 * 1024 * 1024)

        await service.upload_document(
            employee_id=uuid4(),
            document_type="cccd",
            file_name="exact.pdf",
            file_data=exact_data,
            content_type="application/pdf",
        )

        minio_client.upload_file.assert_called_once()

    async def test_raises_unsupported_file_type(
        self, service: DocumentService, employee_repo: AsyncMock
    ) -> None:
        """upload_document raises UnsupportedFileTypeError for invalid MIME types."""
        employee_repo.get_by_id.return_value = MagicMock(spec=Employee)

        with pytest.raises(UnsupportedFileTypeError):
            await service.upload_document(
                employee_id=uuid4(),
                document_type="cccd",
                file_name="script.exe",
                file_data=b"binary data",
                content_type="application/x-executable",
            )

    async def test_all_allowed_mime_types_accepted(
        self,
        service: DocumentService,
        employee_repo: AsyncMock,
        minio_client: AsyncMock,
        document_repo: AsyncMock,
    ) -> None:
        """upload_document accepts all MIME types in the allowed list."""
        employee_repo.get_by_id.return_value = MagicMock(spec=Employee)
        document_repo.create.return_value = MagicMock(spec=EmployeeDocument)

        for mime_type in ALLOWED_MIME_TYPES:
            await service.upload_document(
                employee_id=uuid4(),
                document_type="cccd",
                file_name="file.dat",
                file_data=b"data",
                content_type=mime_type,
            )


class TestDownloadDocument:
    """Tests for DocumentService.download_document."""

    async def test_returns_metadata_and_file_bytes(
        self,
        service: DocumentService,
        document_repo: AsyncMock,
        minio_client: AsyncMock,
    ) -> None:
        """download_document returns document metadata and file bytes."""
        doc_id = uuid4()
        mock_doc = MagicMock(spec=EmployeeDocument)
        mock_doc.storage_path = "employees/123/cccd/id.pdf"
        document_repo.get_by_id.return_value = mock_doc
        minio_client.download_file.return_value = b"file content"

        metadata, file_data = await service.download_document(doc_id)

        document_repo.get_by_id.assert_called_once_with(doc_id)
        minio_client.download_file.assert_called_once_with("employees/123/cccd/id.pdf")
        assert metadata == mock_doc
        assert file_data == b"file content"

    async def test_raises_error_when_document_not_found(
        self, service: DocumentService, document_repo: AsyncMock
    ) -> None:
        """download_document raises EmployeeError when document doesn't exist."""
        document_repo.get_by_id.return_value = None

        with pytest.raises(EmployeeError, match="Document not found"):
            await service.download_document(uuid4())


class TestDeleteDocument:
    """Tests for DocumentService.delete_document."""

    async def test_deletes_from_minio_and_db(
        self,
        service: DocumentService,
        document_repo: AsyncMock,
        minio_client: AsyncMock,
    ) -> None:
        """delete_document removes file from MinIO and metadata from DB."""
        doc_id = uuid4()
        mock_doc = MagicMock(spec=EmployeeDocument)
        mock_doc.storage_path = "employees/456/degree/diploma.pdf"
        document_repo.get_by_id.return_value = mock_doc
        document_repo.delete.return_value = True

        await service.delete_document(doc_id)

        minio_client.delete_file.assert_called_once_with(
            "employees/456/degree/diploma.pdf"
        )
        document_repo.delete.assert_called_once_with(doc_id)

    async def test_raises_error_when_document_not_found(
        self, service: DocumentService, document_repo: AsyncMock
    ) -> None:
        """delete_document raises EmployeeError when document doesn't exist."""
        document_repo.get_by_id.return_value = None

        with pytest.raises(EmployeeError, match="Document not found"):
            await service.delete_document(uuid4())
