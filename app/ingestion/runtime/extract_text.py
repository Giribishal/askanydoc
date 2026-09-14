"""Extract normalized text records from DOCX, TXT, and Markdown documents."""

from __future__ import annotations

import hashlib
from io import BytesIO
import re

from docx import Document


def _record(
    document_bytes: bytes,
    source_name: str,
    source_uri: str,
    text: str,
    location: dict,
) -> dict:
    """Return one normalized record with format-appropriate provenance."""
    normalized_text = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    return {
        "source_name": source_name,
        "source_uri": source_uri,
        "source_sha256": hashlib.sha256(document_bytes).hexdigest(),
        "page_number": 1,
        "location": location,
        "text": normalized_text,
        "character_count": len(normalized_text),
        "status": "extracted" if normalized_text else "empty",
    }


def extract_docx_from_bytes(
    document_bytes: bytes,
    source_name: str,
    source_uri: str,
) -> list[dict]:
    """Extract Word sections and retain their nearest heading."""
    document = Document(BytesIO(document_bytes))
    sections: list[tuple[str | None, list[str]]] = []
    heading: str | None = None
    blocks: list[str] = []
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        if paragraph.style and paragraph.style.name.lower().startswith("heading"):
            if blocks:
                sections.append((heading, blocks))
            heading, blocks = text, []
        else:
            blocks.append(text)
    for table in document.tables:
        for row in table.rows:
            cell_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if cell_text:
                blocks.append(cell_text)
    if blocks or not sections:
        sections.append((heading, blocks))
    return [
        _record(
            document_bytes,
            source_name,
            source_uri,
            "\n".join(section_blocks),
            {"section_index": index, "heading": section_heading},
        )
        for index, (section_heading, section_blocks) in enumerate(sections, start=1)
    ]


def extract_utf8_text_from_bytes(
    document_bytes: bytes,
    source_name: str,
    source_uri: str,
) -> list[dict]:
    """Decode UTF-8 and preserve Markdown headings or plain-text line ranges."""
    text = document_bytes.decode("utf-8-sig")
    if source_name.lower().endswith(".md"):
        records: list[dict] = []
        heading_path: list[str] = []
        section_lines: list[str] = []

        def append_section() -> None:
            if section_lines or not records:
                records.append(_record(
                    document_bytes,
                    source_name,
                    source_uri,
                    "\n".join(section_lines),
                    {"heading_path": list(heading_path)},
                ))

        for line in text.splitlines():
            match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
            if match:
                append_section()
                level = len(match.group(1))
                heading_path = heading_path[:level - 1] + [match.group(2)]
                section_lines = []
            else:
                section_lines.append(line)
        append_section()
        return records

    return [_record(
        document_bytes,
        source_name,
        source_uri,
        text,
        {"line_start": 1, "line_end": max(1, len(text.splitlines()))},
    )]
