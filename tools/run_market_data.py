from __future__ import annotations

from common.config import Config
from tools.base import Tool


class RunMarketDataTool(Tool):
    name = "run_market_data"

    def __init__(self, config: Config, agent) -> None:
        super().__init__(config)
        self._agent = agent

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "run_market_data",
                "description": (
                    "Fetch live market data using yfinance. Use for: current price, "
                    "market cap, PE ratio, 52-week range, price history (OHLCV), "
                    "financial statements (income / balance / cash flow), earnings, "
                    "analyst price targets, options chain, holders, dividends, "
                    "stock screens, and earnings/IPO/FOMC calendar."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "The specific data request to fulfil, "
                                "e.g. 'Get NVDA current price, market cap, and 52-week high'"
                            ),
                        }
                    },
                    "required": ["query"],
                },
            },
        }

    async def run(self, query: str) -> str:  # type: ignore[override]
        print(f"\n[run_market_data] {query!r}")
        self._agent.memory.clear()
        chunks: list[str] = []
        async for chunk in self._agent.stream_chat(query):
            chunks.append(chunk)
        return "".join(chunks)
