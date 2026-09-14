# Live Bedrock coach · 14 September 2026

**A live model ran on the bundled test session. This is execution evidence, not independent adoption or productivity improvement.**

- Provider: Amazon Bedrock, `us-east-1`.
- Model: `us.anthropic.claude-haiku-4-5-20251001-v1:0`.
- Started: `2026-09-14T13:30:35.014506+00:00`; completed: `2026-09-14T13:30:49.794258+00:00`.
- Product source: `5828f39ec4cfeaa63c1cc53e3acdc92589a2ca1a`. The proof runner was an additional uncommitted helper at execution; its SHA256 was `92f70c8e5a1e41d0bb9ab25c368c7505f0b7763fdcd84819bc6b557e32e851e8`. It is included in this commit.
- Input: `samples/sample_session.jsonl`, a labelled public-safe fixture. No private session discovery.
- Model requests: **7**. Strands tool dispatches: **9**.
- Token usage reported by the SDK: **17,123 input + 1,550 output = 18,673 tokens**. Invoice cost was not available at capture time.

## Accepted measurements

Three typed turns; two claims, of which one had matching evidence; one existing artifact out of two referenced writes; zero recorded commits. The accepted numbers match the scripted local run on the same fixture.

The live model called read_run, both claim checks, both artifact checks, both git checks and write_verdict twice. Two verdict calls do not prove a refusal and retry: this receipt retained dispatch names, not the tool response bodies.

## What the model got wrong

The unedited output calls 0.67 a verification rate. It is verified items per typed turn; the claim evidence fraction is one of two. Its “different repository” interpretation is not established by an outside-repository result. File existence and modification time do not prove the file was produced during the session.

The numeric gate checks numeric arguments and nonempty prose. It does not verify narrative truth or the usefulness of advice. Matching local counts establishes consistency between these paths, not independent validation of the measurements.

## Inspect the evidence

[Structured receipt](receipts/bedrock-2026-09-14/receipt.json) · [Unedited live output](receipts/bedrock-2026-09-14/live-report.txt) · [Scripted comparison](receipts/bedrock-2026-09-14/local-report.txt)

## Reproduce only if you intend to pay for inference

Install the coach extra and configure AWS credentials outside the repository. Then:

```sh
python3 scripts/live-coach-proof.py --allow-paid-bedrock --output /tmp/grinder-bedrock-proof
```

The helper uses the existing product's create_coach factory with an explicit Bedrock model. It limits requests to eight, serialized input per request to 30,000 bytes, output to 2,048 tokens per request and disables SDK HTTP retries. Those are request bounds, not an AWS billing meter. The test performs no hosted publication.
