from __future__ import annotations
from tavily import AsyncTavilyClient
from common.config import Config
from tools.base import Tool

class WebSearchTool(Tool):
    name = "web_search"
    description = (
        "Search for news, analyst reports, social media sentiment, and market commentary. "
        "Use this for: breaking news, earnings reactions, analyst upgrades/downgrades, "
        "Reddit/X sentiment, SEC filings, CEO statements, and macro analysis. "
        "Use search_depth='advanced' when you need the full article text."
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
                        "query": {
                            "type": "string",
                            "description": (
                                "The search query. Use search operators for precision: "
                                "site:reddit.com, after:YYYY-MM-DD, \"exact phrase\", OR, -site:."
                            ),
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Number of results to return. Default 5, max 10.",
                            "default": 5,
                        },
                        "search_depth": {
                            "type": "string",
                            "enum": ["basic", "advanced"],
                            "description": (
                                "ONLY use advanced when you need to read the full article."
                            ),
                            "default": "basic",
                        },
                        "include_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Restrict results to these domains only. "
                                "Example: [\"reddit.com\", \"x.com\"]"
                            ),
                        },
                        "exclude_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Exclude results from these domains.",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Limit results to the last N days. Default 30.",
                            "default": 30,
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    async def run(self, **kwargs) -> str:
        query: str = kwargs.get("query", "")
        if not query:
            return "Error: query is required."

        max_results: int = int(kwargs.get("max_results", 5))
        search_depth: str = kwargs.get("search_depth", "basic")
        include_domains: list[str] = kwargs.get("include_domains", [])
        exclude_domains: list[str] = kwargs.get("exclude_domains", [])
        days: int = int(kwargs.get("days", 30))

        print(f"\n[web_search] query={query!r}  depth={search_depth}  days={days}  max={max_results}")

        response = await self.client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_domains=include_domains or None,
            exclude_domains=exclude_domains or None,
            days=days,
            include_answer=True,
        )

        output: list[str] = []

        if response.get("answer"):
            output.append(f"**Summary:** {response['answer']}\n")

        for i, result in enumerate(response.get("results", []), 1):
            output.append(
                f"[{i}] {result.get('title', 'No title')}\n"
                f"URL: {result.get('url', '')}\n"
                f"{result.get('content', result.get('snippet', ''))}\n"
            )
        if output:
            return "\n".join(output)
        else:
            return "No results found."