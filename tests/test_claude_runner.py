from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from financial_agent.claude_runner import run_tool_agent


def _text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def _tool_use_block(tool_id: str, name: str, tool_input: dict) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=tool_id, name=name, input=tool_input)


def _response(content, stop_reason: str) -> SimpleNamespace:
    return SimpleNamespace(content=content, stop_reason=stop_reason)


@pytest.mark.asyncio
async def test_run_tool_agent_executes_tool_and_returns_final_text():
    tool_call_response = _response(
        [_tool_use_block("tool_1", "echo", {"value": "hi"})], "tool_use"
    )
    final_response = _response([_text_block("Echoed: hi")], "end_turn")

    client = AsyncMock()
    client.messages.create.side_effect = [tool_call_response, final_response]

    calls = []

    def echo_impl(value: str) -> str:
        calls.append(value)
        return f"Echoed: {value}"

    result = await run_tool_agent(
        client,
        name="test_agent",
        system="test system",
        user_prompt="say hi",
        tools=[{"name": "echo", "description": "echo", "input_schema": {"type": "object"}}],
        tool_impls={"echo": echo_impl},
    )

    assert calls == ["hi"]
    assert result.text == "Echoed: hi"
    assert result.stop_reason == "end_turn"
    assert client.messages.create.call_count == 2
    # The tool result must reference the original tool_use_id.
    tool_result_message = result.raw_messages[2]
    assert tool_result_message["content"][0]["tool_use_id"] == "tool_1"


@pytest.mark.asyncio
async def test_run_tool_agent_reports_unknown_tool_as_error_without_raising():
    tool_call_response = _response(
        [_tool_use_block("tool_1", "does_not_exist", {})], "tool_use"
    )
    final_response = _response([_text_block("handled")], "end_turn")

    client = AsyncMock()
    client.messages.create.side_effect = [tool_call_response, final_response]

    result = await run_tool_agent(
        client,
        name="test_agent",
        system="test system",
        user_prompt="do something",
        tools=[],
        tool_impls={},
    )

    assert result.text == "handled"
    tool_result_message = result.raw_messages[2]
    assert tool_result_message["content"][0]["is_error"] is True


@pytest.mark.asyncio
async def test_run_tool_agent_handles_tool_exceptions_gracefully():
    tool_call_response = _response(
        [_tool_use_block("tool_1", "boom", {})], "tool_use"
    )
    final_response = _response([_text_block("recovered")], "end_turn")

    client = AsyncMock()
    client.messages.create.side_effect = [tool_call_response, final_response]

    def boom_impl():
        raise RuntimeError("kaboom")

    result = await run_tool_agent(
        client,
        name="test_agent",
        system="test system",
        user_prompt="trigger error",
        tools=[],
        tool_impls={"boom": boom_impl},
    )

    assert result.text == "recovered"
    tool_result_message = result.raw_messages[2]
    assert "kaboom" in tool_result_message["content"][0]["content"]
    assert tool_result_message["content"][0]["is_error"] is True


@pytest.mark.asyncio
async def test_run_tool_agent_handles_refusal():
    refusal_response = _response([], "refusal")
    client = AsyncMock()
    client.messages.create.return_value = refusal_response

    result = await run_tool_agent(
        client,
        name="test_agent",
        system="test system",
        user_prompt="do something risky",
    )

    assert result.stop_reason == "refusal"
    assert "declined" in result.text.lower()


@pytest.mark.asyncio
async def test_run_tool_agent_no_tools_single_round_trip():
    client = AsyncMock()
    client.messages.create.return_value = _response([_text_block("Just an answer.")], "end_turn")

    result = await run_tool_agent(
        client,
        name="test_agent",
        system="test system",
        user_prompt="what is 2+2?",
    )

    assert result.text == "Just an answer."
    client.messages.create.assert_called_once()
