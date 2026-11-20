
import os
from dotenv import load_dotenv
from groq import Groq


# =====================================
# 1. LOAD ENVIRONMENT VARIABLES
# =====================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY not found in .env file"
    )

client = Groq(api_key=api_key)


# =====================================
# 2. NORMAL RAG ANSWER GENERATION
# =====================================

def generate_answer(question, context):

    prompt = f"""
You are Engineering Intelligence Hub,
an AI research assistant for engineering students.

Answer the user's question using ONLY
the information provided in the retrieved context.

RULES:

1. Answer the exact question.
2. Never invent facts or use outside knowledge.
3. Understand the scope of the retrieved information.
4. If information is incomplete, explain the limitation.
5. If no relevant information exists, respond:

"I could not find this information in the
provided documents."

6. Use simple English.
7. Organize answers using an introduction
   and numbered points or bullet points.
8. Include citations immediately after supported statements.

Citation format:
[Source: filename, Chunk: number]

RETRIEVED CONTEXT:
{context}

USER QUESTION:
{question}

YOUR ANSWER:
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_completion_tokens=700
    )

    return response.choices[0].message.content


# =====================================
# 3. MULTI-DOCUMENT COMPARISON
# =====================================

def generate_comparison_answer(question, grouped_context):

    # Convert grouped document information into text
    context_parts = []

    for filename, chunks in grouped_context.items():

        context_parts.append(
            f"\nDOCUMENT: {filename}\n"
        )

        for chunk in chunks:

            context_parts.append(
                f"""
[Source: {filename}, Chunk: {chunk['chunk_index']}]

{chunk['content']}
"""
            )

    context = "\n".join(context_parts)

    prompt = f"""
You are Engineering Intelligence Hub,
an AI research assistant for engineering students.

Your task is to compare information across
multiple engineering PDF documents.

Use ONLY the retrieved context.

IMPORTANT RULES:

1. Answer the user's exact comparison question.

2. Explain each document separately.

3. Identify similarities only when supported
   by the retrieved information.

4. Identify differences only when supported
   by the retrieved information.

5. Never invent missing information or use
   outside knowledge.

6. If a document does not contain enough
   information, clearly mention that.

7. Do not assume two concepts are similar
   just because they appear in different documents.

8. Use simple, student-friendly English.

9. Organize the answer using these headings:

   A. Introduction

   B. Document-wise Explanation

   C. Similarities

   D. Differences

   E. Comparison Table

   F. Conclusion

10. Include citations immediately after
    statements they support.

11. Use this exact citation format:

    [Source: filename, Chunk: number]

12. Every factual statement must have a relevant citation.

13. Never use citations such as [Chunk 163] alone.
    Always include the document filename.

14. Never create unsupported citations.

15. If the retrieved context does not contain
    enough information to compare the documents,
    clearly explain the limitation instead of
    generating a misleading comparison.

16. FORMAT THE OUTPUT USING VALID MARKDOWN:

    - Do not use HTML tags such as <br>, <p>, or <div>.
    - Do not use HTML line breaks inside tables.
    - Use normal bullet points for lists.
    - Keep table cells short and concise.
    - Do not put multiple paragraphs inside table cells.
    - Use actual Markdown headings and line breaks.

17. COMPLETENESS:

    - Complete all six sections.
    - Do not stop in the middle of a sentence or table.
    - Always provide a meaningful conclusion.
    - Prioritize complete, accurate explanations over
      unnecessary lengthy descriptions.

RETRIEVED DOCUMENT CONTEXT:

{context}

USER QUESTION:

{question}

YOUR COMPARISON:
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_completion_tokens=3500
    )

    # Debug information
    print("\n--- COMPARISON GENERATION DEBUG ---")

    print(
        "Finish reason:",
        response.choices[0].finish_reason
    )

    print(
        "Usage:",
        response.usage
    )

    print("----------------------------------")

    return response.choices[0].message.content


# =====================================
# 4. TEST GENERATION MODULE
# =====================================

if __name__ == "__main__":

    question = "What is Hadoop and what are its components?"

    context = """
[Source: UNIT III BASICS_OF_HADOOP.pdf, Chunk: 2]

Hadoop is a distributed data processing framework
that allows storage and processing of large datasets
across multiple machines.
"""

    answer = generate_answer(question, context)

    print("\nQuestion:", question)
    print("\nAI Answer:\n", answer)
