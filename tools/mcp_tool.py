from __future__ import annotations

from common.config import Config
from mcp_client.yfinance_client import YFinanceClient
from tools.base import Tool


class MCPTool(Tool):
    def __init__(self, config: Config, tool_def, client: YFinanceClient) -> None:
        super().__init__(config)
        self.name = tool_def.name
        self._description = tool_def.description or ""
        self._input_schema = tool_def.inputSchema or {
            "type": "object",
            "properties": {},
        }
        self._client = client

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self._description,
                "parameters": self._input_schema,
            },
        }

    async def run(self, **kwargs) -> str:
        print(f"\n[{self.name}] {kwargs}")
        return await self._client.call_tool(self.name, kwargs)
