import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from semantic_kernel.contents import ChatHistory

import app.clients as client_module
from app.agents.orchestrator_agent import OrchestratorAgent
from app.auth import get_current_user
from app.memory.cosmos import load_history, save_history

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
        c = client_module.clients

        # 1. Load chat history — Cosmos DB or in-memory fallback
        container = await c.get_cosmos_container()
        if container:
            history = await load_history(container, user_id, request.session_id)
        else:
            key = f"{user_id}:{request.session_id}"
            history = _local_history.get(key, ChatHistory())

        # 2. Orchestrator coordinates market research + conversation agents
        orchestrator = OrchestratorAgent(
            user_id=user_id,
            history=history,
            search_client=c.search_client,
            token_provider=c.token_provider,
        )

        # 3. Stream tokens to the client as SSE events
        try:
            async for token in orchestrator.stream(request.message):
                yield f"data: {json.dumps({'delta': token})}\n\n"
        finally:
            # 4. Save updated history — Cosmos DB or in-memory fallback
            final_history = getattr(orchestrator, "history", history)
            if container:
                await save_history(container, user_id, request.session_id, final_history)
            else:
                key = f"{user_id}:{request.session_id}"
                _local_history[key] = final_history
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
