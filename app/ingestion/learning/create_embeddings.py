import json
from pathlib import Path

from sentence_transformers import SentenceTransformer


# Load the chunk records.
input_path = Path("tmp/chunk_records.json")

with input_path.open("r", encoding="utf-8") as input_file:
    chunk_records = json.load(input_file)


# Load the local embedding model.
model = SentenceTransformer("all-MiniLM-L6-v2")


embedded_records = []

# Create one vector for each chunk.
for chunk_record in chunk_records:
    embedding = model.encode(chunk_record["text"])

    embedded_record = {
        **chunk_record,
        "embedding": embedding.tolist(),
    }

    embedded_records.append(embedded_record)


# Save the chunks and their vectors.
output_path = Path("tmp/embedded_records.json")
output_path.parent.mkdir(exist_ok=True)

with output_path.open("w", encoding="utf-8") as output_file:
    json.dump(
        embedded_records,
        output_file,
        indent=2,
        ensure_ascii=False,
    )


print("Total embedded records:", len(embedded_records))
print("Vector length:", len(embedded_records[0]["embedding"]))
print("Saved embeddings to:", output_path)