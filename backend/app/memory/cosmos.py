from semantic_kernel.contents import ChatHistory

from app.config import settings


async def load_history(container, user_id: str, session_id: str) -> ChatHistory:
    """Load chat history from Cosmos DB for a session.
    Returns an empty ChatHistory if no session exists yet.
    """
    history = ChatHistory()
    try:
        doc = await container.read_item(item=session_id, partition_key=user_id)
        for turn in doc.get("turns", []):
            if turn["role"] == "user":
                history.add_user_message(turn["content"])
            elif turn["role"] == "assistant":
                history.add_assistant_message(turn["content"])
    except Exception:
        pass  # new session — return empty history
    return history


async def save_history(container, user_id: str, session_id: str, history: ChatHistory) -> None:
    """Persist the current chat history to Cosmos DB.
    Upserts the session document — creates or overwrites.
    """
    turns = []
    for msg in history.messages:
        role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
        if role in ("user", "assistant"):
            turns.append({"role": role, "content": msg.content or ""})

    # Keep only last N turns to stay within Cosmos DB document size limits
    turns = turns[-settings.chat_history_max_turns * 2:]

    doc = {
        "id": session_id,
        "user_id": user_id,
        "session_id": session_id,
        "turns": turns,
        "ttl": settings.session_ttl_seconds,
    }
    await container.upsert_item(doc)
