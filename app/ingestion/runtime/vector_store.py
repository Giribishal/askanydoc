"""Replace one document's chunks atomically through the RDS Data API."""

from __future__ import annotations

import json
import os
from typing import Any

from askanydoc_rag.aws import aws_client
from askanydoc_rag.data_api import call_with_database_resume_retry
from askanydoc_rag.vectors import vector_literal


data_client = aws_client("rds-data")
DATABASE_INSERT_BATCH_SIZE = 25

INSERT_CHUNK_SQL = """
INSERT INTO document_chunks (
    chunk_id,
    document_id,
    source_name,
    source_uri,
    source_sha256,
    source_type,
    object_key,
    location,
    page_number,
    chunk_index,
    chunk_text,
    embedding
)
VALUES (
    :chunk_id,
    :document_id,
    :source_name,
    :source_uri,
    :source_sha256,
    :source_type,
    :object_key,
    CAST(:location AS jsonb),
    :page_number,
    :chunk_index,
    :chunk_text,
    CAST(:embedding AS vector)
)
"""


def _database_arguments() -> dict[str, str]:
    """Return the shared identifiers required by every Data API request."""
    return {
        "resourceArn": os.environ["VECTOR_DATABASE_ARN"],
        "secretArn": os.environ["VECTOR_DATABASE_SECRET_ARN"],
        "database": os.environ["VECTOR_DATABASE_NAME"],
    }


def _string_parameter(name: str, value: str) -> dict[str, Any]:
    return {"name": name, "value": {"stringValue": value}}


def _long_parameter(name: str, value: int) -> dict[str, Any]:
    return {"name": name, "value": {"longValue": value}}


def _chunk_parameters(chunk: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert one embedded chunk into typed Data API parameters."""
    return [
        _string_parameter("chunk_id", chunk["chunk_id"]),
        _string_parameter("document_id", chunk["document_id"]),
        _string_parameter("source_name", chunk["source_name"]),
        _string_parameter("source_uri", chunk["source_uri"]),
        _string_parameter("source_sha256", chunk["source_sha256"]),
        _string_parameter("source_type", chunk["source_type"]),
        _string_parameter("object_key", chunk["object_key"]),
        _string_parameter("location", json.dumps(chunk["location"])),
        _long_parameter("page_number", chunk["location"].get("page_number", 1)),
        _long_parameter("chunk_index", chunk["chunk_index"]),
        _string_parameter("chunk_text", chunk["text"]),
        _string_parameter("embedding", vector_literal(chunk["embedding"])),
    ]


def replace_document_chunks(
    document_id: str,
    embedded_chunks: list[dict[str, Any]],
) -> None:
    """Delete stale chunks and insert the current document version in one transaction."""
    arguments = _database_arguments()
    transaction = call_with_database_resume_retry(
        data_client.begin_transaction,
        **arguments,
    )
    transaction_id = transaction["transactionId"]

    try:
        data_client.execute_statement(
            **arguments,
            transactionId=transaction_id,
            sql="DELETE FROM document_chunks WHERE document_id = :document_id",
            parameters=[_string_parameter("document_id", document_id)],
        )
        for start in range(0, len(embedded_chunks), DATABASE_INSERT_BATCH_SIZE):
            chunk_batch = embedded_chunks[start:start + DATABASE_INSERT_BATCH_SIZE]
            data_client.batch_execute_statement(
                **arguments,
                transactionId=transaction_id,
                sql=INSERT_CHUNK_SQL,
                parameterSets=[_chunk_parameters(chunk) for chunk in chunk_batch],
            )
        data_client.commit_transaction(
            resourceArn=arguments["resourceArn"],
            secretArn=arguments["secretArn"],
            transactionId=transaction_id,
        )
    except Exception:
        data_client.rollback_transaction(
            resourceArn=arguments["resourceArn"],
            secretArn=arguments["secretArn"],
            transactionId=transaction_id,
        )
        raise
