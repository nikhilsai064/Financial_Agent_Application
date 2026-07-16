"""Generic Claude tool-use loop shared by every agent.

Each "agent" in this system is a Claude Messages API call scoped to a system
prompt and a set of tools. This module implements the manual agentic loop:
send a request, execute any client-side tool calls locally, feed the results
back, and repeat until Claude stops asking for tools.
"""

from __future__ import annotations

import asyncio
import dataclasses
from typing import Any, Callable

import anthropic

from .config import DEFAULT_MODEL, MAX_TOOL_ITERATIONS

ToolImpl = Callable[..., str]


@dataclasses.dataclass
class AgentResult:
    """The outcome of running one agent to completion."""

    name: str
    text: str
    raw_messages: list[dict[str, Any]]
    stop_reason: str | None = None


async def run_tool_agent(
    client: anthropic.AsyncAnthropic,
    *,
    name: str,
    system: str,
    user_prompt: str,
    tools: list[dict[str, Any]] | None = None,
    tool_impls: dict[str, ToolImpl] | None = None,
    model: str = DEFAULT_MODEL,
    effort: str = "medium",
    max_tokens: int = 4096,
    max_iterations: int = MAX_TOOL_ITERATIONS,
) -> AgentResult:
    """Run a single Claude agent to completion, handling any tool calls.

    Client-side tools (declared with an `input_schema`) are dispatched to the
    matching callable in `tool_impls` and run off the event loop via
    `asyncio.to_thread`. Server-side tools (e.g. web search) resolve inside
    Anthropic's infrastructure and require no local dispatch.
    """
    tools = tools or []
    tool_impls = tool_impls or {}
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]
    response = None

    for _ in range(max_iterations):
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            thinking={"type": "adaptive"},
            output_config={"effort": effort},
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                impl = tool_impls.get(block.name)
                if impl is None:
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Unknown tool: {block.name}",
                            "is_error": True,
                        }
                    )
                    continue
                try:
                    result = await asyncio.to_thread(impl, **block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        }
                    )
                except Exception as exc:  # noqa: BLE001 - surfaced to the model, not raised
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Tool error: {exc}",
                            "is_error": True,
                        }
                    )

            if not tool_results:
                # stop_reason was "tool_use" but every tool_use block was
                # server-executed (e.g. web search) — nothing to send back.
                break

            messages.append({"role": "user", "content": tool_results})
            continue

        if response.stop_reason == "pause_turn":
            # A server-side tool loop hit its internal iteration cap.
            # Re-sending the conversation as-is resumes it automatically.
            continue

        break

    text = ""
    stop_reason = None
    if response is not None:
        stop_reason = response.stop_reason
        text = "\n".join(block.text for block in response.content if block.type == "text")
        if stop_reason == "refusal" and not text:
            text = "[Agent declined to respond for policy reasons.]"

    return AgentResult(name=name, text=text, raw_messages=messages, stop_reason=stop_reason)
