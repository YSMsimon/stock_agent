"""5 full-analysis end-to-end tests — orchestrator decides which tools to call"""

import asyncio
from common.config import Config
from agents.orchestrator import OrchestratorAgent

TESTS = [
    "Give me a full analysis of NVDA",
    "Analyse META — I want valuation, recent earnings, and current sentiment",
    "Full research report on MSFT",
    "Is TSLA a buy right now? Give me a complete breakdown",
    "Deep dive on AMD vs INTC — which is the better position today?",
]


async def main() -> None:
    config = Config()
    config.validate()
    agent = OrchestratorAgent(config)
    await agent.setup()
    agent.memory.clear()
    print(f"Ready. {agent}\n{'═' * 80}\n")

    try:
        for i, prompt in enumerate(TESTS, 1):
            print(f"TEST {i}: {prompt}")
            print("─" * 80)
            print("Agent> ", end="", flush=True)
            async for chunk in agent.stream_chat(prompt):
                print(chunk, end="", flush=True)
            print(f"\n\n{'═' * 80}\n")
            agent.memory.clear()  # fresh context each test
    finally:
        await agent.teardown()


if __name__ == "__main__":
    asyncio.run(main())
