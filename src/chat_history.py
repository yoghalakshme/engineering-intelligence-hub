
import sqlite3
import json
from pathlib import Path


# =====================================
# DATABASE CONFIGURATION
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "chat_history.db"


# =====================================
# DATABASE CONNECTION
# =====================================

def get_connection():

    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# =====================================
# CREATE DATABASE TABLES
# =====================================

def init_db():

    with get_connection() as conn:

        # Create conversations table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                title TEXT NOT NULL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ---------------------------------
        # DATABASE MIGRATION
        # Add mode column if it doesn't exist
        # ---------------------------------

        columns = conn.execute(
            "PRAGMA table_info(conversations)"
        ).fetchall()

        column_names = [
            column["name"] for column in columns
        ]

        if "mode" not in column_names:

            conn.execute("""
                ALTER TABLE conversations
                ADD COLUMN mode TEXT NOT NULL
                DEFAULT 'Ask Questions'
            """)

        # Create messages table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                conversation_id INTEGER NOT NULL,

                role TEXT NOT NULL,

                content TEXT NOT NULL,

                sources TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (conversation_id)
                REFERENCES conversations(id)
                ON DELETE CASCADE
            )
        """)


# =====================================
# CREATE NEW CONVERSATION
# =====================================

def create_conversation(
    title="New Chat",
    mode="Ask Questions"
):

    if mode not in ["Ask Questions", "Compare Documents"]:
        raise ValueError("Invalid conversation mode.")

    with get_connection() as conn:

        cursor = conn.execute(
            """
            INSERT INTO conversations (title, mode)
            VALUES (?, ?)
            """,
            (title, mode)
        )

        return cursor.lastrowid


# =====================================
# SAVE CHAT MESSAGE
# =====================================

def save_message(
    conversation_id,
    role,
    content,
    sources=None
):

    sources_json = json.dumps(sources or [])

    with get_connection() as conn:

        conn.execute(
            """
            INSERT INTO messages
            (conversation_id, role, content, sources)
            VALUES (?, ?, ?, ?)
            """,
            (
                conversation_id,
                role,
                content,
                sources_json
            )
        )

        conn.execute(
            """
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (conversation_id,)
        )


# =====================================
# GET ALL CONVERSATIONS
# =====================================

def get_conversations():

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT *
            FROM conversations
            ORDER BY updated_at DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]


# =====================================
# GET MESSAGES OF A CONVERSATION
# =====================================

def get_messages(conversation_id):

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT *
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,)
        ).fetchall()

        messages = []

        for row in rows:

            message = dict(row)

            message["sources"] = json.loads(
                message["sources"] or "[]"
            )

            messages.append(message)

        return messages


# =====================================
# DELETE A CONVERSATION
# =====================================

def delete_conversation(conversation_id):

    with get_connection() as conn:

        conn.execute(
            """
            DELETE FROM conversations
            WHERE id = ?
            """,
            (conversation_id,)
        )


# =====================================
# INITIALIZE DATABASE
# =====================================

init_db()
