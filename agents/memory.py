from __future__ import annotations
import json
from pathlib import Path

MEMORY_DIR = ".stock_agent"


class MemorySystem:
    def __init__(self, name: str, base_dir: str | Path = ".") -> None:
        self.name = name
        self.memory_path: Path = Path(base_dir) / MEMORY_DIR / f"{name}.json"
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)

        self.messages: list[dict] = []
        self._load()

    def add_message(self, role: str, content: str) -> None:
        msg: dict = {"role": role, "content": content}
        self.messages.append(msg)
        self._save()

    def get_messages_for_llm(self) -> list[dict]:
        return list(self.messages)

    def clear(self) -> None:
        self.messages = []
        self._save()

    def _save(self) -> None:
        self.memory_path.write_text(
            json.dumps(self.messages, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load(self) -> None:
        if self.memory_path.exists() and self.memory_path.stat().st_size > 0:
            try:
                data = json.loads(self.memory_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self.messages = data
            except (json.JSONDecodeError, ValueError):
                self.messages = []
