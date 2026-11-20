
from src.retrieval import (
    search_documents,
    search_documents_with_sources,
    group_results_by_source
)

from src.generation import (
    generate_answer,
    generate_comparison_answer
)


# =====================================
# 1. NORMAL QUESTION ANSWERING
# =====================================

def ask_question(question):

    # Step 1: Retrieve relevant chunks
    documents = search_documents(question)

    if not documents:
        return "I could not find this information in the provided documents."

    # Step 2: Combine retrieved chunks
    context = "\n\n".join(documents)

    # Step 3: Generate answer
    answer = generate_answer(question, context)

    return answer


# =====================================
# 2. MULTI-DOCUMENT COMPARISON
# =====================================

def compare_documents(question):

    # Step 1: Retrieve relevant chunks with source details
    results = search_documents_with_sources(question)

    if not results:
        return "I could not find relevant information in the provided documents."

    # Step 2: Group retrieved chunks by PDF
    grouped_context = group_results_by_source(results)

    # Step 3: Check how many documents have relevant information
    if len(grouped_context) < 2:

        return (
            "I found relevant information in only one document. "
            "At least two documents need relevant information "
            "to perform a comparison."
        )

    # Step 4: Generate comparison
    answer = generate_comparison_answer(
        question,
        grouped_context
    )

    return answer


# =====================================
# 3. TEST PIPELINE
# =====================================

if __name__ == "__main__":

    question = "Compare the concepts explained in the uploaded documents."

    print("\nQuestion:", question)

    print("\n--- MULTI-DOCUMENT COMPARISON ---")

    answer = compare_documents(question)

    print("\nAI Comparison:\n")
    print(answer)
