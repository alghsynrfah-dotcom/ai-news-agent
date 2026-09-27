import uuid


_sessions: dict[str, dict] = {}


def create_session() -> str:
    thread_id = str(uuid.uuid4())

    _sessions[thread_id] = {
        "messages": [],
        "sources": [],
        "tools_used": [],
        "feedback": None,
        "pending_email": None,
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
            "feedback": None,
            "pending_email": None,
        }

    _sessions[thread_id].update(data)
def set_pending_email(thread_id: str, email_data: dict) -> None:
    update_session(
        thread_id,
        {"pending_email": email_data},
    )


def get_pending_email(thread_id: str) -> dict | None:
    session = get_session(thread_id)

    if not session:
        return None

    return session.get("pending_email")


def clear_pending_email(thread_id: str) -> None:
    update_session(
        thread_id,
        {"pending_email": None},
    )

def clear_session(thread_id: str) -> None:
    _sessions.pop(thread_id, None)