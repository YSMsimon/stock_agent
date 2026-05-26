"""
Direct MCP tool tests — one call per tool, no LLM.
Prints PASS / FAIL and a short preview of the result.
"""
import asyncio
from mcp_client.yfinance_client import YFinanceClient

TESTS = [
    ("get_ticker_info",      {"symbol": "AAPL", "fast": True}),
    ("get_price_history",    {"symbol": "NVDA", "period": "1mo", "interval": "1d"}),
    ("get_financials",       {"symbol": "MSFT", "statement": "income", "period": "yearly"}),
    ("get_earnings",         {"symbol": "GOOGL", "period": "quarterly", "include_dates": True}),
    ("get_analyst_data",     {"symbol": "META", "data_type": "price_targets"}),
    ("get_options",          {"symbol": "TSLA"}),                        # returns expiry dates
    ("get_holders",          {"symbol": "AMZN", "holder_type": "institutional"}),
    ("get_dividends_splits", {"symbol": "AAPL", "data_type": "dividends"}),
    ("get_ticker_calendar",  {"symbol": "NVDA", "data_type": "calendar"}),
    ("download",             {"symbols": ["AAPL", "MSFT", "NVDA"], "period": "5d", "interval": "1d"}),
    ("get_tickers_info",     {"symbols": ["AMD", "INTC", "QCOM"]}),
    ("screen_stocks",        {"query_type": "day_gainers", "count": 5}),
    ("get_market_calendar",  {"calendar_type": "earnings", "limit": 5}),
]

async def main() -> None:
    client = YFinanceClient()
    await client.connect()
    print(f"Connected — {len(client.tools)} tools available\n")
    print(f"{'#':<3} {'Tool':<25} {'Status':<8} Preview")
    print("─" * 90)

    passed = failed = 0
    for i, (name, args) in enumerate(TESTS, 1):
        try:
            result = await client.call_tool(name, args)
            preview = result.replace("\n", " ")[:80]
            status = "PASS" if result and "Error" not in result[:20] else "WARN"
            print(f"{i:<3} {name:<25} {status:<8} {preview}")
            if status == "PASS":
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"{i:<3} {name:<25} {'FAIL':<8} {e}")
            failed += 1

    print("─" * 90)
    print(f"Results: {passed} passed, {failed} failed\n")
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
