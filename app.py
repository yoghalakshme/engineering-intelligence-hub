
import streamlit as st

from src.generation import generate_answer

from src.vector_store import (
    store_uploaded_pdf,
    get_all_documents,
    delete_document
)

from src.retrieval import (
    get_available_sources,
    search_documents_with_sources
)


# --------------------------------
# 1. Page configuration
# --------------------------------

st.set_page_config(
    page_title="Engineering Intelligence Hub",
    page_icon="🤖",
    layout="wide"
)


# --------------------------------
# 2. Application heading
# --------------------------------

st.title("🤖 Engineering Intelligence Hub")

st.caption(
    "Your AI-powered Engineering Research Assistant"
)

st.markdown(
    "Ask questions about your engineering research documents."
)


# --------------------------------
# 3. Initialize chat history
# --------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# --------------------------------
# 4. Sidebar
# --------------------------------

with st.sidebar:

    st.header("⚙️ Settings")

    # Clear chat
    if st.button(
        "Clear Chat",
        use_container_width=True
    ):

        st.session_state.messages = []
        st.rerun()

    st.divider()

    # --------------------------------
    # PDF upload
    # --------------------------------

    st.subheader("📄 Upload Documents")

    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:

        for uploaded_file in uploaded_files:

            if st.button(
                f"Process {uploaded_file.name}",
                key=f"process_{uploaded_file.name}"
            ):

                try:

                    with st.spinner(
                        f"Processing {uploaded_file.name}..."
                    ):

                        chunks = store_uploaded_pdf(
                            uploaded_file.getvalue(),
                            uploaded_file.name
                        )

                    st.success(
                        f"{uploaded_file.name}: "
                        f"{chunks} chunks stored!"
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Upload failed: {e}"
                    )

    st.divider()

    # --------------------------------
    # Document management
    # --------------------------------

    st.subheader("📂 Manage Documents")

    documents = get_all_documents()

    if documents:

        st.caption(
            f"Total uploaded documents: {len(documents)}"
        )

        for filename, chunk_count in documents.items():

            st.write(f"📄 **{filename}**")

            st.caption(
                f"{chunk_count} chunks"
            )

        st.divider()

        selected_delete = st.selectbox(
            "Select document to delete",
            list(documents.keys()),
            key="delete_document_select"
        )

        confirm_delete = st.checkbox(
            "I confirm that I want to delete this document",
            key="confirm_delete"
        )

        if st.button(
            "🗑️ Delete Document",
            use_container_width=True
        ):

            if confirm_delete:

                try:

                    delete_document(selected_delete)

                    st.success(
                        f"{selected_delete} deleted successfully!"
                    )

                    st.session_state.messages = []

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Deletion failed: {e}"
                    )

            else:

                st.warning(
                    "Please confirm before deleting."
                )

    else:

        st.info(
            "No uploaded documents available."
        )

    st.divider()

    st.caption(
        "Powered by Python, ChromaDB and Groq"
    )


# --------------------------------
# 5. Document selection
# --------------------------------

st.subheader("📚 Select Research Document")

available_sources = get_available_sources()

document_options = [
    "All documents"
] + available_sources

selected_source = st.selectbox(
    "Choose a document to search",
    document_options
)


# --------------------------------
# 6. Display previous messages
# --------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if (
            message["role"] == "assistant"
            and message.get("sources")
        ):

            with st.expander("View source context"):

                for i, source in enumerate(
                    message["sources"]
                ):

                    st.markdown(
                        f"**Source {i+1}: "
                        f"{source['source']}**"
                    )

                    st.markdown(
                        f"Chunk: {source['chunk_index']}"
                    )

                    st.write(
                        source["content"]
                    )


# --------------------------------
# 7. Chat input
# --------------------------------

question = st.chat_input(
    "Ask an engineering question..."
)


# --------------------------------
# 8. Generate AI answer
# --------------------------------

if question:

    # Display user question
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):

        st.markdown(question)

    with st.chat_message("assistant"):

        with st.spinner(
            "Searching documents and generating answer..."
        ):

            try:

                # Retrieve relevant documents
                results = search_documents_with_sources(
                    question,
                    source=selected_source
                )

                if not results:

                    answer = (
                        "I could not find relevant information "
                        "in the selected documents."
                    )

                    sources = []

                else:

                    # Handle old records without metadata
                    normalized_results = [
                        (document, metadata or {})
                        for document, metadata in results
                    ]

                    # Prepare context with source information
                    context = "\n\n".join(
                        f"""
[Source: {metadata.get('source', 'Unknown document')},
Chunk: {metadata.get('chunk_index', -1)}]

{document}
"""
                        for document, metadata in normalized_results
                    )

                    # Generate answer using Groq
                    answer = generate_answer(
                        question,
                        context
                    )

                    # Store source details
                    sources = []

                    for document, metadata in normalized_results:

                        sources.append({
                            "source": metadata.get(
                                "source",
                                "Unknown document"
                            ),

                            "chunk_index": metadata.get(
                                "chunk_index",
                                -1
                            ),

                            "content": document
                        })

                # Display answer
                st.markdown(answer)

                # Display source context
                if sources:

                    with st.expander(
                        "View source context"
                    ):

                        for i, source in enumerate(sources):

                            st.markdown(
                                f"**Source {i+1}: "
                                f"{source['source']}**"
                            )

                            st.markdown(
                                f"Chunk: {source['chunk_index']}"
                            )

                            st.write(
                                source["content"]
                            )

                # Save assistant response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

            except Exception as e:

                st.error(
                    f"Something went wrong: {e}"
                )
