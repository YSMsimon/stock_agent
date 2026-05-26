import asyncio

from common.config import Config
from agents.orchestrator import OrchestratorAgent


async def main() -> None:
    config = Config()
    config.validate()
    agent = OrchestratorAgent(config)
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

            print("Agent> ", end="", flush=True)
            async for chunk in agent.stream_chat(user_input):
                print(chunk, end="", flush=True)
            print("\n")
    finally:
        await agent.teardown()


if __name__ == "__main__":
    asyncio.run(main())
