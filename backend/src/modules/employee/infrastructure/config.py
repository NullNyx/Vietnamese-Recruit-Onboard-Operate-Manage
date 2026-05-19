"""Employee module configuration.

Loads employee module settings from environment variables with the EMPLOYEE_ prefix.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmployeeSettings(BaseSettings):
    """Employee module configuration loaded from environment variables.

    All environment variables are prefixed with ``EMPLOYEE_``. For example,
    ``minio_endpoint`` maps to ``EMPLOYEE_MINIO_ENDPOINT``.

    Attributes:
        minio_endpoint: MinIO server endpoint (host:port).
        minio_access_key: MinIO access key for authentication.
        minio_secret_key: MinIO secret key for authentication.
        minio_bucket: MinIO bucket name for employee documents.
        max_file_size_mb: Maximum allowed file upload size in megabytes.
    """

    model_config = SettingsConfigDict(env_prefix="EMPLOYEE_")

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "employee-documents"

    # File upload limits
    max_file_size_mb: int = Field(default=10, gt=0)
