import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from semantic_kernel.contents import ChatHistory

import app.clients as client_module
from app.agents.orchestrator_agent import OrchestratorAgent
from app.auth import get_current_user
from app.memory.cosmos import load_history, save_history
from app.safety import check_content

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

        # 1. Content Safety — input check
        is_safe, reason = await check_content(request.message, source="input")
        if not is_safe:
            yield f"data: {json.dumps({'delta': f'⚠️ I cannot respond to that message ({reason}).'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        # 2. Load chat history — Cosmos DB or in-memory fallback
        container = await c.get_cosmos_container()
        if container:
            history = await load_history(container, user_id, request.session_id)
        else:
            key = f"{user_id}:{request.session_id}"
            history = _local_history.get(key, ChatHistory())

        # 3. Orchestrator coordinates market research + conversation agents
        orchestrator = OrchestratorAgent(
            user_id=user_id,
            history=history,
            search_client=c.search_client,
            token_provider=c.token_provider,
        )

        # 4. Stream tokens — collect output for safety check
        full_output = ""
        output_safe = True
        try:
            async for token in orchestrator.stream(request.message):
                full_output += token
                yield f"data: {json.dumps({'delta': token})}\n\n"

            # 5. Content Safety — output check (post-stream, non-blocking)
            output_safe, out_reason = await check_content(full_output, source="output")
            if not output_safe:
                yield f"data: {json.dumps({'delta': f'\n\n⚠️ Note: part of this response was flagged ({out_reason}).'})}\n\n"

        finally:
            # 6. Save history only if output was safe
            if output_safe:
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
