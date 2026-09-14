"""Create normalized Titan Text Embeddings V2 vectors for document chunks."""

from __future__ import annotations

from typing import Any

from askanydoc_rag.embeddings import embed_text


def embed_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach a Titan embedding to each provenance-preserving chunk."""
    return [{**chunk, "embedding": embed_text(chunk["text"])} for chunk in chunks]
