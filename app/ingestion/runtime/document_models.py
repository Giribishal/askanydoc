"""Common text and provenance contracts for all AskAnyDoc extractors."""

from __future__ import annotations

import hashlib
from typing import Any, TypedDict


class NormalizedRecord(TypedDict):
    document_id: str
    bucket_name: str
    source_name: str
    source_type: str
    source_uri: str
    source_sha256: str
    object_key: str
    text: str
    location: dict[str, Any]


class ChunkRecord(NormalizedRecord):
    chunk_id: str
    chunk_index: int


def make_chunk_id(document_id: str, chunk_index: int) -> str:
    """Return a stable ID so repeated ingestion can replace the same chunk."""
    value = f"{document_id}:{chunk_index}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
