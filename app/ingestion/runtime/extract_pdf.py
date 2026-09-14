"""Read a local PDF into page records with traceable source information."""

import argparse
import hashlib
import json
import sys
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PyPdfError


def extract_pages_from_bytes(
    pdf_bytes: bytes,
    source_name: str,
    source_uri: str,
) -> list[dict]:
    """Return page records from PDF bytes downloaded from any source adapter."""
    # Hash the same bytes that PyPDF reads so this exact document version is traceable.
    source_hash = hashlib.sha256(pdf_bytes).hexdigest()

    # PdfReader parses the PDF; BytesIO gives it an in-memory file to read.
    reader = PdfReader(BytesIO(pdf_bytes))
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported by this first version.")
    if not reader.pages:
        raise ValueError("The PDF contains no pages.")

    records = []
    # enumerate pairs each page with a number; start=1 matches a PDF viewer's position.
    for page_number, page in enumerate(reader.pages, start=1):
        # extract_text is a method: it reads text stored on this page, without OCR.
        text = page.extract_text() or ""
        # Keep line boundaries and internal spacing; remove only trailing whitespace.
        text = "\n".join(line.rstrip() for line in text.splitlines()).strip()
        status = "empty" if not text else "near_empty" if len(text) < 50 else "extracted"

        # This dictionary keeps the content and its provenance together.
        records.append({
            "source_name": source_name,
            "source_uri": source_uri,
            "source_sha256": source_hash,
            "page_number": page_number,
            "character_count": len(text),
            "status": status,
            "text": text,
        })
    return records


def extract_pages(pdf_path: Path, source_url: str | None = None) -> list[dict]:
    """Read a local PDF and delegate extraction to the shared byte-based function."""
    # Read once, then use the same production extraction path as an S3 download.
    pdf_bytes = pdf_path.read_bytes()
    return extract_pages_from_bytes(
        pdf_bytes=pdf_bytes,
        source_name=pdf_path.name,
        source_uri=source_url or pdf_path.resolve().as_uri(),
    )


def main() -> int:
    # argparse turns command-line arguments into named values.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("--source-url", help="Public source URL to retain for citations.")
    parser.add_argument("--output", type=Path, required=True, help="New JSON file, normally under tmp/.")
    args = parser.parse_args()

    try:
        records = extract_pages(args.pdf_path, args.source_url)
        # Exclusive mode refuses to overwrite an existing file, including the source PDF.
        # json.dump serializes our Python records into inspectable UTF-8 JSON.
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(records, output, ensure_ascii=False, indent=2)
            output.write("\n")
    except (OSError, PyPdfError, ValueError) as error:
        print(f"Extraction failed: {error}", file=sys.stderr)
        return 1

    non_empty = sum(record["status"] != "empty" for record in records)
    print(f"Source: {args.pdf_path.name}")
    print(f"Pages: {len(records)}; non-empty: {non_empty}; output: {args.output}")
    # Summaries show status without printing the complete document into logs.
    for record in records:
        print(f"Page {record['page_number']}: {record['character_count']} characters ({record['status']})")
    needs_review = [record["page_number"] for record in records if record["status"] != "extracted"]
    if needs_review:
        print(f"Review required: empty/near-empty pages {needs_review}. No OCR was attempted.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    # This guard runs the command only when this file is executed directly.
    raise SystemExit(main())
