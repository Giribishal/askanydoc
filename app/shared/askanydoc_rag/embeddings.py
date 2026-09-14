"""Create compatible Titan embeddings for documents and questions."""

from __future__ import annotations

import json
import os

from .aws import aws_client


bedrock_client = aws_client("bedrock-runtime")
EMBEDDING_DIMENSIONS = 1024


def embed_text(text: str) -> list[float]:
    """Return one normalized Titan Text Embeddings V2 vector."""
    response = bedrock_client.invoke_model(
        modelId=os.environ["EMBEDDING_MODEL_ID"],
        body=json.dumps({
            "inputText": text,
            "dimensions": EMBEDDING_DIMENSIONS,
            "normalize": True,
        }),
    )
    payload = json.loads(response["body"].read())
    embedding = payload["embedding"]
    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Titan returned {len(embedding)} dimensions; expected {EMBEDDING_DIMENSIONS}."
        )
    return embedding
