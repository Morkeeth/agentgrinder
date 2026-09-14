"""Explicit, bounded Bedrock provider shared by the shipped coaching paths."""
import json
import os

MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
MAX_CALLS = 8
MAX_REQUEST_BYTES = 30000
MAX_OUTPUT_TOKENS = 2048


def create_model():
    # Lazy imports keep local coaching free of provider construction and requests.
    from strands.models import BedrockModel
    from botocore.config import Config

    class BoundedModel(BedrockModel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.calls = 0

        async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
            encoded = json.dumps([messages, tool_specs, system_prompt, kwargs], default=str).encode()
            if self.calls >= MAX_CALLS or len(encoded) > MAX_REQUEST_BYTES:
                raise RuntimeError("Bedrock request limit reached; no further inference was sent")
            self.calls += 1
            async for event in super().stream(messages, tool_specs, system_prompt, **kwargs):
                yield event

    return BoundedModel(
        model_id=os.environ.get("AGENTGRINDER_BEDROCK_MODEL", MODEL_ID),
        region_name=os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1",
        max_tokens=MAX_OUTPUT_TOKENS,
        boto_client_config=Config(retries={"total_max_attempts": 1}, read_timeout=90),
    )


def model_label():
    return "strands agent loop · Amazon Bedrock · " + os.environ.get("AGENTGRINDER_BEDROCK_MODEL", MODEL_ID)
