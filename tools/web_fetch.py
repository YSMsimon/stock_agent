from __future__ import annotations
from tavily import AsyncTavilyClient
from common.config import Config
from tools.base import Tool


class WebFetchTool(Tool):
    name = "web_fetch"
    description = (
        "Fetch and extract the full text of a specific news article, analyst report, "
        "SEC filing, Reddit thread, or any URL. Use this when you already have a URL "
        "from web_search results or a known source and need the complete content."
    )

    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.client = AsyncTavilyClient(api_key=config.tavily_api_key)

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": (
                                "The full URL to fetch. "
                                "Examples: an SEC EDGAR filing, a Bloomberg article, "
                                "a Reddit thread, a specific earnings report page."
                            ),
                        },
                    },
                    "required": ["url"],
                },
            },
        }

    async def run(self, **kwargs) -> str:
        url: str = kwargs.get("url", "")
        if not url:
            return "Error: url is required."

        print(f"\n[web_fetch] Fetching: {url}")

        response = await self.client.extract(urls=[url])

        results = response.get("results", [])
        if not results:
            return f"Error: could not extract content from {url}"

        result = results[0]
        title = result.get("title", "")
        content = result.get("raw_content") or result.get("content", "")

        output: list[str] = []
        if title:
            output.append(f"**{title}**\n")
        output.append(f"URL: {url}\n")
        output.append(content)

        return "\n".join(output)
