"""
Multi-turn conversation test — simulates a real user session across many exchanges.
Tests: memory carryover, follow-ups, topic switches, context errors, edge cases.
"""
import asyncio
from common.config import Config
from agents.orchestrator import OrchestratorAgent

# One continuous conversation — no memory.clear() between turns
CONVERSATION = [
    # --- warm up ---
    "Hi, what can you do?",

    # --- market data ---
    "What's NVDA's current price and market cap?",
    "What about its PE ratio and 52-week high?",          # follow-up — no ticker mentioned

    # --- topic switch ---
    "Now look at AAPL — how has it performed over the last 3 months?",
    "Compare that to MSFT over the same period",           # follow-up compare

    # --- full analysis flow ---
    "Give me a full analysis of META",
    "no just text",                                        # reply to the .md question

    # --- follow-up on the analysis ---
    "What was the operating margin you just mentioned?",   # memory test
    "What are analysts saying about it?",                  # implicit ticker follow-up

    # --- topic switch to news ---
    "Any recent news on the semiconductor sector?",

    # --- ambiguous / tricky ---
    "What about the other one?",                           # completely ambiguous

    # --- out of scope ---
    "Can you book me a flight to New York?",

    # --- come back to finance ---
    "Ok back to stocks — screen for the top 5 day gainers right now",
]


async def main() -> None:
    config = Config()
    config.validate()
    agent = OrchestratorAgent(config)
    await agent.setup()
    # do NOT clear memory — this is a continuous session
    print(f"Ready. {agent}\n{'═' * 80}\n")

    try:
        for i, msg in enumerate(CONVERSATION, 1):
            print(f"[Turn {i:02d}] You> {msg}")
            print("         Agent> ", end="", flush=True)
            async for chunk in agent.stream_chat(msg):
                print(chunk, end="", flush=True)
            print(f"\n{'─' * 80}\n")
    finally:
        await agent.teardown()


if __name__ == "__main__":
    asyncio.run(main())
