"""Base `Agent` definition: a system prompt plus a bound set of tools."""

from __future__ import annotations

import dataclasses
from typing import Any, Callable

import anthropic

from ..claude_runner import AgentResult, run_tool_agent
from ..config import DEFAULT_MODEL


@dataclasses.dataclass
class Agent:
    """A named, single-purpose Claude agent with its own system prompt and tools."""

    name: str
    system: str
    tools: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    tool_impls: dict[str, Callable[..., str]] = dataclasses.field(default_factory=dict)
    model: str = DEFAULT_MODEL
    effort: str = "medium"
    max_tokens: int = 4096

    async def run(self, client: anthropic.AsyncAnthropic, user_prompt: str) -> AgentResult:
        return await run_tool_agent(
            client,
            name=self.name,
            system=self.system,
            user_prompt=user_prompt,
            tools=self.tools,
            tool_impls=self.tool_impls,
            model=self.model,
            effort=self.effort,
            max_tokens=self.max_tokens,
        )
