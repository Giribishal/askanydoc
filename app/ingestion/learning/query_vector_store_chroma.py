from sentence_transformers import SentenceTransformer
import chromadb


# Connect to the local Chroma database.
client = chromadb.PersistentClient(path="tmp/chroma_db")

collection = client.get_collection(
    name="askanydoc_chunks"
)


# Load the same model used for the stored chunk embeddings.
model = SentenceTransformer("all-MiniLM-L6-v2")


# Ask a question.
question = "Describe the document ingestion process in this AWS design."


# Convert the question into a vector.
question_embedding = model.encode(question).tolist()


# Ask Chroma for the three nearest chunks.
results = collection.query(
    query_embeddings=[question_embedding],
    n_results=3,
)


# Display the retrieved chunks.
for rank, (document, metadata, distance) in enumerate(
    zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ),
    start=1,
):
    print(f"\nResult {rank}")
    print("Distance:", round(distance, 4))
    print("Source:", metadata["source_name"])
    print("Printed page:", metadata["printed_page_number"])
    print("Chunk number:", metadata["chunk_number_on_page"])
    print("Text preview:")
    print(document[:500])