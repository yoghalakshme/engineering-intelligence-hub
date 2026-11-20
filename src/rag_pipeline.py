
from src.retrieval import search_documents
from src.generation import generate_answer


def ask_question(question):

    # Step 1: Retrieve relevant chunks
    documents = search_documents(question)

    # Step 2: Combine retrieved chunks
    context = "\n\n".join(documents)

    # Step 3: Generate answer using Groq
    answer = generate_answer(question, context)

    return answer


if __name__ == "__main__":

    question = "How does self-attention work?"

    answer = ask_question(question)

    print("\nQuestion:", question)
    print("\nAI Answer:\n", answer)
