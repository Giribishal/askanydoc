"""Convert vectors to PostgreSQL pgvector's text input representation."""

from __future__ import annotations


def vector_literal(embedding: list[float]) -> str:
    """Serialize numeric dimensions without interpolating SQL."""
    return "[" + ",".join(str(number) for number in embedding) + "]"
