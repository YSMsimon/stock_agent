from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.agent import get_agent

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


@router.post("/chat")
async def chat(request: ChatRequest):
    agent = get_agent()

    async def generate():
        try:
            async for chunk in agent.stream_chat(request.message):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        except Exception as e:
            logger.exception("Error during chat stream")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/clear")
async def clear_history():
    agent = get_agent()
    agent.memory.clear()
    return {"status": "cleared"}


@router.get("/health")
async def health():
    return {"status": "ok"}
