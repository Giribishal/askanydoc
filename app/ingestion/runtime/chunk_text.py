"""Create searchable chunks while preserving document and page provenance."""

from __future__ import annotations

from typing import Any

from document_models import make_chunk_id


def chunk_pages(
    page_records: list[dict[str, Any]],
    document_id: str,
    source_type: str,
    object_key: str,
    bucket_name: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[dict[str, Any]]:
    """Split page text at word boundaries and retain source metadata."""
    if chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("Chunk size must be positive and larger than the overlap.")

    chunks: list[dict[str, Any]] = []
    chunk_index = 0

    for page in page_records:
        text = page["text"]
        start = 0
        chunk_number_on_page = 1

        while start < len(text):
            requested_end = min(start + chunk_size, len(text))
            end = requested_end

            # Prefer ending at a complete word instead of cutting through one.
            if requested_end < len(text):
                boundary = text.rfind(" ", start, requested_end)
                if boundary > start:
                    end = boundary

            chunk_text = text[start:end].strip()
            if chunk_text:
                location = dict(page.get("location", {"page_number": page["page_number"]}))
                location["chunk_number_in_record"] = chunk_number_on_page
                chunks.append({
                    "document_id": document_id,
                    "bucket_name": bucket_name,
                    "source_name": page["source_name"],
                    "source_type": source_type,
                    "source_uri": page["source_uri"],
                    "source_sha256": page["source_sha256"],
                    "object_key": object_key,
                    "text": chunk_text,
                    "location": location,
                    "chunk_id": make_chunk_id(document_id, chunk_index),
                    "chunk_index": chunk_index,
                })
                chunk_index += 1

            if end >= len(text):
                break

            candidate_start = max(end - chunk_overlap, start + 1)
            next_space = text.find(" ", candidate_start, end)
            start = next_space + 1 if next_space != -1 else candidate_start
            chunk_number_on_page += 1

    return chunks
