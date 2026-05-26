from __future__ import annotations

from common.config import Config
from tools.base import Tool


class RunNewsSentimentTool(Tool):
    name = "run_news_sentiment"

    def __init__(self, config: Config, agent) -> None:
        super().__init__(config)
        self._agent = agent

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "run_news_sentiment",
                "description": (
                    "Search for and analyse news, sentiment, and public opinion. "
                    "Use for: recent news articles, analyst upgrades/downgrades, "
                    "Reddit/X/StockTwits sentiment, SEC filings, CEO statements, "
                    "earnings reactions, macro news."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "The search query, "
                                "e.g. 'NVDA earnings reaction and Reddit sentiment May 2026'"
                            ),
                        }
                    },
                    "required": ["query"],
                },
            },
        }

    async def run(self, query: str) -> str:
        print(f"\n[run_news_sentiment] {query!r}")
        self._agent.memory.clear()
        chunks: list[str] = []
        async for chunk in self._agent.stream_chat(query):
            chunks.append(chunk)
        return "".join(chunks)
