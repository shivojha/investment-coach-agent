import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import app.clients as client_module
from app.agent import InvestmentCoachAgent
from app.auth import get_current_user
from app.memory.cosmos import load_history, save_history
from semantic_kernel.contents import ChatHistory

router = APIRouter(tags=["chat"])

# In-memory fallback when Cosmos DB is not configured
_local_history: dict[str, ChatHistory] = {}


class ChatRequest(BaseModel):
    session_id: str
    message: str


@router.post("/chat")
async def chat(
    request: ChatRequest,
    user_id: str = Depends(get_current_user),
):
    async def stream():
        # Read singleton at request time — not at import time
        c = client_module.clients

        # 1. Load chat history — Cosmos DB or in-memory fallback
        container = await c.get_cosmos_container()
        if container:
            history = await load_history(container, user_id, request.session_id)
        else:
            key = f"{user_id}:{request.session_id}"
            history = _local_history.get(key, ChatHistory())

        # 2. Build agent — pass None search_client if AI Search not configured
        agent = InvestmentCoachAgent(
            user_id=user_id,
            history=history,
            search_client=c.search_client,
            token_provider=c.token_provider,
        )

        # 3. Stream tokens to the client as SSE events
        try:
            async for token in agent.stream(request.message):
                yield f"data: {json.dumps({'delta': token})}\n\n"
        finally:
            # 4. Save history — Cosmos DB or in-memory fallback
            if container:
                await save_history(container, user_id, request.session_id, agent.history)
            else:
                key = f"{user_id}:{request.session_id}"
                _local_history[key] = agent.history
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
