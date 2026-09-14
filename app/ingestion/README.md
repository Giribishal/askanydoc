# Ingestion code map

This area keeps the deployable AWS ingestion code separate from the small scripts used to learn and inspect each RAG stage.

## `runtime/`

Production code intended for the ingestion Lambda container:

- `ingestion_lambda_handler.py` receives S3 events and routes supported documents.
- `extract_pdf.py` contains the first PDF page extractor.
- `document_models.py` defines the shared document and chunk record shapes.
- `requirements.txt` lists packages installed in the Lambda image.
- `Dockerfile` describes how to build that image.

## `learning/`

Local, step-by-step scripts that preserve the path from page extraction through chunking, embeddings, Chroma storage, and retrieval. They are useful evidence and are not copied into the Lambda image.

Install their recorded dependencies from the repository root with:

```powershell
.\.venv\Scripts\python.exe -m pip install -r app/ingestion/learning/requirements.txt
```

## `tests/`

Local automated checks for the ingestion behavior. Run them from the repository root with:

```powershell
.\.venv\Scripts\python.exe -m unittest -v app/ingestion/tests/test_ingestion_lambda_handler.py
```

