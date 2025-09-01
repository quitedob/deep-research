import asyncio
import uuid
from typing import Dict, List, Any


class SessionStore:
    """简单的会话与研究结果存储（进程内）。
    生产可替换为 Redis/DB。
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._chat_sessions: Dict[str, List[Dict[str, str]]] = {}
        self._research_reports: Dict[str, Dict[str, Any]] = {}

    async def ensure_session(self, session_id: str | None) -> str:
        sid = session_id or uuid.uuid4().hex
        async with self._lock:
            self._chat_sessions.setdefault(sid, [])
        return sid

    async def list_sessions(self) -> List[str]:
        async with self._lock:
            return list(self._chat_sessions.keys())

    async def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        async with self._lock:
            return list(self._chat_sessions.get(session_id, []))

    async def append_message(self, session_id: str, role: str, content: str) -> None:
        async with self._lock:
            self._chat_sessions.setdefault(session_id, []).append({"role": role, "content": content})

    async def clear_all(self) -> None:
        async with self._lock:
            self._chat_sessions.clear()

    # Research results
    async def set_research_report(self, session_id: str, query: str, report: str) -> None:
        async with self._lock:
            self._research_reports[session_id] = {"session_id": session_id, "query": query, "report": report}

    async def get_research_report(self, session_id: str) -> Dict[str, Any] | None:
        async with self._lock:
            return self._research_reports.get(session_id)


store = SessionStore()


