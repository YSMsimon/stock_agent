import asyncio

from common.config import Config
from agents.orchestrator import OrchestratorAgent
from agents.compactor import CompactorAgent


async def main() -> None:
    config = Config()
    config.validate()
    agent = OrchestratorAgent(config)
    compactor = CompactorAgent(config)
    await agent.setup()
    try:
        while True:
            try:
                user_input = input("You> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break

            if not user_input or user_input.lower() == "/exit":
                break

            if user_input.lower() == "/compact":
                messages = agent.memory.messages
                keep = 10
                if len(messages) <= keep:
                    print(
                        f"Agent> Nothing to compact — only {len(messages)} messages in history.\n"
                    )
                    continue
                to_compact = messages[:-keep]
                to_keep = messages[-keep:]
                summary = await compactor.compact(to_compact)
                agent.memory.clear()
                agent.memory.add_message("assistant", f"[Compacted context]\n{summary}")
                for msg in to_keep:
                    agent.memory.add_message(msg["role"], msg.get("content") or "")
                print(
                    f"Agent> Done. {len(to_compact)} messages → 1 summary + {len(to_keep)} kept.\n"
                )
                continue

            print("Agent> ", end="", flush=True)
            async for chunk in agent.stream_chat(user_input):
                print(chunk, end="", flush=True)
            print("\n")
    finally:
        await agent.teardown()


if __name__ == "__main__":
    asyncio.run(main())
