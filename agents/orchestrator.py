from __future__ import annotations

from common.config import Config
from agents.base import Agent, load_skill


class OrchestratorAgent(Agent):
    def __init__(self, config: Config) -> None:
        super().__init__(
            config=config,
            name="OrchestratorAgent",
            prompt_name="orchestrator",
            tools=[],
        )
        self.system_prompt += "\n\n---\n\n" + load_skill("report")

    async def setup(self) -> None:
        from mcp_client.yfinance_client import YFinanceClient
        from agents.market_data_agent import MarketDataAgent
        from agents.news_sentiment_agent import NewsSentimentAgent
        from tools.run_market_data import RunMarketDataTool
        from tools.run_news_sentiment import RunNewsSentimentTool
        from tools.write_report import WriteReportTool

        self._yfinance_client = YFinanceClient()
        await self._yfinance_client.connect()

        market_data = MarketDataAgent(self.config, self._yfinance_client)
        news_sentiment = NewsSentimentAgent(self.config)

        self.tools = [
            RunMarketDataTool(self.config, market_data),
            RunNewsSentimentTool(self.config, news_sentiment),
            WriteReportTool(self.config, self._yfinance_client),
        ]
        self._tool_map = {t.name: t for t in self.tools}

    async def teardown(self) -> None:
        client = getattr(self, "_yfinance_client", None)
        if client:
            await client.close()

    def __repr__(self) -> str:
        return f"OrchestratorAgent(tools={[t.name for t in self.tools]})"
