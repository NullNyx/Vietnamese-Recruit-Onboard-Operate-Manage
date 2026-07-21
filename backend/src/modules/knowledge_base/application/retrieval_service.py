"""Knowledge Base retrieval service.

Embeds a user query and performs pgvector similarity search across
document chunks, returning formatted context for injection into the
AI Assistant system prompt.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.modules.knowledge_base.application.ingestion_service import (
    call_embedding_service,
)
from src.modules.knowledge_base.infrastructure.config import KnowledgeBaseSettings

if TYPE_CHECKING:
    from src.modules.knowledge_base.infrastructure.repository import (
        KnowledgeBaseRepository,
    )

logger = logging.getLogger(__name__)


class RetrievalService:
    """Embeds a query and searches for relevant document chunks.

    Used by ContextBuilder to inject HR knowledge base content into
    the AI Assistant system prompt. Not exposed as a chat Read-Tool.
    """

    def __init__(
        self,
        repo: KnowledgeBaseRepository,
        settings: KnowledgeBaseSettings,
    ) -> None:
        self._repo = repo
        self._settings = settings

    async def retrieve(
        self,
        query: str,
        kb_types: list[str] | None = None,
        top_k: int = 3,
        similarity_threshold: float = 0.5,
    ) -> str:
        """Retrieve relevant chunks and format them for context injection.

        Args:
            query: The user's chat message text to search for.
            kb_types: KB type filters (e.g. ['hr'] or ['hr', 'employee']).
                      None means no filter (all KB types).
            top_k: Max chunks to retrieve.
            similarity_threshold: Minimum cosine similarity (0.0-1.0).

        Returns:
            Formatted context block string, or empty string if no relevant chunks found.
            Format:
                ---
                [TÀI LIỆU NỘI BỘ LIÊN QUAN]
                (Tên tài liệu): "nội dung chunk..."
                (Tên tài liệu 2): "nội dung chunk 2..."
                ---
        """
        try:
            # Step 1: Embed the query
            embedding_url = self._settings.embedding_service_url
            embeddings = await call_embedding_service([query], embedding_url, timeout=30.0)
            if not embeddings or not embeddings[0]:
                logger.warning("Embedding service returned empty result for query.")
                return ""
            query_embedding = embeddings[0]

            # Step 2: Search pgvector
            results = await self._repo.search_similar_chunks(
                query_embedding=query_embedding,
                kb_types=kb_types,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
            )

            if not results:
                return ""

            # Step 3: Format
            lines = ["---", "[TÀI LIỆU NỘI BỘ LIÊN QUAN]"]
            for chunk, display_name, similarity in results:
                # Trim very long chunks for prompt efficiency
                content = chunk.content.strip()
                if len(content) > 1500:
                    content = content[:1500] + "..."
                lines.append(f'({display_name}): "{content}"')
            lines.append("---")

            formatted = "\n".join(lines)
            logger.debug(
                "Retrieved %d chunks for query (kb_types=%s)",
                len(results),
                kb_types,
            )
            return formatted

        except Exception:
            logger.exception("Knowledge base retrieval failed")
            return ""
