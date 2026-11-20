
from src.vector_store import collection
from src.embeddings import create_embeddings


# Maximum cosine distance for accepting retrieved chunks
MAX_DISTANCE = 0.80

# Maximum number of PDFs to compare
MAX_DOCUMENTS = 5

# Maximum relevant chunks per PDF
CHUNKS_PER_DOCUMENT = 3


# =====================================
# 1. GET ALL AVAILABLE PDF SOURCES
# =====================================

def get_available_sources():

    result = collection.get(include=["metadatas"])

    sources = {
        item["source"]
        for item in result["metadatas"]
        if item and "source" in item
    }

    return sorted(sources)


# =====================================
# 2. SEARCH ACROSS MULTIPLE DOCUMENTS
# =====================================


def search_documents_with_sources(
    question,
    source=None,
    selected_sources=None
):

    # Convert question into an embedding
    query_embedding = create_embeddings([question])[0]

    available_sources = get_available_sources()

    # Select documents for retrieval
    if selected_sources is not None:

        selected_documents = [
            name for name in selected_sources
            if name in available_sources
        ]

    elif source and source != "All documents":

        selected_documents = (
            [source] if source in available_sources else []
        )

    else:

        selected_documents = available_sources[:MAX_DOCUMENTS]

    if not selected_documents:
        print("No available documents found.")
        return []

    matches = []

    print("\n--- MULTI-DOCUMENT RETRIEVAL ---")

    for filename in selected_documents:

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=CHUNKS_PER_DOCUMENT,
            where={"source": filename}
        )

        if not results.get("documents") or not results["documents"][0]:
            continue

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances_result = results.get("distances")

        if not distances_result or not distances_result[0]:
            distances = [float("inf")] * len(documents)
        else:
            distances = distances_result[0]

        accepted_count = 0

        for document, metadata, distance in zip(
            documents, metadatas, distances
        ):

            print(f"{filename} | Distance: {distance:.4f}")

            if distance <= MAX_DISTANCE:

                if metadata is None:
                    metadata = {
                        "source": filename,
                        "chunk_index": -1
                    }

                matches.append((document, metadata))
                accepted_count += 1

        print(f"Accepted from {filename}: {accepted_count}")

    print("--------------------------------")
    print("Total accepted chunks:", len(matches))
    print()

    return matches



# =====================================
# 3. GROUP RESULTS BY PDF
# =====================================

def group_results_by_source(results):

    grouped_results = {}

    for document, metadata in results:

        source = metadata.get(
            "source",
            "Unknown / legacy document"
        )

        if source not in grouped_results:
            grouped_results[source] = []

        grouped_results[source].append({
            "content": document,
            "chunk_index": metadata.get("chunk_index", -1)
        })

    return grouped_results


# =====================================
# 4. OLD FUNCTION RETAINED
# =====================================

def search_documents(question):

    results = search_documents_with_sources(question)

    return [
        document
        for document, metadata in results
    ]


# =====================================
# 5. TEST RETRIEVAL
# =====================================

if __name__ == "__main__":

    question = question = "What is Hadoop and how does it process large datasets?"

    results = search_documents_with_sources(question)

    grouped = group_results_by_source(results)

    if not grouped:
        print("No relevant information found.")

    for filename, chunks in grouped.items():

        print("\nSource:", filename)

        for chunk in chunks:
            print("Chunk:", chunk["chunk_index"])
            print("Content:")
            print(chunk["content"])
