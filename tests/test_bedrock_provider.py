import asyncio
import pytest
from agentgrinder.coach import bedrock


def provider(monkeypatch):
    from strands.models import BedrockModel
    calls = []
    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        calls.append(messages)
        yield {"messageStop": {"stopReason": "end_turn"}}
    monkeypatch.setattr(BedrockModel, "stream", stream)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    return bedrock.create_model(), calls


def consume(model, messages):
    async def run():
        return [x async for x in model.stream(messages)]
    return asyncio.run(run())


def test_request_ceiling_blocks_ninth_dispatch(monkeypatch):
    model, calls = provider(monkeypatch)
    for _ in range(8): consume(model, [])
    with pytest.raises(RuntimeError, match="request limit"):
        consume(model, [])
    assert len(calls) == 8


def test_oversized_input_never_reaches_provider(monkeypatch):
    model, calls = provider(monkeypatch)
    with pytest.raises(RuntimeError, match="request limit"):
        consume(model, [{"role": "user", "content": [{"text": "x" * 30001}]}])
    assert calls == [] and model.calls == 0


def test_limits_are_per_run(monkeypatch):
    first, _ = provider(monkeypatch)
    second = bedrock.create_model()
    consume(first, [])
    assert first.calls == 1 and second.calls == 0
