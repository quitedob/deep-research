"""Persistence for user interactions, always scoped by authenticated identity."""

from datetime import datetime, timedelta
import json
import secrets
import uuid

from backend.repositories.base import BaseDAO


class InteractionDAO(BaseDAO):
    async def owned_message(self, message_id, user_id):
        return await self.fetch_one(
            """SELECT m.* FROM chat_messages m JOIN chat_sessions s ON s.id = m.session_id
               WHERE m.id = $1 AND s.user_id = $2""", (message_id, user_id),
        )

    async def report_message(self, user_id, message_id, reason, description):
        return await self.fetch_one(
            """INSERT INTO message_reports (user_id, message_id, reason, description)
               SELECT s.user_id, m.id, $3, $4 FROM chat_messages m
               JOIN chat_sessions s ON s.id = m.session_id WHERE m.id = $2 AND s.user_id = $1
               RETURNING id, created_at""", (user_id, message_id, reason, description),
        )

    async def create_share(self, user_id, session_id, title, description, expire_days):
        # Snapshot selection and persistence happen in one statement.
        return await self.fetch_one(
            """INSERT INTO conversation_shares (id, user_id, session_id, snapshot, expires_at)
               SELECT $1, s.user_id, s.id,
                   jsonb_build_object('title', COALESCE(NULLIF($4, ''), s.title),
                       'description', $5::text, 'messages', COALESCE((
                           SELECT jsonb_agg(jsonb_build_object('role', m.role,
                               'content', m.content, 'timestamp', m.created_at) ORDER BY m.id)
                           FROM chat_messages m WHERE m.session_id = s.id AND m.role IN ('user','assistant')
                       ), '[]'::jsonb)), $6
               FROM chat_sessions s WHERE s.id = $2 AND s.user_id = $3
               RETURNING id, created_at, expires_at""",
            (secrets.token_urlsafe(32), session_id, user_id, title, description,
             datetime.utcnow() + timedelta(days=expire_days)),
        )

    async def get_public_share(self, share_id):
        row = await self.fetch_one(
            """UPDATE conversation_shares SET view_count = view_count + 1
               WHERE id = $1 AND expires_at > (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
               RETURNING snapshot, created_at, expires_at, view_count""", (share_id,),
        )
        if row:
            snapshot = row.pop("snapshot")
            return {**(json.loads(snapshot) if isinstance(snapshot, str) else snapshot), **row}
        return None

    async def revoke_share(self, share_id, user_id):
        return await self.fetch_one(
            "DELETE FROM conversation_shares WHERE id = $1 AND user_id = $2 RETURNING id",
            (share_id, user_id),
        )

    async def save_feedback(self, user_id, message_id, rating, comment):
        return await self.fetch_one(
            """INSERT INTO message_feedback (user_id, message_id, rating, comment)
               SELECT s.user_id, m.id, $3, $4 FROM chat_messages m JOIN chat_sessions s ON s.id = m.session_id
               WHERE m.id = $2 AND s.user_id = $1
               ON CONFLICT (user_id, message_id) DO UPDATE SET rating = EXCLUDED.rating, comment = EXCLUDED.comment
               RETURNING user_id, message_id, rating, comment""", (user_id, message_id, rating, comment),
        )

    async def get_feedback(self, user_id, message_id):
        return await self.fetch_all(
            "SELECT user_id, message_id, rating, comment FROM message_feedback WHERE user_id = $1 AND message_id = $2",
            (user_id, message_id),
        )

    async def delete_feedback(self, user_id, message_id):
        await self.execute_query(
            "DELETE FROM message_feedback WHERE user_id = $1 AND message_id = $2", (user_id, message_id),
        )

    async def save_document(self, user_id, filename, file_type, content, original_bytes):
        return await self.fetch_one(
            """INSERT INTO uploaded_documents (id, user_id, filename, file_type, content, original_bytes)
               VALUES ($1, $2, $3, $4, $5, $6) RETURNING id, filename, file_type, content, created_at""",
            (str(uuid.uuid4()), user_id, filename, file_type, content, original_bytes),
        )

    async def get_document(self, document_id, user_id):
        return await self.fetch_one(
            "SELECT id, filename, file_type, content, created_at FROM uploaded_documents WHERE id = $1 AND user_id = $2",
            (document_id, user_id),
        )

    async def list_documents(self, user_id, limit, offset):
        return await self.fetch_all(
            """SELECT id, filename, file_type, LEFT(content, 500) AS content, created_at
               FROM uploaded_documents WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3""",
            (user_id, limit, offset),
        )

    async def delete_document(self, document_id, user_id):
        return await self.fetch_one(
            "DELETE FROM uploaded_documents WHERE id = $1 AND user_id = $2 RETURNING id", (document_id, user_id),
        )

    async def search_documents(self, query, user_id, limit):
        return await self.fetch_all(
            """SELECT id, filename, ts_headline('simple', content, plainto_tsquery('simple', $1)) AS content
               FROM uploaded_documents WHERE user_id = $2
               AND to_tsvector('simple', content) @@ plainto_tsquery('simple', $1)
               ORDER BY ts_rank(to_tsvector('simple', content), plainto_tsquery('simple', $1)) DESC LIMIT $3""",
            (query, user_id, limit),
        )

    async def session_evidence(self, session_id, user_id, limit, offset):
        return await self.fetch_all(
            """SELECT c.*, COALESCE(f.used_in_response, FALSE) AS used_in_response,
                      COALESCE(f.verified_by_user, FALSE) AS verified_by_user
               FROM research_citations c JOIN research_sessions s ON s.id = c.session_id
               LEFT JOIN evidence_flags f ON f.citation_id = c.id
               WHERE c.session_id = $1 AND s.user_id = $2 ORDER BY c.id LIMIT $3 OFFSET $4""",
            (session_id, user_id, limit, offset),
        )

    async def update_evidence(self, citation_id, user_id, *, used=None, verified=None):
        return await self.fetch_one(
            """INSERT INTO evidence_flags (citation_id, used_in_response, verified_by_user)
               SELECT c.id, COALESCE($3, FALSE), COALESCE($4, FALSE) FROM research_citations c
               JOIN research_sessions s ON s.id = c.session_id WHERE c.id = $1 AND s.user_id = $2
               ON CONFLICT (citation_id) DO UPDATE
               SET used_in_response = COALESCE($3, evidence_flags.used_in_response),
                   verified_by_user = COALESCE($4, evidence_flags.verified_by_user)
               RETURNING *""", (citation_id, user_id, used, verified),
        )

    async def evidence_stats(self, user_id, days):
        return await self.fetch_one(
            """SELECT COUNT(*) AS total_evidence,
                      COUNT(*) FILTER (WHERE f.verified_by_user) AS verified_evidence
               FROM research_citations c JOIN research_sessions s ON s.id = c.session_id
               LEFT JOIN evidence_flags f ON f.citation_id = c.id
               WHERE s.user_id = $1 AND c.created_at >= $2""",
            (user_id, datetime.utcnow() - timedelta(days=days)),
        )
