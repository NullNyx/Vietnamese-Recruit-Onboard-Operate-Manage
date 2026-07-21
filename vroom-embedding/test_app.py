"""Tests for the vroom-embedding service.

Uses FastAPI TestClient with a mock SentenceTransformer to verify
the /embed and /health endpoints without requiring the real model.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import numpy as np
import pytest


def _fake_encode(texts: list[str], **kwargs: object) -> np.ndarray:
    """Return an embedding per text with a distinct non-zero pattern.

    Each embedding is a 768-dim vector where position 0 carries a
    deterministic value derived from the text length so tests can
    assert each text produces a unique, non-zero vector.
    """
    vectors = np.zeros((len(texts), 768), dtype=np.float32)
    for i, t in enumerate(texts):
        vectors[i, 0] = float(len(t) % 100 + i)
        vectors[i, 1] = 0.1 * (i + 1)
    return vectors


# Create a fake sentence_transformers module before importing app,
# since app does ``from sentence_transformers import SentenceTransformer``
# at module level.
_fake_st = ModuleType("sentence_transformers")
_fake_st.SentenceTransformer = MagicMock()
_fake_st.SentenceTransformer.return_value.encode.side_effect = _fake_encode
_fake_st.SentenceTransformer.return_value.max_seq_length = 512
sys.modules["sentence_transformers"] = _fake_st

from fastapi.testclient import TestClient  # noqa: E402

from app import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    """Create a TestClient with the embedding app (model already mocked)."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestEmbedEndpoint:
    """Tests for POST /embed."""

    def test_embed_single_text_returns_768_dim_vector(self, client: TestClient) -> None:
        payload = {"texts": ["Xin chào"]}
        response = client.post("/embed", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "embeddings" in data
        assert len(data["embeddings"]) == 1
        assert len(data["embeddings"][0]) == 768

    def test_embed_multiple_texts_returns_correct_count(self, client: TestClient) -> None:
        payload = {"texts": ["Text một", "Text hai", "Text ba"]}
        response = client.post("/embed", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["embeddings"]) == 3

    def test_embed_vietnamese_with_diacritics(self, client: TestClient) -> None:
        """Verify Vietnamese text with diacritics is accepted and encoded."""
        payload = {
            "texts": [
                "Người lao động được nghỉ phép năm 12 ngày",
                "Quy chế phúc lợi áp dụng từ ngày 01/01/2025",
            ]
        }
        response = client.post("/embed", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["embeddings"]) == 2
        for emb in data["embeddings"]:
            assert len(emb) == 768
            # Should not be all zeros
            assert any(abs(v) > 1e-9 for v in emb)

    def test_embed_empty_texts_rejected(self, client: TestClient) -> None:
        payload: dict[str, list[str]] = {"texts": []}
        response = client.post("/embed", json=payload)
        assert response.status_code == 422

    def test_embed_missing_texts_field_rejected(self, client: TestClient) -> None:
        payload: dict[str, str] = {}
        response = client.post("/embed", json=payload)
        assert response.status_code == 422

    def test_embed_hundred_requests_stable(self, client: TestClient) -> None:
        """AC: Service chạy ổn định sau 100 request liên tiếp."""
        payload = {"texts": ["Kiểm tra độ ổn định"]}
        for i in range(100):
            response = client.post("/embed", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert len(data["embeddings"]) == 1
            assert len(data["embeddings"][0]) == 768

    def test_embed_returns_valid_non_null_vectors(self, client: TestClient) -> None:
        """Verify returned vectors are valid (not null, not NaN)."""
        payload = {"texts": ["Văn bản tiếng Việt có dấu đầy đủ"]}
        response = client.post("/embed", json=payload)
        assert response.status_code == 200
        data = response.json()
        emb = data["embeddings"][0]
        assert all(not (v is None or (isinstance(v, float) and v != v)) for v in emb)
