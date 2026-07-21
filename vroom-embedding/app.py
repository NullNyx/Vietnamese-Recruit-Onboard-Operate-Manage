"""Vroom Embedding Service.

FastAPI service that loads AITeamVN/Vietnamese_Embedding_v2 and exposes
a single ``POST /embed`` endpoint that accepts a list of texts and returns
their 768-dimensional embedding vectors.

This service runs as a standalone Docker container (``vroom-embedding``)
and is called by the backend's Knowledge Base ingestion pipeline and
retrieval functions.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = os.environ.get("EMBEDDING_MODEL_NAME", "AITeamVN/Vietnamese_Embedding_v2")
MODEL_CACHE_DIR = os.environ.get("MODEL_CACHE_DIR", "/app/model_cache")
HF_TOKEN = os.environ.get("HF_TOKEN") or None

os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

model_kwargs = {"cache_folder": MODEL_CACHE_DIR}
if HF_TOKEN:
    model_kwargs["token"] = HF_TOKEN

logger.info("Loading embedding model: %s (cache: %s, auth: %s)", MODEL_NAME, MODEL_CACHE_DIR, bool(HF_TOKEN))
model: SentenceTransformer = SentenceTransformer(MODEL_NAME, **model_kwargs)
logger.info("Embedding model loaded successfully. Max seq length: %s", model.max_seq_length)


app = FastAPI(
    title="Vroom Embedding Service",
    description="Vietnamese text embedding service using AITeamVN/Vietnamese_Embedding_v2",
    version="0.1.0",
)


class EmbedRequest(BaseModel):
    """Request body for the /embed endpoint.

    Attributes:
        texts: List of input texts to embed. Each text should be a natural
            language string (typically Vietnamese). The service will tokenize
            and encode each text into a 768-dimensional vector.
    """

    texts: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of texts to embed (1-100 items per request)",
    )


class EmbedResponse(BaseModel):
    """Response from the /embed endpoint.

    Attributes:
        embeddings: List of embedding vectors, where each vector is a list
            of 768 floats. The ordering matches the input texts list.
    """

    embeddings: list[list[float]]


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for Docker healthcheck.

    Returns:
        ``{"status": "ok"}`` when the service and model are ready.
    """
    return {"status": "ok"}


@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest) -> EmbedResponse:
    """Encode a list of texts into 768-dimensional embedding vectors.

    Args:
        request: Contains the list of texts to embed.

    Returns:
        ``EmbedResponse`` with the corresponding embeddings.

    Raises:
        HTTPException 500: If the model fails to encode the input.
    """
    try:
        # sentence-transformers encode returns a numpy array of shape
        # (len(texts), 768). We convert to list[list[float]] for JSON.
        vectors = model.encode(
            request.texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        embeddings: list[list[float]] = vectors.tolist()
        return EmbedResponse(embeddings=embeddings)
    except Exception as exc:
        logger.exception("Embedding encoding failed for %d texts", len(request.texts))
        raise HTTPException(
            status_code=500,
            detail=f"Embedding encoding failed: {exc}",
        ) from exc
