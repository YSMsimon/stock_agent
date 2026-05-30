from abc import ABC, abstractmethod
from typing import Any
from common.config import Config


class Tool(ABC):
    name: str
    description: str

    def __init__(self, config: Config) -> None:
        self.config = config

    @abstractmethod
    def schema(self) -> dict:
        """Return the OpenAI function-calling schema for this tool."""
        ...

    @abstractmethod
    async def run(self, **kwargs: Any) -> str:
        """Execute the tool and return a string result."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
