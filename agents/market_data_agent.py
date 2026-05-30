from __future__ import annotations

from common.config import Config
from agents.base import Agent
from mcp_client.yfinance_client import YFinanceClient
from tools.mcp_tool import MCPTool

_TOOL_NAMES = {
    # ── Single-ticker ──────────────────────────────────────────────────────────
    "get_ticker_info",  # price, market cap, PE, 52-week high/low
    "get_price_history",  # OHLCV history (single ticker)
    "get_financials",  # income / balance sheet / cash flow
    "get_earnings",  # EPS history + upcoming earnings dates
    "get_analyst_data",  # price targets, recommendations, upgrades
    "get_options",  # options chain (calls & puts)
    "get_holders",  # institutional, insider, mutual fund holders
    "get_dividends_splits",  # dividend history & stock splits
    "get_ticker_calendar",  # calendar events, news, SEC filings
    # ── Multi-ticker (batch) ───────────────────────────────────────────────────
    "download",  # OHLCV for many tickers at once (efficient)
    "get_tickers_info",  # info for many tickers at once (efficient)
    # ── Market-wide ───────────────────────────────────────────────────────────
    "screen_stocks",  # 8 predefined screens (most active, gainers, …)
    "get_market_calendar",  # earnings / IPO / FOMC / splits calendar
}


class MarketDataAgent(Agent):
    def __init__(self, config: Config, client: YFinanceClient) -> None:
        tools = [
            MCPTool(config, t, client) for t in client.tools if t.name in _TOOL_NAMES
        ]
        super().__init__(
            config=config,
            name="MarketDataAgent",
            prompt_name="market_data_agent",
            tools=tools,
        )
