"""Knowledge Base document repository.

Provides async CRUD operations for both HR and Employee Knowledge Base
documents and chunks. Methods dispatch to the correct physical table based
on kb_type (physical security isolation per Issue #260).
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import and_, func, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.modules.knowledge_base.domain.entities import (
    EmployeeKnowledgeBaseChunk,
    EmployeeKnowledgeBaseDocument,
    KnowledgeBaseChunk,
    KnowledgeBaseDocument,
)

# ---------------------------------------------------------------------------
# Entity dispatch helpers
# ---------------------------------------------------------------------------

_DOC_ENTITY_MAP: dict[str, type] = {
    "hr": KnowledgeBaseDocument,
    "employee": EmployeeKnowledgeBaseDocument,
}

_CHUNK_ENTITY_MAP: dict[str, type] = {
    "hr": KnowledgeBaseChunk,
    "employee": EmployeeKnowledgeBaseChunk,
}

_VALID_KB_TYPES = frozenset({"hr", "employee"})


def _get_doc_entity(kb_type: str) -> type:
    """Return the document entity class for a kb_type."""
    if kb_type not in _VALID_KB_TYPES:
        raise ValueError(f"Invalid kb_type: {kb_type}. Must be one of {_VALID_KB_TYPES}.")
    return _DOC_ENTITY_MAP[kb_type]


def _get_chunk_entity(kb_type: str) -> type:
    """Return the chunk entity class for a kb_type."""
    if kb_type not in _VALID_KB_TYPES:
        raise ValueError(f"Invalid kb_type: {kb_type}. Must be one of {_VALID_KB_TYPES}.")
    return _CHUNK_ENTITY_MAP[kb_type]


class KnowledgeBaseRepository:
    """Async repository for Knowledge Base documents and chunks.

    All methods receive and share a single AsyncSession; transaction
    boundaries are owned by the caller (service layer).

    Handles both HR and Employee KB tables with physical separation.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    async def insert_document(
        self,
        doc: KnowledgeBaseDocument | EmployeeKnowledgeBaseDocument,
    ) -> KnowledgeBaseDocument | EmployeeKnowledgeBaseDocument:
        """Insert a new document record and return it with the generated id.

        The document entity itself carries the kb_type, so the correct
        table is used automatically via SQLModel inheritance.
        """
        self._session.add(doc)
        await self._session.flush()
        return doc

    async def get_document(
        self,
        document_id: uuid.UUID,
        kb_type: str = "hr",
    ) -> KnowledgeBaseDocument | EmployeeKnowledgeBaseDocument | None:
        """Fetch a single document by id from the appropriate table."""
        doc_entity = _get_doc_entity(kb_type)
        result = await self._session.execute(select(doc_entity).where(doc_entity.id == document_id))
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        kb_type: str = "hr",
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        status: str | None = None,
    ) -> tuple[Sequence, int]:
        """List documents with pagination and optional filters, ordered by created_at DESC.

        Queries only the table for the given kb_type.
        Supports optional filtering by category and/or status (Issue #261, KB-05).

        Returns:
            Tuple of (documents, total_count).
        """
        doc_entity = _get_doc_entity(kb_type)

        # Build where clauses
        conditions = [doc_entity.kb_type == kb_type]
        if category:
            conditions.append(doc_entity.category == category)
        if status:
            conditions.append(doc_entity.status == status)

        where_clause = and_(*conditions)

        # Total count
        count_result = await self._session.execute(
            select(func.count()).select_from(doc_entity).where(where_clause)
        )
        total = count_result.scalar_one()

        # Paginated query
        offset = (page - 1) * page_size
        result = await self._session.execute(
            select(doc_entity)
            .where(where_clause)
            .order_by(col(doc_entity.created_at).desc())
            .offset(offset)
            .limit(page_size)
        )
        docs = result.scalars().all()
        return docs, total

    async def update_document_metadata(
        self,
        document_id: uuid.UUID,
        *,
        kb_type: str = "hr",
        display_name: str | None = None,
        category: str | None = None,
        description: str | None = None,
    ) -> KnowledgeBaseDocument | EmployeeKnowledgeBaseDocument | None:
        """Update document metadata (display_name, category, description).

        Does NOT modify file, chunks, or indexing. Returns the updated
        document or None if not found (Issue #261, KB-05).
        """
        doc = await self.get_document(document_id, kb_type=kb_type)
        if doc is None:
            return None
        if display_name is not None:
            doc.display_name = display_name
        if category is not None:
            doc.category = category
        if description is not None:
            doc.description = description
        doc.updated_at = datetime.now(UTC)
        await self._session.flush()
        return doc

    async def update_document_status(
        self,
        document_id: uuid.UUID,
        status: str,
        *,
        kb_type: str = "hr",
        chunk_count: int | None = None,
        error_message: str | None = None,
    ) -> KnowledgeBaseDocument | EmployeeKnowledgeBaseDocument | None:
        """Update document status and related fields.

        Returns the updated document or None if not found.
        """
        doc = await self.get_document(document_id, kb_type=kb_type)
        if doc is None:
            return None
        doc.status = status
        doc.updated_at = datetime.now(UTC)
        if chunk_count is not None:
            doc.chunk_count = chunk_count
        if error_message is not None:
            doc.error_message = error_message
        await self._session.flush()
        return doc

    async def delete_document(
        self,
        document_id: uuid.UUID,
        kb_type: str = "hr",
    ) -> KnowledgeBaseDocument | EmployeeKnowledgeBaseDocument | None:
        """Hard-delete a document and its chunks.

        Deletes chunks first (via explicit DELETE to avoid ORM cascade issues
        with pgvector), then the document row itself. Returns the deleted
        document's metadata (including storage_path for MinIO cleanup)
        or None if not found (Issue #261, KB-05).
        """
        doc = await self.get_document(document_id, kb_type=kb_type)
        if doc is None:
            return None

        # Delete chunks first
        await self.delete_chunks_by_document(document_id, kb_type=kb_type)

        # Store storage_path for caller (MinIO cleanup)
        storage_path = doc.storage_path

        # Delete document row
        await self._session.delete(doc)
        await self._session.flush()

        # Set storage_path on the detached object for caller convenience
        doc.storage_path = storage_path
        return doc

    # ------------------------------------------------------------------
    # Chunks
    # ------------------------------------------------------------------

    async def insert_chunks(
        self,
        chunks: list[KnowledgeBaseChunk | EmployeeKnowledgeBaseChunk],
    ) -> None:
        """Insert multiple chunks in bulk. Each chunk knows its own table."""
        self._session.add_all(chunks)
        await self._session.flush()

    async def delete_chunks_by_document(
        self,
        document_id: uuid.UUID,
        kb_type: str = "hr",
    ) -> None:
        """Delete all chunks for a document (used before re-ingestion)."""
        from sqlalchemy import delete

        chunk_entity = _get_chunk_entity(kb_type)
        await self._session.execute(
            delete(chunk_entity).where(
                chunk_entity.document_id == document_id,
            )
        )
        await self._session.flush()

    # ------------------------------------------------------------------
    # Similarity search
    # ------------------------------------------------------------------

    async def search_similar_chunks(
        self,
        query_embedding: list[float],
        kb_types: list[str] | None = None,
        top_k: int = 3,
        similarity_threshold: float = 0.7,
    ) -> list[tuple,]:
        """Find chunks semantically similar to query_embedding via pgvector cosine distance.

        Joins with the appropriate document table to filter by kb_type and retrieve
        the document's display_name for citation formatting.

        When kb_types includes both 'hr' and 'employee', queries both table sets
        via UNION ALL and returns the top_k results overall.

        Cosine similarity = 1 - cosine_distance.
        We filter where cosine_distance < (1 - similarity_threshold).

        Args:
            query_embedding: The embedding vector of the query text.
            kb_types: Optional list of kb_type values to filter (e.g. ['hr']).
            top_k: Maximum number of chunks to return.
            similarity_threshold: Minimum cosine similarity (0.0-1.0).

        Returns:
            List of (chunk, document_display_name, similarity_score) tuples.
        """
        if kb_types is None:
            kb_types = ["hr"]

        # Validate kb_types
        for kbt in kb_types:
            if kbt not in _VALID_KB_TYPES:
                raise ValueError(f"Invalid kb_type: {kbt}. Must be one of {_VALID_KB_TYPES}.")

        max_distance = 1.0 - similarity_threshold

        # Build a subquery for each kb_type and UNION ALL
        subqueries = []
        for kbt in kb_types:
            doc_entity = _get_doc_entity(kbt)
            chunk_entity = _get_chunk_entity(kbt)

            subq = (
                select(
                    chunk_entity.id.label("chunk_id"),
                    chunk_entity.document_id.label("document_id"),
                    chunk_entity.chunk_index.label("chunk_index"),
                    chunk_entity.content.label("content"),
                    chunk_entity.token_count.label("token_count"),
                    chunk_entity.created_at.label("chunk_created_at"),
                    doc_entity.display_name.label("display_name"),
                    (1.0 - chunk_entity.embedding.cosine_distance(query_embedding)).label(
                        "similarity"
                    ),
                )
                .join(
                    doc_entity,
                    chunk_entity.document_id == doc_entity.id,
                )
                .where(
                    chunk_entity.embedding.isnot(None),
                    doc_entity.status == "ready",
                    chunk_entity.embedding.cosine_distance(query_embedding) < max_distance,
                )
            )
            subqueries.append(subq)

        if len(subqueries) == 1:
            stmt = (
                subqueries[0]
                .order_by(subqueries[0].selected_columns.similarity.desc())
                .limit(top_k)
            )
        else:
            union_stmt = union_all(*subqueries).subquery()
            stmt = select(union_stmt).order_by(union_stmt.c.similarity.desc()).limit(top_k)

        result = await self._session.execute(stmt)
        rows = result.all()

        # Reconstruct chunk-like objects from rows.
        # We return tuples of (chunk_dict, display_name, similarity) since we can't
        # reconstruct full ORM objects from UNION results.
        # The RetrievalService only uses .content and .strip() on the chunk.
        class _ChunkProxy:
            """Minimal proxy for chunk results from UNION queries."""

            __slots__ = ("id", "document_id", "chunk_index", "content", "token_count", "created_at")

            def __init__(self, row: tuple) -> None:
                self.id = row.chunk_id
                self.document_id = row.document_id
                self.chunk_index = row.chunk_index
                self.content = row.content
                self.token_count = row.token_count
                self.created_at = row.chunk_created_at

        return [(_ChunkProxy(row), row.display_name, float(row.similarity)) for row in rows]
