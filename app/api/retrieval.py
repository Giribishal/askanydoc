"""Embed a question and retrieve citation-ready evidence from pgvector."""

from __future__ import annotations

import json
import os
from typing import Any

from askanydoc_rag.aws import aws_client
from askanydoc_rag.data_api import call_with_database_resume_retry
from askanydoc_rag.embeddings import embed_text
from askanydoc_rag.vectors import vector_literal


data_client = aws_client("rds-data")

RETRIEVAL_SQL = """
SELECT
    chunk_id,
    chunk_text,
    source_name,
    source_type,
    source_uri,
    object_key,
    location::text AS location_json,
    1 - (embedding <=> CAST(:question_embedding AS vector)) AS similarity
FROM document_chunks
WHERE 1 - (embedding <=> CAST(:question_embedding AS vector)) >= :minimum_similarity
ORDER BY embedding <=> CAST(:question_embedding AS vector)
LIMIT :result_limit
"""


def _database_arguments() -> dict[str, str]:
    return {
        "resourceArn": os.environ["VECTOR_DATABASE_ARN"],
        "secretArn": os.environ["VECTOR_DATABASE_SECRET_ARN"],
        "database": os.environ["VECTOR_DATABASE_NAME"],
    }


def retrieve_evidence(question: str) -> list[dict[str, Any]]:
    """Return nearest chunks whose cosine similarity clears the configured gate."""
    embedding = embed_text(question)
    minimum_similarity = float(os.environ.get("MINIMUM_RETRIEVAL_SIMILARITY", "0.35"))
    result_limit = int(os.environ.get("RETRIEVAL_RESULT_LIMIT", "5"))
    response = call_with_database_resume_retry(
        data_client.execute_statement,
        **_database_arguments(),
        sql=RETRIEVAL_SQL,
        parameters=[
            {"name": "question_embedding", "value": {"stringValue": vector_literal(embedding)}},
            {"name": "minimum_similarity", "value": {"doubleValue": minimum_similarity}},
            {"name": "result_limit", "value": {"longValue": result_limit}},
        ],
        formatRecordsAs="JSON",
    )
    records = json.loads(response.get("formattedRecords", "[]"))
    for record in records:
        record["location"] = json.loads(record.pop("location_json"))
    return records
