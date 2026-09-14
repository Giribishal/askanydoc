"""Turn supported AskAnyDoc S3 uploads into searchable vector chunks."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import unquote_plus

from askanydoc_rag.aws import aws_client
from chunk_text import chunk_pages
from embed_chunks import embed_chunks
from extract_pdf import extract_pages_from_bytes
from extract_text import extract_docx_from_bytes, extract_utf8_text_from_bytes
from vector_store import replace_document_chunks


# Create the AWS client once so warm Lambda invocations can reuse it.
s3_client = aws_client("s3")
MAX_DOCUMENT_BYTES = int(os.environ.get("MAX_DOCUMENT_BYTES", str(10 * 1024 * 1024)))
MAX_DOCUMENT_CHUNKS = int(os.environ.get("MAX_DOCUMENT_CHUNKS", "100"))


SUPPORTED_FORMATS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
    ".md": "md",
}

EXTRACTOR_ROUTES = {
    "pdf": "extract_pdf",
    "docx": "extract_docx",
    "txt": "extract_txt",
    "md": "extract_markdown",
}


def detect_source_type(object_key: str) -> str | None:
    """Return the supported document format, or None for an unsupported key."""
    return SUPPORTED_FORMATS.get(PurePosixPath(object_key).suffix.lower())


def build_source_envelope(
    bucket: str,
    object_key: str,
    source_type: str,
    version_id: str | None = None,
) -> dict[str, str]:
    """Create stable source identity and provenance before extraction begins."""
    source_uri = f"s3://{bucket}/{object_key}"
    document_id = hashlib.sha256(source_uri.encode("utf-8")).hexdigest()
    source = {
        "document_id": document_id,
        "bucket_name": bucket,
        "source_name": PurePosixPath(object_key).name,
        "source_type": source_type,
        "source_uri": source_uri,
        "object_key": object_key,
    }
    if version_id:
        source["version_id"] = version_id
    return source


def route_record(record: dict[str, Any]) -> dict[str, Any]:
    """Validate one S3 event record and select its future extractor adapter."""
    bucket = record["s3"]["bucket"]["name"]
    object_key = unquote_plus(record["s3"]["object"]["key"])
    object_details = record["s3"]["object"]
    object_size = object_details.get("size")
    version_id = object_details.get("versionId")
    source_type = detect_source_type(object_key)

    if source_type is None:
        return {
            "status": "ignored",
            "reason": "unsupported_file_type",
            "source_uri": f"s3://{bucket}/{object_key}",
            "object_key": object_key,
        }

    if object_size is not None and object_size > MAX_DOCUMENT_BYTES:
        return {
            "status": "ignored",
            "reason": "document_too_large",
            "source_uri": f"s3://{bucket}/{object_key}",
            "object_key": object_key,
            "size_bytes": object_size,
            "maximum_size_bytes": MAX_DOCUMENT_BYTES,
        }

    source = build_source_envelope(bucket, object_key, source_type, version_id)
    return {
        "status": "routed",
        "extractor": EXTRACTOR_ROUTES[source_type],
        **source,
    }


def extract_record(route: dict[str, str]) -> dict[str, Any]:
    """Download, extract, chunk, embed, and store one supported document."""
    # The event contains the address of the object, not the document bytes themselves.
    get_object_arguments = {
        "Bucket": route["bucket_name"],
        "Key": route["object_key"],
    }
    if route.get("version_id"):
        get_object_arguments["VersionId"] = route["version_id"]
    object_response = s3_client.get_object(**get_object_arguments)
    content_length = object_response.get("ContentLength")
    if content_length is not None and content_length > MAX_DOCUMENT_BYTES:
        raise ValueError(
            f"Document is {content_length} bytes; maximum is {MAX_DOCUMENT_BYTES} bytes."
        )
    document_bytes = object_response["Body"].read(MAX_DOCUMENT_BYTES + 1)
    if len(document_bytes) > MAX_DOCUMENT_BYTES:
        raise ValueError(
            f"Document exceeds the {MAX_DOCUMENT_BYTES}-byte ingestion limit."
        )

    if route["source_type"] == "pdf":
        page_records = extract_pages_from_bytes(
            pdf_bytes=document_bytes,
            source_name=route["source_name"],
            source_uri=route["source_uri"],
        )
    elif route["source_type"] == "docx":
        page_records = extract_docx_from_bytes(
            document_bytes, route["source_name"], route["source_uri"]
        )
    else:
        page_records = extract_utf8_text_from_bytes(
            document_bytes, route["source_name"], route["source_uri"]
        )
    chunks = chunk_pages(
        page_records=page_records,
        document_id=route["document_id"],
        source_type=route["source_type"],
        object_key=route["object_key"],
        bucket_name=route["bucket_name"],
    )
    if len(chunks) > MAX_DOCUMENT_CHUNKS:
        raise ValueError(
            f"Document created {len(chunks)} chunks; maximum is {MAX_DOCUMENT_CHUNKS}."
        )
    embedded_chunks = embed_chunks(chunks)
    replace_document_chunks(route["document_id"], embedded_chunks)
    non_empty_pages = sum(page["status"] != "empty" for page in page_records)

    # Do not return or print full document text because Lambda logs are not document storage.
    return {
        **route,
        "status": "extracted",
        "page_count": len(page_records),
        "non_empty_page_count": non_empty_pages,
        "character_count": sum(page["character_count"] for page in page_records),
        "chunk_count": len(embedded_chunks),
        "source_sha256": page_records[0]["source_sha256"],
    }


def process_record(record: dict[str, Any]) -> dict[str, Any]:
    """Route one S3 record and run the extractor implemented in this milestone."""
    route = route_record(record)
    if route["status"] != "routed":
        return route
    return extract_record(route)


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Receive S3 ObjectCreated events and report deterministic routing decisions."""
    records = event.get("Records", [])
    results: list[dict[str, Any]] = []

    for record in records:
        if record.get("eventSource") != "aws:s3":
            results.append({"status": "ignored", "reason": "not_an_s3_record"})
            continue

        try:
            results.append(process_record(record))
        except (KeyError, TypeError) as error:
            results.append({"status": "invalid", "reason": f"malformed_s3_record: {error}"})

    response = {
        "milestone": "s3_multi_format_to_aurora_vector_ingestion",
        "record_count": len(records),
        "results": results,
    }
    print(json.dumps(response, separators=(",", ":")))
    return response
