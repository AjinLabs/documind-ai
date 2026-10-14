"""
DocuMind AI — SQLite Database Layer
Persistent storage for Documents, Chunks, Collections, Conversations,
Claims, Entities, Relationships, Research Tasks, Version Diff, and Audit Logs.
"""
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import SQLITE_DB_PATH

logger = logging.getLogger(__name__)

def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection configured with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(str(SQLITE_DB_PATH), timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes all required enterprise tables and indexes."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Collections Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS collections (
            name TEXT PRIMARY KEY,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Documents Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            content_hash TEXT NOT NULL UNIQUE,
            collection_name TEXT DEFAULT 'General',
            page_count INTEGER DEFAULT 0,
            file_size_bytes INTEGER DEFAULT 0,
            tags TEXT DEFAULT '',
            is_scanned INTEGER DEFAULT 0,
            extraction_status TEXT DEFAULT 'indexed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (collection_name) REFERENCES collections(name) ON DELETE SET DEFAULT
        );
        """)

        # Chunks Table with Page-level Provenance
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            page_number INTEGER NOT NULL,
            text_content TEXT NOT NULL,
            token_count INTEGER DEFAULT 0,
            embedding_model TEXT,
            metadata_json TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_page ON chunks(document_id, page_number);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id);")

        # Conversations Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            session_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            collection_name TEXT DEFAULT 'General',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Messages Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            citations_json TEXT DEFAULT '[]',
            model_used TEXT DEFAULT 'Extractive',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES conversations(session_id) ON DELETE CASCADE
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);")

        # Claims & Contradiction Evidence Ledger
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY,
            claim_text TEXT NOT NULL,
            document_id TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            supporting_excerpt TEXT NOT NULL,
            verification_status TEXT DEFAULT 'requires_review',
            related_claims_json TEXT DEFAULT '[]',
            contradictions_json TEXT DEFAULT '[]',
            reviewer_notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
        );
        """)

        # Knowledge Graph: Entities
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            entity_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            canonical_name TEXT NOT NULL,
            document_ids_json TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_canonical ON entities(canonical_name);")

        # Knowledge Graph: Relationships
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationships (
            rel_id TEXT PRIMARY KEY,
            source_entity TEXT NOT NULL,
            target_entity TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            document_id TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            evidence_text TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
        );
        """)

        # Document Versions Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_versions (
            version_id TEXT PRIMARY KEY,
            base_document_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            filename TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            diff_summary_json TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Bounded Research Tasks Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_tasks (
            task_id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            collection_name TEXT DEFAULT 'All',
            status TEXT DEFAULT 'pending',
            plan_json TEXT DEFAULT '[]',
            logs_json TEXT DEFAULT '[]',
            findings_json TEXT DEFAULT '[]',
            report_markdown TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
        """)

        # RAG Evaluation Experiments
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_records (
            eval_id TEXT PRIMARY KEY,
            experiment_name TEXT NOT NULL,
            dataset_name TEXT NOT NULL,
            retrieval_strategy TEXT NOT NULL,
            embedding_model TEXT NOT NULL,
            metrics_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Immutable Audit Event Log
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            details_json TEXT DEFAULT '{}',
            severity TEXT DEFAULT 'INFO',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Ensure default 'General' collection exists
        cursor.execute("INSERT OR IGNORE INTO collections (name, description) VALUES ('General', 'Default collection for indexed documents');")
        conn.commit()


# --- Document Helpers ---

def get_document_by_hash(content_hash: str) -> Optional[Dict[str, Any]]:
    """Checks for existing document with identical content hash (duplicate detection)."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM documents WHERE content_hash = ?", (content_hash,)).fetchone()
        return dict(row) if row else None


def insert_document(doc: Dict[str, Any]):
    """Inserts a new document record."""
    with get_connection() as conn:
        conn.execute("""
        INSERT INTO documents (document_id, filename, content_hash, collection_name, page_count, file_size_bytes, tags, is_scanned, extraction_status)
        VALUES (:document_id, :filename, :content_hash, :collection_name, :page_count, :file_size_bytes, :tags, :is_scanned, :extraction_status)
        """, doc)
        conn.commit()


def get_all_documents(collection: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all documents, optionally filtered by collection."""
    with get_connection() as conn:
        if collection and collection != "All":
            rows = conn.execute("SELECT * FROM documents WHERE collection_name = ? ORDER BY created_at DESC", (collection,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single document by its ID."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,)).fetchone()
        return dict(row) if row else None


def delete_document(document_id: str):
    """Deletes a document and its cascading chunks, claims, relationships."""
    with get_connection() as conn:
        conn.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
        conn.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
        conn.execute("DELETE FROM claims WHERE document_id = ?", (document_id,))
        conn.execute("DELETE FROM relationships WHERE document_id = ?", (document_id,))
        conn.commit()


# --- Chunks Helpers ---

def insert_chunks(chunks: List[Dict[str, Any]]):
    """Batch inserts text chunks."""
    with get_connection() as conn:
        conn.executemany("""
        INSERT INTO chunks (chunk_id, document_id, chunk_index, page_number, text_content, token_count, embedding_model, metadata_json)
        VALUES (:chunk_id, :document_id, :chunk_index, :page_number, :text_content, :token_count, :embedding_model, :metadata_json)
        """, chunks)
        conn.commit()


def get_chunks_for_document(document_id: str) -> List[Dict[str, Any]]:
    """Returns all chunks for a document ordered by page and index."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index ASC", (document_id,)).fetchall()
        return [dict(r) for r in rows]


def get_all_chunks(collection: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all chunks across indexed documents, optionally filtered by collection."""
    with get_connection() as conn:
        if collection and collection != "All":
            rows = conn.execute("""
            SELECT c.*, d.filename, d.collection_name
            FROM chunks c
            JOIN documents d ON c.document_id = d.document_id
            WHERE d.collection_name = ?
            ORDER BY c.document_id, c.chunk_index
            """, (collection,)).fetchall()
        else:
            rows = conn.execute("""
            SELECT c.*, d.filename, d.collection_name
            FROM chunks c
            JOIN documents d ON c.document_id = d.document_id
            ORDER BY c.document_id, c.chunk_index
            """).fetchall()
        return [dict(r) for r in rows]


def get_chunk_by_id(chunk_id: str) -> Optional[Dict[str, Any]]:
    """Returns a specific chunk with document metadata."""
    with get_connection() as conn:
        row = conn.execute("""
        SELECT c.*, d.filename, d.collection_name
        FROM chunks c
        JOIN documents d ON c.document_id = d.document_id
        WHERE c.chunk_id = ?
        """, (chunk_id,)).fetchone()
        return dict(row) if row else None


# --- Collections Helpers ---

def get_collections() -> List[str]:
    """Returns list of distinct collection names."""
    with get_connection() as conn:
        rows = conn.execute("SELECT name FROM collections ORDER BY name ASC").fetchall()
        return [r["name"] for r in rows]


def add_collection(name: str, description: str = ""):
    """Creates a new collection."""
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO collections (name, description) VALUES (?, ?)", (name.strip(), description.strip()))
        conn.commit()


# --- Audit Log Helpers ---

def log_audit_event(event_type: str, details: Dict[str, Any], severity: str = "INFO"):
    """Records a security or administrative audit event."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO audit_events (event_type, details_json, severity) VALUES (?, ?, ?)",
                (event_type, json.dumps(details), severity)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to write audit event: {e}")


def get_audit_events(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves recent audit events."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM audit_events ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


# Initialize schema on module import
init_db()
