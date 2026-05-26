from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import AsyncGenerator, Optional, TYPE_CHECKING

from openai import AsyncOpenAI

from common.config import Config
from agents.memory import MemorySystem

if TYPE_CHECKING:
    from tools.base import Tool

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
SKILLS_DIR  = Path(__file__).parent.parent / "skills"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"System prompt not found: {path}\n"
            f"Create prompts/{name}.md to define this agent's system prompt."
        )
    return path.read_text(encoding="utf-8").strip()


def load_skill(name: str) -> str:
    path = SKILLS_DIR / name / "SKILL.md"
    if not path.exists():
        raise FileNotFoundError(
            f"Skill not found: {path}\n"
            f"Create skills/{name}/SKILL.md to define this skill."
        )
    content = path.read_text(encoding="utf-8").strip()
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:].strip()
    return content


class Agent:
    def __init__(
        self,
        config: Config,
        name: str = "StockAgent",
        prompt_name: str = "stock_agent",
        tools: Optional[list[Tool]] = None,
    ) -> None:
        self.name      = name
        self.config    = config
        self.tools     = tools or []
        self._tool_map = {t.name: t for t in self.tools}

        self.system_prompt: str = load_prompt(prompt_name)

        self.client = AsyncOpenAI(
            api_key=config.llm_api_key,
            base_url=config.llm_api_url,
        )
        self.memory = MemorySystem(name=prompt_name)

    async def _execute_tool_call(self, tool_call) -> dict:
        tool_name = tool_call.function.name
        try:
            tool_args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            tool_args = {}

        tool = self._tool_map.get(tool_name)
        if tool:
            result = await tool.run(**tool_args)
        else:
            result = f"Error: tool '{tool_name}' not found."

        return {
            "role":         "tool",
            "tool_call_id": tool_call.id,
            "content":      result,
        }

    _MAX_TOOL_ITERATIONS = 10

    async def _run_tool_loop(self, messages: list[dict]) -> list[dict]:
        tool_schemas = [t.schema() for t in self.tools]

        for _ in range(self._MAX_TOOL_ITERATIONS):
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                tools=tool_schemas,
                tool_choice="auto",
                extra_body={"thinking": {"type": "disabled"}},
            )

            choice = response.choices[0]
            content = choice.message.content or ""

            if choice.finish_reason != "tool_calls" or "<｜｜DSML｜｜" in content:
                return messages

            messages.append({
                "role":    "assistant",
                "content": content,
                "tool_calls": [
                    {
                        "id":   tc.id,
                        "type": tc.type,
                        "function": {
                            "name":      tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ],
            })

            results = await asyncio.gather(
                *[self._execute_tool_call(tc) for tc in choice.message.tool_calls]
            )
            for result_msg in results:
                messages.append(result_msg)

        return messages

    async def stream_chat(self, user_message: str) -> AsyncGenerator[str, None]:
        self.memory.add_message("user", user_message)

        messages: list[dict] = [{"role": "system", "content": self.system_prompt}]
        for msg in self.memory.get_messages_for_llm():
            messages.append(msg)

        if self.tools:
            messages = await self._run_tool_loop(messages)

        stream = await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            stream=True,
            extra_body={"thinking": {"type": "disabled"}},
        )

        chunks: list[str] = []
        async for event in stream:
            delta = event.choices[0].delta
            if delta.content:
                chunks.append(delta.content)
                yield delta.content

        self.memory.add_message("assistant", "".join(chunks))

    @property
    def history(self) -> list[dict]:
        return self.memory.messages

    def __repr__(self) -> str:
        return (
            f"Agent(name={self.name!r}, model={self.config.model!r}, "
            f"tools={[t.name for t in self.tools]})"
        )
