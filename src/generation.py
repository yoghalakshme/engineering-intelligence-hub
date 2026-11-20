
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

# Initialize Groq client
client = Groq(api_key=api_key)


# =====================================
# 2. GENERATE ANSWER USING RAG
# =====================================

def generate_answer(question, context):

    prompt = f"""
You are Engineering Intelligence Hub,
an AI research assistant for engineering students.

Your task is to answer questions using ONLY
the information provided in the retrieved context.

FOLLOW THESE RULES CAREFULLY:

1. Answer the user's exact question.

2. Use only information available in the context.
   Never add outside knowledge or invent facts.

3. Understand the scope of the retrieved information.
   For example:
   - Hadoop architecture components are different
     from Hadoop Java API components.
   - Do not present Java API classes as the complete
     Hadoop architecture.

4. If the context contains only part of the answer,
   explain what information is available and clearly
   mention what is not covered in the documents.

5. If the context does not contain relevant information,
   respond:
   "I could not find this information in the
   provided documents."

6. Organize answers using:
   - A short introduction
   - Numbered points or bullet points
   - Simple explanations

7. Include source citations immediately after
   the statements they support.

8. Use this exact citation format:
   [Source: filename, Chunk: number]

9. Do not create citations for information that
   is not supported by the context.

10. Keep the answer clear, accurate and easy
    for engineering students to understand.

RETRIEVED CONTEXT:
{context}

USER QUESTION:
{question}

YOUR ANSWER:
"""

    # Send prompt to Groq
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
# 3. TEST GENERATION MODULE
# =====================================

if __name__ == "__main__":

    question = "What is Hadoop and what are its components?"

    context = """
    [Source: UNIT III BASICS_OF_HADOOP.pdf, Chunk: 2]

    Hadoop is a distributed data processing framework
    that allows storage and processing of large datasets
    across multiple machines.

    [Source: UNIT III BASICS_OF_HADOOP.pdf, Chunk: 67]

    The Java interface in Hadoop includes:
    Configuration and FileSystem.

    [Source: UNIT III BASICS_OF_HADOOP.pdf, Chunk: 74]

    The Java interface is used for developing custom
    MapReduce applications and interacting with HDFS.
    """

    answer = generate_answer(question, context)

    print("\nQuestion:", question)
    print("\nAI Answer:\n", answer)
