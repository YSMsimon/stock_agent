from __future__ import annotations

import asyncio
import json
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.agent import get_agent

router = APIRouter()
logger = logging.getLogger(__name__)

TOOL_LABELS: dict[str, str] = {
    "run_market_data": "Fetching market data",
    "run_news_sentiment": "Searching news & sentiment",
    "write_report": "Writing report",
    # yfinance MCP tools
    "get_ticker_info": "Loading ticker info",
    "get_price_history": "Loading price history",
    "get_financials": "Loading financials",
    "get_earnings": "Loading earnings data",
    "get_analyst_data": "Loading analyst data",
    "get_options": "Loading options chain",
    "get_holders": "Loading holders",
    "get_dividends_splits": "Loading dividends",
    "get_ticker_calendar": "Loading calendar",
    "download": "Downloading price data",
    "get_tickers_info": "Loading tickers info",
    "screen_stocks": "Screening stocks",
    "get_market_calendar": "Loading market calendar",
    # web search
    "web_search": "Searching the web",
    "web_fetch": "Fetching web page",
}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class SwitchMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(default="")


class SwitchRequest(BaseModel):
    messages: list[SwitchMessage] = Field(default_factory=list)


def _tool_label(name: str) -> str:
    return TOOL_LABELS.get(name, name.replace("_", " ").title())


@router.post("/chat")
async def chat(request: ChatRequest):
    agent = get_agent()
    progress_queue: asyncio.Queue = asyncio.Queue()

    # Patch _execute_tool_call to emit progress events
    original_execute = agent._execute_tool_call

    async def patched_execute(tool_call):
        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
        except Exception:
            args = {}
        label = _tool_label(name)
        query = args.get("query") or args.get("ticker") or args.get("symbol") or ""
        await progress_queue.put(
            {"type": "tool_start", "tool": name, "label": label, "query": query}
        )
        result = await original_execute(tool_call)
        await progress_queue.put({"type": "tool_end", "tool": name})
        return result

    agent._execute_tool_call = patched_execute

    async def generate():
        stream_done = False
        stream_exc = None

        async def run_stream():
            nonlocal stream_done, stream_exc
            try:
                async for chunk in agent.stream_chat(request.message):
                    await progress_queue.put({"type": "chunk", "content": chunk})
            except Exception as e:
                logger.exception("Error during chat stream")
                stream_exc = e
            finally:
                stream_done = True
                await progress_queue.put(None)

        task = asyncio.create_task(run_stream())

        try:
            while True:
                item = await progress_queue.get()
                if item is None:
                    break
                yield f"data: {json.dumps(item)}\n\n"
        finally:
            agent._execute_tool_call = original_execute
            await task

        if stream_exc:
            yield f"data: {json.dumps({'type': 'error', 'content': str(stream_exc)})}\n\n"
            return

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/switch")
async def switch_conversation(request: SwitchRequest):
    """Load a stored conversation history into the agent's memory."""
    agent = get_agent()
    agent.memory.clear()
    for msg in request.messages:
        if msg.content:
            agent.memory.add_message(msg.role, msg.content)
    return {"status": "ok", "loaded": len(request.messages)}


@router.post("/clear")
async def clear_history():
    agent = get_agent()
    agent.memory.clear()
    return {"status": "cleared"}


@router.get("/health")
async def health():
    return {"status": "ok"}
