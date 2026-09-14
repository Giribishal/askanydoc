import json
from pathlib import Path

from sentence_transformers import SentenceTransformer


# Load the first chunk from our chunk records.
input_path = Path("tmp/chunk_records.json")

with input_path.open("r", encoding="utf-8") as input_file:
    chunk_records = json.load(input_file)

first_chunk = chunk_records[0]


# Load the local embedding model.
model = SentenceTransformer("all-MiniLM-L6-v2")


# Convert the chunk text into a vector.
embedding = model.encode(first_chunk["text"])


print("Source:", first_chunk["source_name"])
print("Printed page:", first_chunk["printed_page_number"])
print("Chunk number:", first_chunk["chunk_number_on_page"])
print("Vector length:", len(embedding))
print("First five numbers:", embedding[:5])