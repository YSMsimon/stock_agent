"""5 end-to-end tests through OrchestratorAgent → MarketDataAgent → yfinance MCP"""
import asyncio
from common.config import Config
from agents.orchestrator import OrchestratorAgent

TESTS = [
    "What is NVDA's current price, market cap, and 52-week high?",
    "Compare AMD, INTC, and QCOM — give me their current price, PE ratio, and market cap",
    "Show me META's annual income statement for the last 3 years",
    "Use the market calendar tool to fetch upcoming earnings announcements this week",
    "How has TSLA's stock performed over the last month? Show key OHLCV data",
]

async def main() -> None:
    config = Config()
    config.validate()
    agent = OrchestratorAgent(config)
    await agent.setup()
    # clear stale orchestrator memory so previous test runs don't bleed in
    agent.memory.clear()
    print(f"Ready. {agent}\n{'═'*80}\n")

    try:
        for i, prompt in enumerate(TESTS, 1):
            print(f"TEST {i}: {prompt}")
            print("─" * 80)
            print("Agent> ", end="", flush=True)
            async for chunk in agent.stream_chat(prompt):
                print(chunk, end="", flush=True)
            print(f"\n\n{'═'*80}\n")
    finally:
        await agent.teardown()

if __name__ == "__main__":
    asyncio.run(main())
