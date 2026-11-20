
import chromadb
import hashlib

from src.ingestion import (
    extract_text_from_pdf,
    extract_text_from_bytes,
    split_text_into_chunks
)

from src.embeddings import create_embeddings


# =====================================
# 1. CREATE PERSISTENT VECTOR DATABASE
# =====================================

client = chromadb.PersistentClient(
    path="data/chroma_db"
)

collection = client.get_or_create_collection(
    name="engineering_documents",
    metadata={"hnsw:space": "cosine"}
)


# =====================================
# 2. STORE UPLOADED PDF DOCUMENTS
# =====================================

def store_uploaded_pdf(pdf_bytes, filename):

    text = extract_text_from_bytes(pdf_bytes)

    if not text.strip():
        raise ValueError("No readable text found in PDF.")

    chunks = split_text_into_chunks(text)

    if not chunks:
        raise ValueError("No text chunks generated.")

    embeddings = create_embeddings(chunks)

    ids = [
        hashlib.sha256(
            f"{filename}:{i}:{chunk}".encode("utf-8")
        ).hexdigest()
        for i, chunk in enumerate(chunks)
    ]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[
            {
                "source": filename,
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]
    )

    return len(chunks)


# =====================================
# 3. GET ALL UPLOADED DOCUMENTS
# =====================================

def get_all_documents():

    result = collection.get(
        include=["metadatas"]
    )

    documents = {}

    for metadata in result["metadatas"]:

        if metadata and "source" in metadata:

            filename = metadata["source"]

            documents[filename] = (
                documents.get(filename, 0) + 1
            )

    return documents


# =====================================
# 4. DELETE A SELECTED DOCUMENT
# =====================================

def delete_document(filename):

    collection.delete(
        where={"source": filename}
    )

    return True


# =====================================
# 5. OLD FUNCTION RETAINED
# =====================================

def store_documents(chunks):

    embeddings = create_embeddings(chunks)

    collection.add(
        ids=[
            f"legacy_chunk_{i}"
            for i in range(len(chunks))
        ],
        documents=chunks,
        embeddings=embeddings
    )

    print("Documents stored successfully!")
    print("Total stored:", collection.count())


# =====================================
# 6. TEST DATABASE
# =====================================

if __name__ == "__main__":

    print("\nTotal stored chunks:", collection.count())

    print("\nUploaded Documents:")

    documents = get_all_documents()

    if not documents:
        print("No uploaded documents found.")

    for filename, count in documents.items():
        print(f"{filename} - {count} chunks")
