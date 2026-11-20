
import logging

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field

from src.generation import (
    generate_answer,
    generate_comparison_answer
)

from src.vector_store import (
    store_uploaded_pdf,
    get_all_documents,
    delete_document
)

from src.retrieval import (
    get_available_sources,
    search_documents_with_sources,
    group_results_by_source
)


# --------------------------------------------------
# LOGGING CONFIGURATION
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024


# --------------------------------------------------
# 1. CREATE FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="Engineering Intelligence Hub API",
    description="AI-powered Engineering Research Assistant",
    version="1.2.0"
)


# --------------------------------------------------
# 2. REQUEST MODELS
# --------------------------------------------------

class QuestionRequest(BaseModel):

    question: str = Field(..., max_length=2000)
    source: str | None = None


class ComparisonRequest(BaseModel):

    question: str = Field(..., max_length=2000)

    selected_sources: list[str] = Field(
        ...,
        min_length=2,
        max_length=5
    )


# --------------------------------------------------
# 3. HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "message": "Engineering Intelligence Hub API is running"
    }


# --------------------------------------------------
# 4. UPLOAD PDF
# --------------------------------------------------

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    if not file.filename or not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    if "/" in file.filename or "\\" in file.filename:

        raise HTTPException(
            status_code=400,
            detail="Invalid filename."
        )

    try:

        pdf_bytes = await file.read(MAX_FILE_SIZE + 1)

        if not pdf_bytes:

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        if len(pdf_bytes) > MAX_FILE_SIZE:

            raise HTTPException(
                status_code=413,
                detail="PDF file size must not exceed 10 MB."
            )

        if not pdf_bytes.startswith(b"%PDF-"):

            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file. Please upload a valid PDF."
            )

        chunks = store_uploaded_pdf(
            pdf_bytes,
            file.filename
        )

        logger.info(
            "PDF uploaded successfully: %s",
            file.filename
        )

        return {
            "message": "PDF uploaded successfully",
            "filename": file.filename,
            "chunks_stored": chunks
        }

    except HTTPException:
        raise

    except Exception:

        logger.exception("PDF upload failed")

        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while uploading the PDF."
        )

    finally:

        await file.close()


# --------------------------------------------------
# 5. LIST DOCUMENTS
# --------------------------------------------------

@app.get("/documents")
def list_documents():

    try:

        documents = get_all_documents()

        return {
            "total_documents": len(documents),
            "documents": documents
        }

    except Exception:

        logger.exception("Document listing failed")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve documents."
        )


# --------------------------------------------------
# 6. ASK QUESTION
# --------------------------------------------------

@app.post("/ask")
def ask_question(request: QuestionRequest):

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:

        results = search_documents_with_sources(
            question,
            source=request.source
        )

        if not results:

            return {
                "question": question,
                "answer": (
                    "I could not find relevant information "
                    "in the selected documents."
                ),
                "sources": []
            }

        normalized_results = [
            (document, metadata or {})
            for document, metadata in results
        ]

        context = "\n\n".join(
            f"""
[Source: {metadata.get('source', 'Unknown document')},
Chunk: {metadata.get('chunk_index', -1)}]

{document}
"""
            for document, metadata in normalized_results
        )

        answer = generate_answer(
            question,
            context
        )

        sources = [
            {
                "source": metadata.get(
                    "source",
                    "Unknown document"
                ),
                "chunk_index": metadata.get(
                    "chunk_index",
                    -1
                )
            }
            for document, metadata in normalized_results
        ]

        return {
            "question": question,
            "answer": answer,
            "sources": sources
        }

    except Exception:

        logger.exception("Question answering failed")

        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing your question."
        )


# --------------------------------------------------
# 7. COMPARE MULTIPLE DOCUMENTS
# --------------------------------------------------

@app.post("/compare")
def compare_documents(request: ComparisonRequest):

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Comparison question cannot be empty."
        )

    selected_sources = request.selected_sources

    # Check for duplicate filenames
    if len(selected_sources) != len(set(selected_sources)):

        raise HTTPException(
            status_code=400,
            detail="Duplicate document selections are not allowed."
        )

    try:

        # Get uploaded document names
        available_sources = get_available_sources()

        # Validate selected documents
        invalid_sources = [
            filename
            for filename in selected_sources
            if filename not in available_sources
        ]

        if invalid_sources:

            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Some selected documents were not found.",
                    "invalid_documents": invalid_sources
                }
            )

        # Retrieve relevant chunks from selected PDFs
        results = search_documents_with_sources(
            question,
            selected_sources=selected_sources
        )

        if not results:

            return {
                "question": question,
                "answer": (
                    "No relevant information was found "
                    "in the selected documents."
                ),
                "sources": []
            }

        # Group retrieved chunks by PDF
        grouped_context = group_results_by_source(
            results
        )

        # At least two documents must contain relevant information
        if len(grouped_context) < 2:

            return {
                "question": question,
                "answer": (
                    "Relevant information was found in fewer "
                    "than two selected documents. Try another "
                    "question or select different PDFs."
                ),
                "sources": []
            }

        # Generate AI comparison
        answer = generate_comparison_answer(
            question,
            grouped_context
        )

        # Prepare source information for API response
        sources = []

        for filename, chunks in grouped_context.items():

            sources.append({
                "source": filename,
                "chunks": [
                    {
                        "chunk_index": chunk["chunk_index"],
                        "content": chunk["content"]
                    }
                    for chunk in chunks
                ]
            })

        logger.info(
            "Document comparison completed for %d PDFs",
            len(sources)
        )

        return {
            "question": question,
            "selected_documents": selected_sources,
            "answer": answer,
            "sources": sources
        }

    except HTTPException:
        raise

    except Exception:

        logger.exception("Document comparison failed")

        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while comparing documents."
        )


# --------------------------------------------------
# 8. DELETE DOCUMENT
# --------------------------------------------------

@app.delete("/documents/{filename}")
def remove_document(filename: str):

    try:

        documents = get_all_documents()

        if filename not in documents:

            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        delete_document(filename)

        logger.info(
            "Document deleted: %s",
            filename
        )

        return {
            "message": "Document deleted successfully",
            "filename": filename
        }

    except HTTPException:
        raise

    except Exception:

        logger.exception("Document deletion failed")

        raise HTTPException(
            status_code=500,
            detail="Unable to delete the document."
        )
