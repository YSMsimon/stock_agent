from __future__ import annotations

from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_SERVER_CMD = "python3"
_SERVER_ARGS = [
    "-c",
    "import asyncio; from yfinance_mcp.server import mcp; asyncio.run(mcp.run_stdio_async())",
]


class YFinanceClient:

    def __init__(self) -> None:
        self._session: ClientSession | None = None
        self._exit_stack: AsyncExitStack | None = None
        self.tools: list = []

    async def connect(self) -> None:
        self._exit_stack = AsyncExitStack()
        params = StdioServerParameters(command=_SERVER_CMD, args=_SERVER_ARGS)
        r, w = await self._exit_stack.enter_async_context(stdio_client(params))
        self._session = await self._exit_stack.enter_async_context(ClientSession(r, w))
        await self._session.initialize()
        result = await self._session.list_tools()
        self.tools = result.tools

    async def call_tool(self, name: str, args: dict) -> str:
        if self._session is None:
            return "Error: YFinanceClient not connected."
        result = await self._session.call_tool(name, args)
        texts = [c.text for c in result.content if hasattr(c, "text")]
        return "\n".join(texts) if texts else "No data returned."

    async def close(self) -> None:
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
            self._session = None
