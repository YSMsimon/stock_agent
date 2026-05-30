from __future__ import annotations

from common.config import Config
from agents.orchestrator import OrchestratorAgent

_agent: OrchestratorAgent | None = None


def get_agent() -> OrchestratorAgent:
    global _agent
    if _agent is None:
        config = Config()
        config.validate()
        _agent = OrchestratorAgent(config)
    return _agent
