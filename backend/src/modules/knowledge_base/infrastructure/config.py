"""Knowledge Base module configuration.

Loads knowledge base module settings from environment variables with the KB_ prefix.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class KnowledgeBaseSettings(BaseSettings):
    """Knowledge Base module configuration loaded from environment variables.

    All environment variables are prefixed with ``KB_``.
    """

    model_config = SettingsConfigDict(env_prefix="KB_")

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "knowledge-base"

    # Embedding service
    embedding_service_url: str = "http://localhost:8080"

    # Redis (for ARQ worker)
    redis_url: str = "redis://localhost:6379/0"

    # Database (for ARQ worker — same as main DB)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vroom_hr"

    # File upload limits
    max_file_size_mb: int = Field(default=20, gt=0)

    # Chunking
    chunk_size_tokens: int = Field(default=512, gt=0)
    chunk_overlap_tokens: int = Field(default=50, ge=0)
