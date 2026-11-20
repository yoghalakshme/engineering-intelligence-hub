
from sentence_transformers import SentenceTransformer

# Load a pretrained embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embeddings(texts):
    embeddings = model.encode(texts)
    return embeddings.tolist()


if __name__ == "__main__":
    sentences = [
        "Machine learning helps computers learn.",
        "Deep learning uses neural networks."
    ]

    vectors = create_embeddings(sentences)

    print("Number of embeddings:", len(vectors))
    print("Vector dimensions:", len(vectors[0]))
    print("First embedding:", vectors[0][:5])

