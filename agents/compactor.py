from __future__ import annotations

from agents.base import Agent
from common.config import Config


class CompactorAgent(Agent):
    """Compresses a conversation history into a dense summary."""

    def __init__(self, config: Config) -> None:
        super().__init__(
            config=config,
            name="CompactorAgent",
            prompt_name="compactor",
            tools=[],
        )

    async def compact(self, messages: list[dict]) -> str:
        formatted = self._format_messages(messages)
        summary_chunks: list[str] = []
        async for chunk in self.stream_chat(formatted):
            summary_chunks.append(chunk)
        return "".join(summary_chunks).strip()

    def _format_messages(self, messages: list[dict]) -> str:
        lines: list[str] = ["CONVERSATION:"]
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "tool":
                continue
            if not content:
                continue
            lines.append(f"{role}: {content}")
        return "\n".join(lines)
