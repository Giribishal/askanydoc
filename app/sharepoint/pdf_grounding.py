"""Bounded, in-memory PDF grounding for delegated SharePoint files."""

from __future__ import annotations

import re
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from .sharepoint_source import SharePointError


_WORD = re.compile(r"[a-z0-9][a-z0-9-]{2,}")
_STOP_WORDS = {
    "and", "are", "for", "from", "how", "into", "main", "that", "the",
    "their", "this", "using", "what", "when", "where", "which", "with",
}


def _query_terms(query: str) -> set[str]:
    return {word for word in _WORD.findall(query.lower()) if word not in _STOP_WORDS}


def rank_page_texts(
    pages: list[tuple[int, str]],
    query: str,
    max_pages: int,
    max_characters: int,
) -> list[dict[str, object]]:
    """Select useful pages without another model or embedding request."""
    terms = _query_terms(query)
    ranked: list[tuple[int, int, str]] = []
    for page_number, text in pages:
        cleaned = text.strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        score = sum(min(lowered.count(term), 3) for term in terms)
        ranked.append((score, page_number, cleaned))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [
        {
            "page_number": page_number,
            "text": text[:max_characters],
            "lexical_score": score,
        }
        for score, page_number, text in ranked[:max_pages]
    ]


def extract_relevant_pdf_pages(
    pdf_bytes: bytes,
    query: str,
    *,
    max_document_pages: int,
    max_evidence_pages: int,
    max_excerpt_characters: int,
) -> list[dict[str, object]]:
    """Extract and rank a bounded number of text-bearing PDF pages."""
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        if reader.is_encrypted:
            raise SharePointError("unsupported_document", "Encrypted SharePoint PDFs are not supported")
        if len(reader.pages) > max_document_pages:
            raise SharePointError("document_too_large", "The SharePoint PDF exceeds the page limit")
        pages = [
            (index, page.extract_text() or "")
            for index, page in enumerate(reader.pages, start=1)
        ]
    except SharePointError:
        raise
    except (PyPdfError, ValueError) as error:
        raise SharePointError("extraction_failed", "The SharePoint PDF could not be extracted") from error

    return rank_page_texts(
        pages,
        query,
        max_pages=max_evidence_pages,
        max_characters=max_excerpt_characters,
    )
