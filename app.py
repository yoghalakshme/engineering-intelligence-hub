
import streamlit as st

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
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Engineering Intelligence Hub",
    page_icon="🤖",
    layout="wide"
)


# --------------------------------------------------
# SESSION STATE INITIALIZATION
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "comparison_result" not in st.session_state:
    st.session_state.comparison_result = ""

if "comparison_sources" not in st.session_state:
    st.session_state.comparison_sources = {}

if "comparison_question" not in st.session_state:
    st.session_state.comparison_question = ""


# --------------------------------------------------
# CLEAR COMPARISON RESULT
# --------------------------------------------------

def clear_comparison_result():

    st.session_state.comparison_result = ""
    st.session_state.comparison_sources = {}
    st.session_state.comparison_question = ""


# --------------------------------------------------
# PAGE TITLE
# --------------------------------------------------

st.title("🤖 Engineering Intelligence Hub")

st.caption(
    "Your AI-powered Engineering Research Assistant"
)

st.markdown(
    "Ask questions and compare information across "
    "engineering research documents."
)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.header("⚙️ Settings")

    if st.button("Clear Chat", use_container_width=True):

        st.session_state.messages = []
        st.rerun()

    st.divider()

    # ----------------------------------------------
    # UPLOAD DOCUMENTS
    # ----------------------------------------------

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

                    st.error(f"Upload failed: {e}")

    st.divider()

    # ----------------------------------------------
    # MANAGE DOCUMENTS
    # ----------------------------------------------

    st.subheader("📂 Manage Documents")

    documents = get_all_documents()

    if documents:

        st.caption(
            f"Total uploaded documents: {len(documents)}"
        )

        for filename, chunk_count in documents.items():

            st.write(f"📄 **{filename}**")
            st.caption(f"{chunk_count} chunks")

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

                    st.session_state.messages = []

                    clear_comparison_result()

                    st.session_state.pop(
                        "comparison_selected_docs",
                        None
                    )

                    st.success(
                        f"{selected_delete} deleted successfully!"
                    )

                    st.rerun()

                except Exception as e:

                    st.error(f"Deletion failed: {e}")

            else:

                st.warning(
                    "Please confirm before deleting."
                )

    else:

        st.info("No uploaded documents available.")

    st.divider()

    st.caption(
        "Powered by Python, ChromaDB and Groq"
    )


# --------------------------------------------------
# MODE SELECTION
# --------------------------------------------------

st.subheader("🔍 Choose Your Mode")

mode = st.radio(
    "Select how you want to use the application",
    ["Ask Questions", "Compare Documents"],
    horizontal=True,
    key="mode_selector",
    on_change=clear_comparison_result
)


# ==================================================
# ASK QUESTIONS MODE
# ==================================================

if mode == "Ask Questions":

    st.subheader("📚 Ask Questions")

    st.write(
        "Ask questions about your uploaded engineering documents."
    )

    available_sources = get_available_sources()

    document_options = (
        ["All documents"] + available_sources
    )

    selected_source = st.selectbox(
        "Choose a document to search",
        document_options
    )

    st.divider()

    # ----------------------------------------------
    # DISPLAY CHAT HISTORY
    # ----------------------------------------------

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            if (
                message["role"] == "assistant"
                and message.get("sources")
            ):

                with st.expander("📚 View Source Context"):

                    for i, source in enumerate(
                        message["sources"]
                    ):

                        st.markdown(
                            f"**Source {i + 1}: "
                            f"{source['source']}**"
                        )

                        st.markdown(
                            f"Chunk: {source['chunk_index']}"
                        )

                        st.write(source["content"])

    # ----------------------------------------------
    # QUESTION INPUT
    # ----------------------------------------------

    question = st.chat_input(
        "Ask an engineering question..."
    )

    if question:

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
                            for document, metadata
                            in normalized_results
                        )

                        answer = generate_answer(
                            question,
                            context
                        )

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

                    st.markdown(answer)

                    if sources:

                        with st.expander(
                            "📚 View Source Context"
                        ):

                            for i, source in enumerate(sources):

                                st.markdown(
                                    f"**Source {i + 1}: "
                                    f"{source['source']}**"
                                )

                                st.markdown(
                                    f"Chunk: {source['chunk_index']}"
                                )

                                st.write(source["content"])

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })

                except Exception as e:

                    error_message = (
                        f"Something went wrong: {e}"
                    )

                    st.error(error_message)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message,
                        "sources": []
                    })


# ==================================================
# COMPARE DOCUMENTS MODE
# ==================================================

elif mode == "Compare Documents":

    st.subheader("📊 Multi-Document Intelligence")

    st.write(
        "Select multiple engineering PDFs and ask a question "
        "to compare their information."
    )

    available_sources = get_available_sources()

    if len(available_sources) < 2:

        st.warning(
            "Upload at least two PDFs to use document comparison."
        )

    else:

        # ------------------------------------------
        # SELECT DOCUMENTS
        # ------------------------------------------

        selected_docs = st.multiselect(
            "Select documents to compare (maximum 5)",
            options=available_sources,
            max_selections=5,
            key="comparison_selected_docs",
            on_change=clear_comparison_result
        )

        # ------------------------------------------
        # COMPARISON QUESTION
        # ------------------------------------------

        comparison_question = st.text_area(
            "What would you like to compare?",
            placeholder=(
                "Example: Compare the main concepts and "
                "techniques explained in these documents."
            )
        )

        # ------------------------------------------
        # GENERATE COMPARISON
        # ------------------------------------------

        if st.button(
            "🔍 Generate Comparison",
            use_container_width=True
        ):

            # Clear previous result before validation
            clear_comparison_result()

            if len(selected_docs) < 2:

                st.warning(
                    "Please select at least two documents."
                )

            elif not comparison_question.strip():

                st.warning(
                    "Please enter a comparison question."
                )

            else:

                with st.spinner(
                    "Retrieving information and comparing documents..."
                ):

                    try:

                        # Retrieve relevant chunks
                        results = search_documents_with_sources(
                            comparison_question,
                            selected_sources=selected_docs
                        )

                        # Group chunks by PDF
                        grouped_context = group_results_by_source(
                            results
                        )

                        # Check relevant information in both PDFs
                        if len(grouped_context) < 2:

                            st.session_state.comparison_result = (
                                "Relevant information was found in fewer "
                                "than two selected documents. Try a "
                                "different question or select other PDFs."
                            )

                            st.session_state.comparison_sources = {}

                        else:

                            # Generate comparison
                            answer = generate_comparison_answer(
                                comparison_question,
                                grouped_context
                            )

                            st.session_state.comparison_result = answer

                            st.session_state.comparison_sources = (
                                grouped_context
                            )

                        st.session_state.comparison_question = (
                            comparison_question
                        )

                    except Exception as e:

                        st.error(
                            f"Comparison failed: {e}"
                        )

        # ------------------------------------------
        # DISPLAY COMPARISON RESULT
        # ------------------------------------------

        if st.session_state.comparison_result:

            st.divider()

            st.subheader("📋 Comparison Result")

            st.markdown(
                st.session_state.comparison_result
            )

            # --------------------------------------
            # DISPLAY RETRIEVED SOURCES
            # --------------------------------------

            if st.session_state.comparison_sources:

                with st.expander(
                    "📚 View Retrieved Sources"
                ):

                    for filename, chunks in (
                        st.session_state.comparison_sources.items()
                    ):

                        st.markdown(
                            f"### 📄 {filename}"
                        )

                        for chunk in chunks:

                            st.markdown(
                                f"**Chunk: {chunk['chunk_index']}**"
                            )

                            st.write(
                                chunk["content"]
                            )

                            st.divider()
