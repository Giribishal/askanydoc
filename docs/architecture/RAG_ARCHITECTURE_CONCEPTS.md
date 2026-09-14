# AskAnyDoc RAG Architecture Concepts

## The architecture in one sentence

AskAnyDoc keeps the original supported document in S3, uses one Ingestion Lambda to select a format-specific extractor, normalizes the extracted text and provenance, then reuses one chunking, Titan embedding, and Aurora PostgreSQL with pgvector pipeline.

## Version 1 scope

| Format | v1 | Primary location metadata |
|---|---:|---|
| PDF `.pdf` | Yes | Physical PDF page number |
| Word `.docx` | Yes | Heading or section; page only when reliably available |
| Plain text `.txt` | Yes | Line range and chunk position |
| Markdown `.md` | Yes | Heading or section |
| Excel `.xlsx/.xls` and CSV | No | Later, with structure-aware extraction |
| PowerPoint `.pptx` | No | Later |
| Images and scanned-document OCR | No | Later OCR/document-understanding path |
| Any other format | No | Ignore safely and log as unsupported |

DOCX files can display page numbers in Word, but page boundaries depend on layout, fonts, and rendering. The native document structure reliably exposes paragraphs, headings, tables, and sections, not universal page positions. AskAnyDoc therefore cites DOCX headings or sections first.

## Two separate flows

```text
INGESTION - runs after a supported document is uploaded

.pdf / .docx / .txt / .md
             |
             v
        Private S3 bucket
             |
       ObjectCreated event
             |
             v
       INGESTION LAMBDA
       1. Decode bucket and object key
       2. Allowlist the file extension
       3. Select the matching extractor
       4. Normalize text + provenance
       5. Chunk normalized records
       6. Ask Titan to embed each chunk
       7. Store text + vector + metadata
             |
             v
    Aurora PostgreSQL + pgvector
```

```text
HYBRID ASSISTANT - runs for each message

User + recent history -> React -> Answer Lambda -> Claude
                                                /      \
                              normal response <-        -> requests organisation search
                                                               |
                                                    Titan question embedding
                                                               |
                                                    pgvector evidence search
                                                               |
                                                    Claude final response
                                                               |
User <- React <- source mode + answer + validated citations <-+
```

Lambda coordinates. Claude decides whether the organisation-search tool is needed. Titan creates vectors. Aurora stores records. pgvector performs similarity search. Claude writes the response, while application code validates evidence numbers and builds citations from stored provenance.

## One ingestion Lambda with four extractor adapters

The Lambda trigger receives every object created under `uploads/`. The handler owns the explicit allowlist:

```text
object key extension
        |
        +-- .pdf  -> PDF extractor
        +-- .docx -> DOCX extractor
        +-- .txt  -> TXT extractor
        +-- .md   -> Markdown extractor
        +-- other -> ignore + structured log
```

S3 notification filters cannot conveniently express four suffixes for the same Lambda without repeated configuration. A single `uploads/` prefix trigger plus validation in the handler keeps the routing rule visible and testable.

The format-specific part ends after extraction:

```text
format-specific extractor
          |
          v
normalized text + provenance records
          |
          v
shared chunking -> Titan embeddings -> Aurora/pgvector
```

The document file itself is never sent to Titan. Titan receives text only.

## Common normalized record

Every extractor returns the same outer shape:

```json
{
  "document_id": "stable source identity",
  "source_name": "employee-handbook.docx",
  "source_type": "docx",
  "source_uri": "s3://askanydoc-documents-prod-apse2/uploads/employee-handbook.docx",
  "object_key": "uploads/employee-handbook.docx",
  "text": "Employees receive annual leave...",
  "location": {
    "heading": "Annual Leave",
    "section_index": 7
  }
}
```

| Field | Purpose |
|---|---|
| `document_id` | Stable identity for replacement and deduplication |
| `source_name` | Human-readable citation name |
| `source_type` | `pdf`, `docx`, `txt`, or `md` |
| `source_uri` | Original source location, initially an S3 URI |
| `object_key` | Exact S3 object key |
| `text` | Extracted text for shared chunking |
| `location` | Format-appropriate provenance object |

The `location` object varies by format:

```json
PDF:  {"page_number": 12}
DOCX: {"heading": "Annual Leave", "section_index": 7}
MD:   {"heading": "Authentication", "heading_path": ["Architecture", "Authentication"]}
TXT:  {"line_start": 120, "line_end": 145}
```

If a DOCX conversion later provides a verified page position, it may be recorded as optional metadata. It must not replace heading/section provenance or be invented from paragraph order.

## Common chunk record

Chunking adds a stable chunk identity and position without removing extractor provenance:

```json
{
  "document_id": "...",
  "chunk_id": "stable hash of document_id + chunk_index",
  "chunk_index": 3,
  "source_name": "architecture.md",
  "source_type": "md",
  "source_uri": "s3://bucket/uploads/architecture.md",
  "object_key": "uploads/architecture.md",
  "text": "The Ingestion Lambda selects an extractor...",
  "location": {
    "heading": "Ingestion",
    "heading_path": ["Architecture", "Ingestion"]
  }
}
```

Aurora stores the chunk text, embedding vector, and all citation metadata together. Retrieval must return readable text and provenance, not vectors alone.

## Provenance rules

1. Create `document_id` as soon as the S3 event is decoded.
2. Keep `source_name`, `source_type`, `source_uri`, and `object_key` on every normalized record.
3. Never discard `location` during chunking.
4. Add a deterministic `chunk_id` to every chunk.
5. Build citations from retrieved metadata, never from model guesses.
6. Use document version/hash plus stable identifiers so reprocessing does not create uncontrolled duplicates.

Example citations:

```text
PDF  - Security Policy.pdf, page 12
DOCX - Employee Handbook.docx, section "Annual Leave"
MD   - architecture.md, heading "Authentication"
TXT  - meeting-notes.txt, lines 120-145
```

## Incremental implementation plan

### Milestone 1 - prove the event and routing boundary

```text
Upload under uploads/
  -> S3 invokes Ingestion Lambda
  -> Lambda decodes the key
  -> supported extension is routed
  -> unsupported extension is ignored and logged
```

Acceptance checks:

- `.pdf`, `.docx`, `.txt`, and `.md` route case-insensitively.
- URL-encoded S3 keys are decoded.
- the response/log contains source identity and selected extractor;
- `.xlsx`, `.csv`, `.pptx`, images, and other files do not enter extraction;
- no extraction, embedding, or database write is claimed yet.

### Milestone 2 - wire extractors one at a time

1. Retain and verify the existing PDF extractor.
2. Add DOCX extraction using heading/section provenance.
3. Add TXT extraction with line ranges.
4. Add Markdown extraction with heading paths.
5. Contract-test that all four produce normalized records.

### Milestone 3 - connect the existing shared RAG pipeline

```text
normalized records
  -> shared chunking
  -> Titan Text Embeddings V2
  -> Aurora PostgreSQL + pgvector
```

This ordering preserves the existing learning plan: prove one boundary, inspect its output, then connect the next specialist.

## Responsibility map

| Component | Responsibility | Does not do |
|---|---|---|
| S3 | Stores original documents and emits upload events | Extract text |
| Ingestion Lambda | Validates type and coordinates the sequence | Create embeddings itself |
| Format extractor | Produces clean text and location metadata | Search vectors |
| Shared chunker | Splits text while preserving provenance | Interpret file formats |
| Titan Embeddings | Converts chunk or question text to vectors | Answer questions |
| Aurora PostgreSQL | Stores text, vectors, and metadata | Generate prose |
| pgvector | Performs nearest-neighbour search | Choose or invoke extractors |
| Answer Lambda | Validates requests, runs Claude's approved tool calls, and enforces citation/source contracts | Grant Claude AWS credentials |
| Claude | Converses normally and decides when organisation tools are needed | Search S3 or Aurora directly |

## Local-to-AWS mapping

```text
Current local learning slice
PDF -> PDF extractor -> records -> chunks -> local embeddings/store

Target AWS ingestion
S3 event -> router -> selected extractor -> normalized records
         -> shared chunks -> Titan -> Aurora/pgvector
```

The existing PDF exercise remains useful as the first extractor proof. It is no longer the architectural boundary.

## Quick diagnosis

**An uploaded file does nothing**

Check that the object key begins with `uploads/`, the S3 notification exists, and S3 has permission to invoke the Ingestion Lambda.

**An unsupported file invoked Lambda**

That is expected for the broad prefix trigger. The handler must return `ignored` and must not extract, embed, or store it.

**A DOCX citation claims a page that changes in Word**

Use heading/section provenance. Keep page information only when a rendering process provides a reliable, verified page position.

**A scanned PDF produces no text**

The v1 PDF extractor reads embedded text only. OCR and image understanding are explicitly later work.

**Aurora returns vectors but no evidence**

Store and select chunk text plus provenance in the same rows as the vectors.

## Thirty-second refresher

```text
UPLOAD
PDF / DOCX / TXT / MD -> S3 -> Ingestion Lambda -> matching extractor
-> normalized text + provenance -> chunks -> Titan -> Aurora/pgvector

ASSISTANT
Message + recent history -> Answer Lambda -> Claude
-> optional organisation tool -> Titan -> pgvector -> evidence
-> Claude response -> application-validated citations
```

The durable rule is simple: file format changes extraction; everything after normalized text and provenance is shared.
