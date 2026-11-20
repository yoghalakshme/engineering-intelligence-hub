
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from io import BytesIO


# Extract text from an existing PDF file
def extract_text_from_pdf(file_path):

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


# Extract text from an uploaded PDF
def extract_text_from_bytes(pdf_bytes):

    reader = PdfReader(BytesIO(pdf_bytes))

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


# Split extracted text into chunks
def split_text_into_chunks(text):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    return splitter.split_text(text)


# Test PDF extraction and chunking
if __name__ == "__main__":

    text = extract_text_from_pdf("data/raw/sample.pdf")

    chunks = split_text_into_chunks(text)

    print("Total characters:", len(text))
    print("Total chunks:", len(chunks))

    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i+1}:")
        print(chunk)
