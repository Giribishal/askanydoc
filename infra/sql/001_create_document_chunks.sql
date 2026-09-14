CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_uri TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    source_type TEXT NOT NULL,
    object_key TEXT NOT NULL,
    location JSONB NOT NULL,
    page_number INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1024) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx
    ON document_chunks (document_id);

CREATE INDEX IF NOT EXISTS document_chunks_embedding_cosine_idx
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops);
