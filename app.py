
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

from src.chat_history import (
    create_conversation,
    save_message,
    get_conversations,
    get_messages,
    delete_conversation
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Engineering Intelligence Hub",
    page_icon="🤖",
    layout="wide"
)


# ==================================================
# SESSION STATE INITIALIZATION
# ==================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_conversation_id" not in st.session_state:
    st.session_state.active_conversation_id = None

if "active_conversation_mode" not in st.session_state:
    st.session_state.active_conversation_mode = None

if "mode_selector" not in st.session_state:
    st.session_state.mode_selector = "Ask Questions"

if "comparison_result" not in st.session_state:
    st.session_state.comparison_result = ""

if "comparison_sources" not in st.session_state:
    st.session_state.comparison_sources = {}

if "comparison_question" not in st.session_state:
    st.session_state.comparison_question = ""


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def clear_comparison_result():

    st.session_state.comparison_result = ""
    st.session_state.comparison_sources = {}
    st.session_state.comparison_question = ""


def start_new_chat():

    st.session_state.active_conversation_id = None
    st.session_state.active_conversation_mode = None
    st.session_state.messages = []

    clear_comparison_result()

    st.session_state.mode_selector = "Ask Questions"


def handle_mode_change():

    # Start a fresh conversation when the user
    # manually changes between the two modes.

    st.session_state.active_conversation_id = None
    st.session_state.active_conversation_mode = None
    st.session_state.messages = []

    clear_comparison_result()


def open_conversation(conversation):

    conversation_id = conversation["id"]

    conversation_mode = conversation.get(
        "mode",
        "Ask Questions"
    )

    if conversation_mode not in [
        "Ask Questions",
        "Compare Documents"
    ]:
        conversation_mode = "Ask Questions"

    st.session_state.active_conversation_id = conversation_id

    st.session_state.active_conversation_mode = conversation_mode

    st.session_state.messages = get_messages(
        conversation_id
    )

    # Restore the original mode.
    st.session_state.mode_selector = conversation_mode

    clear_comparison_result()


def get_active_conversation_id(title, mode):

    # Create a new conversation if there is no active
    # conversation or if the mode has changed.

    if (
        st.session_state.active_conversation_id is None
        or st.session_state.active_conversation_mode != mode
    ):

        conversation_id = create_conversation(
            title=title[:60],
            mode=mode
        )

        st.session_state.active_conversation_id = conversation_id

        st.session_state.active_conversation_mode = mode

    return st.session_state.active_conversation_id


def display_messages():

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            sources = message.get("sources", [])

            if message["role"] == "assistant" and sources:

                with st.expander("📚 View Retrieved Sources"):

                    for i, source in enumerate(sources):

                        st.markdown(
                            f"**Source {i + 1}: {source['source']}**"
                        )

                        st.markdown(
                            f"Chunk: {source['chunk_index']}"
                        )

                        st.write(source["content"])

                        st.divider()


# ==================================================
# PAGE TITLE
# ==================================================

st.title("🤖 Engineering Intelligence Hub")

st.caption(
    "Your AI-powered Engineering Research Assistant"
)

st.markdown(
    "Ask questions and compare information across "
    "engineering research documents."
)


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.header("⚙️ Settings")

    # ----------------------------------------------
    # NEW CHAT
    # ----------------------------------------------

    if st.button(
        "➕ New Chat",
        use_container_width=True
    ):

        start_new_chat()
        st.rerun()

    st.divider()

    # ----------------------------------------------
    # CHAT HISTORY
    # ----------------------------------------------

    st.subheader("💬 Chat History")

    conversations = get_conversations()

    if conversations:

        for conversation in conversations:

            conversation_id = conversation["id"]

            title = conversation["title"]

            conversation_mode = conversation.get(
                "mode",
                "Ask Questions"
            )

            # Short mode label
            if conversation_mode == "Compare Documents":
                mode_label = "📊"
            else:
                mode_label = "💬"

            if st.button(
                f"{mode_label} {title[:35]}",
                key=f"chat_{conversation_id}",
                use_container_width=True
            ):

                open_conversation(conversation)

                st.rerun()

        st.divider()

        # ------------------------------------------
        # DELETE CONVERSATION
        # ------------------------------------------

        delete_options = {
            f"{chat['title'][:35]} (ID: {chat['id']})": chat["id"]
            for chat in conversations
        }

        selected_chat = st.selectbox(
            "Select conversation to delete",
            options=list(delete_options.keys()),
            key="delete_chat_select"
        )

        if st.button(
            "🗑️ Delete Chat",
            use_container_width=True
        ):

            conversation_id = delete_options[selected_chat]

            delete_conversation(conversation_id)

            if (
                st.session_state.active_conversation_id
                == conversation_id
            ):

                start_new_chat()

            st.success(
                "Conversation deleted successfully!"
            )

            st.rerun()

    else:

        st.info("No previous conversations yet.")

    st.divider()

    # ----------------------------------------------
    # PDF UPLOAD
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
        "Powered by Python, ChromaDB, SQLite and Groq"
    )


# ==================================================
# MODE SELECTION
# ==================================================

st.subheader("🔍 Choose Your Mode")

mode = st.radio(
    "Select how you want to use the application",
    ["Ask Questions", "Compare Documents"],
    horizontal=True,
    key="mode_selector",
    on_change=handle_mode_change
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
    # QUESTION INPUT
    # ----------------------------------------------

    question = st.chat_input(
        "Ask an engineering question..."
    )

    if question:

        try:

            # --------------------------------------
            # CREATE OR GET CONVERSATION
            # --------------------------------------

            conversation_id = get_active_conversation_id(
                question,
                "Ask Questions"
            )

            # --------------------------------------
            # SAVE USER QUESTION
            # --------------------------------------

            save_message(
                conversation_id,
                "user",
                question
            )

            st.session_state.messages.append({

                "role": "user",

                "content": question

            })

            # --------------------------------------
            # RETRIEVE DOCUMENTS
            # --------------------------------------

            with st.spinner(
                "Searching documents and generating answer..."
            ):

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
                        for document, metadata in normalized_results
                    )

                    # ----------------------------------
                    # GENERATE ANSWER
                    # ----------------------------------

                    answer = generate_answer(
                        question,
                        context
                    )

                    # ----------------------------------
                    # PREPARE SOURCES
                    # ----------------------------------

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

            # --------------------------------------
            # SAVE ASSISTANT ANSWER
            # --------------------------------------

            save_message(
                conversation_id,
                "assistant",
                answer,
                sources
            )

            st.session_state.messages.append({

                "role": "assistant",

                "content": answer,

                "sources": sources

            })

        except Exception as e:

            error_message = f"Something went wrong: {e}"

            if st.session_state.active_conversation_id is not None:

                save_message(
                    st.session_state.active_conversation_id,
                    "assistant",
                    error_message,
                    []
                )

                st.session_state.messages.append({

                    "role": "assistant",

                    "content": error_message,

                    "sources": []

                })

            st.error(error_message)

    # ----------------------------------------------
    # DISPLAY CHAT HISTORY
    # ----------------------------------------------

    display_messages()


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

                try:

                    # ----------------------------------
                    # CREATE OR GET CONVERSATION
                    # ----------------------------------

                    conversation_id = get_active_conversation_id(
                        comparison_question,
                        "Compare Documents"
                    )

                    # ----------------------------------
                    # SAVE USER QUESTION
                    # ----------------------------------

                    save_message(
                        conversation_id,
                        "user",
                        comparison_question
                    )

                    st.session_state.messages.append({

                        "role": "user",

                        "content": comparison_question

                    })

                    with st.spinner(
                        "Retrieving information and comparing documents..."
                    ):

                        # ----------------------------------
                        # RETRIEVE DOCUMENTS
                        # ----------------------------------

                        results = search_documents_with_sources(
                            comparison_question,
                            selected_sources=selected_docs
                        )

                        grouped_context = group_results_by_source(
                            results
                        )

                        # ----------------------------------
                        # CHECK RESULTS
                        # ----------------------------------

                        if len(grouped_context) < 2:

                            answer = (
                                "Relevant information was found in fewer "
                                "than two selected documents. Try a "
                                "different question or select other PDFs."
                            )

                            comparison_sources = []

                        else:

                            # ----------------------------------
                            # GENERATE COMPARISON
                            # ----------------------------------

                            answer = generate_comparison_answer(
                                comparison_question,
                                grouped_context
                            )

                            # ----------------------------------
                            # FLATTEN SOURCES FOR SQLITE
                            # ----------------------------------

                            comparison_sources = []

                            for filename, chunks in grouped_context.items():

                                for chunk in chunks:

                                    comparison_sources.append({

                                        "source": filename,

                                        "chunk_index": chunk["chunk_index"],

                                        "content": chunk["content"]

                                    })

                    # --------------------------------------
                    # SAVE COMPARISON ANSWER
                    # --------------------------------------

                    save_message(
                        conversation_id,
                        "assistant",
                        answer,
                        comparison_sources
                    )

                    st.session_state.messages.append({

                        "role": "assistant",

                        "content": answer,

                        "sources": comparison_sources

                    })

                    # --------------------------------------
                    # UPDATE COMPARISON STATE
                    # --------------------------------------

                    st.session_state.comparison_result = answer

                    st.session_state.comparison_sources = grouped_context

                    st.session_state.comparison_question = (
                        comparison_question
                    )

                except Exception as e:

                    error_message = f"Comparison failed: {e}"

                    if st.session_state.active_conversation_id is not None:

                        save_message(
                            st.session_state.active_conversation_id,
                            "assistant",
                            error_message,
                            []
                        )

                        st.session_state.messages.append({

                            "role": "assistant",

                            "content": error_message,

                            "sources": []

                        })

                    st.error(error_message)

        # ------------------------------------------
        # DISPLAY COMPARISON CHAT HISTORY
        # ------------------------------------------

        st.divider()

        display_messages()
