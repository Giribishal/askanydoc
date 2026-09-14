# F1: Read one PDF and preserve its source

This remains the first extractor learning slice. It proves PDF text and page provenance inside the wider v1 architecture: PDF, DOCX, TXT, and Markdown each normalize into common text + provenance records before shared chunking, embeddings, and storage.

Status: First implementation tested; Bishal's code review, page comparison and understanding are pending. No commit made.

## Run locally

From the AskAnyDoc repository root, with Python installed:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r app/ingestion/runtime/requirements.txt
New-Item -ItemType Directory -Force data/raw, tmp | Out-Null
$sourceUrl = 'https://www.cyber.gov.au/sites/default/files/2025-03/Essential%20Eight%20maturity%20model%20%28November%202023%29.pdf'
Invoke-WebRequest -Uri $sourceUrl -OutFile data/raw/essential-eight-maturity-model.pdf
.\.venv\Scripts\python.exe app/ingestion/runtime/extract_pdf.py data/raw/essential-eight-maturity-model.pdf --source-url $sourceUrl --output tmp/essential-eight-pages.json
```

Use a new output filename on subsequent runs. The command deliberately refuses to overwrite existing files. The output directory must already exist.

## Meaning of one record

- `source_name`: the local filename.
- `source_uri`: the supplied official URL (otherwise the local file URI).
- `source_sha256`: a fingerprint of the exact PDF bytes, so later revisions can be distinguished.
- `page_number`: physical PDF position, starting at 1; not necessarily a printed page label in other PDFs.
- `character_count`, `status`, `text`: the extracted content and a basic review signal.

Source and page information are provenance: they let us trace text back to its evidence. A hash identifies bytes, not whether a source is trustworthy.

## Source and verification, 2026-09-06

Official landing page: https://www.cyber.gov.au/business-government/asds-cyber-security-frameworks/essential-eight/essential-eight-maturity-model

Title: Essential Eight maturity model. Document states last updated November 2023. Downloaded 2026-09-06 from the official attachment linked above.

SHA-256: `43018b0250b717bcffac4e7fe173d0e936ebf97e3a01c7d176aa14e3f20489f4`

Tested initially with the Codex bundled Python 3.12.14 and pypdf 6.10.0. Match API documentation: https://pypdf.readthedocs.io/en/6.10.0/user/extract-text.html

Keep the available, tested pypdf version for this isolated first slice; the stable documentation currently reports 6.17.0. No newer API is required by this implementation. DOCX, TXT, and Markdown extractors follow incrementally. Excel/CSV, PowerPoint, images, and OCR are deferred.

- Official PDF: 34 pages. Extractor: 34 records, all non-empty.
- Page numbers verified to be 1 through 34, sharing one source hash.
- Missing path and invalid PDF return exit code 1 with an explanation.
- Blank-page fixture produces an explicit empty record and exit code 2 (review required).
- Exit code 0 means extraction ran without empty/near-empty pages; it does not certify text quality.

## Remaining inspection

Compare pages 1, 17 and 34 with the original, including table structure on page 17. Bishal has not yet performed this review. Text extraction keeps words and page boundaries but can lose bolding, columns, table relationships and reading order. It does not perform OCR. The under-50-character warning is only a heuristic; a page with a header and a scanned image could escape it.

Downloaded PDF belongs under ignored `data/raw/`; generated JSON belongs under ignored `tmp/`. This is local extraction only. It does not retrieve passages or answer questions.

Reading: assigned Chapter 6 RAG/retrieval sections remain unconfirmed. Discuss how document preparation affects later retrieval as Bishal reads; do not substitute a chapter summary.

Next small learning step: inspect the first record and trace its source, page number and text through `extract_pages`. Complete the human checks before closing F1 or committing deliberately.
