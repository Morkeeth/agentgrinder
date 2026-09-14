# Bedrock in the product coaching path

Both transcript coaching and native Cursor/Codex activity coaching construct the same bounded provider. The default is Claude Haiku 4.5 through the US inference profile on Amazon Bedrock. Set AWS_REGION (or AWS_DEFAULT_REGION); AGENTGRINDER_BEDROCK_MODEL can override the model. An override may change availability and cost.

Each run permits at most eight provider stream requests, 30,000 serialized request bytes per request, and 2,048 output tokens per request. HTTP retries are disabled. These are inference request limits, not a billing meter. Oversized sessions can stop before a verdict. Transcript coaching visibly reports a deterministic fallback as DEGRADED; native activity coaching raises on failure.

Local mode does not construct this provider. Native activity coaching sends supported counts and capability labels; it does not send accepted private practices. Transcript coaching sends the existing tool evidence and retains its existing disclosure.

## Live product-path check, 14 September 2026

`run_coach(..., mode="bedrock")` completed on the bundled safe sample through the new shared provider. This is the function used by the transcript CLI, not a replacement agent constructed by a proof script. It dispatched nine tools. The dispatch hook recorded write_verdict accepted=false followed by accepted=true. Accepted counts matched the card: three typed turns, two claims, one evidenced claim, one currently existing artifact and zero commits. This is a sample execution, not adoption.

The output still made unsupported narrative claims, including interpreting outside-repository as another repository. Prompt guidance did not eliminate that error. The report now labels interpretation separately from the numeric check. The proposed next-session plan must still be reviewed by the builder. No general narrative correctness is claimed.

[Unedited report](receipts/bedrock-product-2026-09-14/report.txt) · [Dispatch outcomes](receipts/bedrock-product-2026-09-14/dispatch.json)

## Next product change

A hosted coach needs a versioned evidence package, explicit cloud consent, authenticated invocation, a persistent request budget and saved private results. It cannot verify the user's local filesystem from a cloud runtime. AgentCore should serve this journey rather than a disconnected sample endpoint.
