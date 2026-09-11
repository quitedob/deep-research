"""Additive tables for the existing sharing, feedback, upload, and evidence UI."""

INTERACTION_TABLES = {
    "conversation_shares": """
        CREATE TABLE IF NOT EXISTS conversation_shares (
            id TEXT PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            session_id VARCHAR(255) NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
            snapshot JSONB NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            view_count INTEGER NOT NULL DEFAULT 0
        );
    """,
    "message_reports": """
        CREATE TABLE IF NOT EXISTS message_reports (
            id BIGSERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            message_id INTEGER NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
            reason TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "message_feedback": """
        CREATE TABLE IF NOT EXISTS message_feedback (
            user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            message_id INTEGER NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
            rating INTEGER NOT NULL CHECK (rating IN (-1, 1)),
            comment TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, message_id)
        );
    """,
    "uploaded_documents": """
        CREATE TABLE IF NOT EXISTS uploaded_documents (
            id TEXT PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            content TEXT NOT NULL,
            original_bytes BYTEA NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_uploaded_documents_user ON uploaded_documents(user_id);
    """,
    "evidence_flags": """
        CREATE TABLE IF NOT EXISTS evidence_flags (
            citation_id INTEGER PRIMARY KEY REFERENCES research_citations(id) ON DELETE CASCADE,
            used_in_response BOOLEAN NOT NULL DEFAULT FALSE,
            verified_by_user BOOLEAN NOT NULL DEFAULT FALSE
        );
    """,
}
