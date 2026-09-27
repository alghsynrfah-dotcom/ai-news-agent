import uuid


_sessions: dict[str, dict] = {}


def create_session() -> str:
    thread_id = str(uuid.uuid4())

    _sessions[thread_id] = {
        "messages": [],
        "sources": [],
        "tools_used": [],
    }

    return thread_id


def get_session(thread_id: str) -> dict | None:
    return _sessions.get(thread_id)


def update_session(thread_id: str, data: dict) -> None:
    if thread_id not in _sessions:
        _sessions[thread_id] = {
            "messages": [],
            "sources": [],
            "tools_used": [],
        }

    _sessions[thread_id].update(data)


def clear_session(thread_id: str) -> None:
    _sessions.pop(thread_id, None)