# Multi-format ingestion milestone

## Current result

The first AWS milestone proves the permanent ingestion boundary using an ECR container image, without pretending the extractors, embeddings, or database writes are already connected.

```text
uploads/* object created
  -> S3 invokes askanydoc-ingestion-prod
  -> handler decodes bucket and key
  -> .pdf / .docx / .txt / .md routes to a named extractor
  -> any other extension is ignored and logged
```

## Test locally

From the repository root:

```powershell
python -m unittest -v app/ingestion/tests/test_ingestion_lambda_handler.py
```

The tests prove case-insensitive detection, URL-decoded S3 object keys, stable source metadata, DOCX routing, and clean rejection of an `.xlsx` file.

## Deploy and prove in AWS

1. Run Terraform formatting and validation.
2. Apply the infrastructure changes.
3. Upload one small file of each supported type under `uploads/` in the private document bucket.
4. Upload one unsupported file such as `uploads/example.xlsx`.
5. Inspect the `askanydoc-ingestion-prod` CloudWatch logs.

Expected supported result:

```json
{
  "status": "routed",
  "extractor": "extract_markdown",
  "source_type": "md",
  "source_name": "architecture.md",
  "source_uri": "s3://bucket/uploads/architecture.md",
  "object_key": "uploads/architecture.md",
  "document_id": "stable sha256 value"
}
```

Expected unsupported result:

```json
{
  "status": "ignored",
  "reason": "unsupported_file_type"
}
```

## Next implementation slice

Connect extractors one at a time behind the proven routes:

```text
PDF  -> page records
DOCX -> heading/section records
MD   -> heading-path records
TXT  -> line-range records
```

Every adapter must produce the shared record fields defined in `app/ingestion/runtime/document_models.py`. Then the existing learning plan continues with shared chunking, Titan Text Embeddings V2, and Aurora PostgreSQL/pgvector.
