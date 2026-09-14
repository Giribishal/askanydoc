import json
from pathlib import Path

import chromadb


# Load the embedded records.
input_path = Path("tmp/embedded_records.json")

with input_path.open("r", encoding="utf-8") as input_file:
    embedded_records = json.load(input_file)


# Create a local Chroma database.
client = chromadb.PersistentClient(path="tmp/chroma_db")

collection = client.get_or_create_collection(
    name="askanydoc_chunks"
)


# Add each chunk, vector, and metadata to Chroma.
for index, record in enumerate(embedded_records):
    collection.upsert(
        ids=[f"chunk-{index}"],
        embeddings=[record["embedding"]],
        documents=[record["text"]],
        metadatas=[{
            "source_name": record["source_name"],
            "source_path": record["source_path"],
            "pdf_page_number": record["pdf_page_number"],
            "printed_page_number": record["printed_page_number"],
            "chunk_number_on_page": record["chunk_number_on_page"],
        }],
    )


print("Stored records:", collection.count())
print("Database location: tmp/chroma_db")