from __future__ import annotations

from common.config import Config
from agents.base import Agent, load_skill
from tools.web_search import WebSearchTool
from tools.web_fetch import WebFetchTool


class NewsSentimentAgent(Agent):

    def __init__(self, config: Config) -> None:
        super().__init__(
            config=config,
            name="NewsSentimentAgent",
            prompt_name="news_sentiment_agent",
            tools=[
                WebSearchTool(config),
                WebFetchTool(config),
            ],
        )
        self.system_prompt += "\n\n---\n\n" + load_skill("search")
