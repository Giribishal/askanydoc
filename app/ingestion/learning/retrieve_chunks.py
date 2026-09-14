import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


# Load the embedded chunk records.
input_path = Path("tmp/embedded_records.json")

with input_path.open("r", encoding="utf-8") as input_file:
    embedded_records = json.load(input_file)


# Load the same model used for the chunk embeddings.
model = SentenceTransformer("all-MiniLM-L6-v2")


# This is the user's question.
question = "Describe the document ingestion process in this AWS design."


# Convert the question into a 384-number vector.
question_embedding = model.encode(question)


def cosine_similarity(first_vector, second_vector):
    first_vector = np.array(first_vector)
    second_vector = np.array(second_vector)

    return np.dot(first_vector, second_vector) / (
        np.linalg.norm(first_vector) * np.linalg.norm(second_vector)
    )


# Compare the question with every chunk.
ranked_records = []

for record in embedded_records:
    score = cosine_similarity(
        question_embedding,
        record["embedding"],
    )

    ranked_records.append({
        "score": float(score),
        "record": record,
    })


# Put the most similar chunks first.
ranked_records.sort(
    key=lambda item: item["score"],
    reverse=True,
)


# Display the three best matches.
for rank, item in enumerate(ranked_records[:3], start=1):
    record = item["record"]

    print(f"\nResult {rank}")
    print("Similarity:", round(item["score"], 4))
    print("Printed page:", record["printed_page_number"])
    print("Chunk number:", record["chunk_number_on_page"])
    print("Text preview:")
    print(record["text"][:500])