
from src.vector_store import collection
from src.embeddings import create_embeddings


# Maximum cosine distance for accepting retrieved chunks
MAX_DISTANCE = 0.80


# Get all uploaded PDF filenames
def get_available_sources():

    result = collection.get(include=["metadatas"])

    sources = {
        item["source"]
        for item in result["metadatas"]
        if item and "source" in item
    }

    return sorted(sources)


# Search documents with source information
def search_documents_with_sources(question, source=None):

    # Convert question into an embedding
    query_embedding = create_embeddings([question])[0]

    search_args = {
        "query_embeddings": [query_embedding],
        "n_results": 3
    }

    # Filter by selected PDF
    if source and source != "All documents":
        search_args["where"] = {"source": source}

    # Search ChromaDB
    results = collection.query(**search_args)

    # Check whether any documents were retrieved
    if not results.get("documents") or not results["documents"][0]:
        print("\nNo documents retrieved.")
        return []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    distances_result = results.get("distances")

    if not distances_result or not distances_result[0]:
        distances = [float("inf")] * len(documents)
    else:
        distances = distances_result[0]

    matches = []

    print("\n--- RETRIEVAL DISTANCE SCORES ---")

    # Filter chunks using cosine distance
    for i, (document, metadata, distance) in enumerate(
        zip(documents, metadatas, distances)
    ):

        print(f"Chunk {i+1}: {distance:.4f}")

        if distance <= MAX_DISTANCE:

            if metadata is None:
                metadata = {
                    "source": "Unknown / legacy document",
                    "chunk_index": -1
                }

            matches.append((document, metadata))

    print("---------------------------------")

    print("Accepted chunks:", len(matches))
    print("Rejected chunks:", len(documents) - len(matches))
    print()

    return matches


# Maintain compatibility with previous code
def search_documents(question):

    results = search_documents_with_sources(question)

    return [
        document
        for document, metadata in results
    ]


# Test retrieval independently
if __name__ == "__main__":

    question = "How does self-attention work?"

    results = search_documents_with_sources(question)

    if not results:
        print("No relevant information found.")

    for document, metadata in results:

        print("\nSource:", metadata["source"])
        print("Chunk:", metadata["chunk_index"])
        print("Content:")
        print(document)
