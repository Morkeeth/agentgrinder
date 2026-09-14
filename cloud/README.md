# Private web coach on AWS

The signed-in owner of a private, measured run can ask a Strands agent for one next-session practice. AWS Lambda hosts this service; AgentCore is not used.

## Use

Open your private run, review the measurement preview, optionally enter a goal, and give consent before choosing **Coach this run**. Review the returned proposal, then accept or edit it through the existing private-practice form. Acceptance saves the practice in Supabase and freezes the run as its baseline. Generating a proposal does not publish or update the run. The proposal is transient until accepted.

The browser sends `run_id`, `consent_version: "metrics-v1"` and `goal`, with the current Supabase session as a Bearer token. Lambda verifies the session and ownership, requires private visibility and a measurement revision, and reads an explicit column allowlist. Bedrock receives harness and recorded counts plus the entered goal. This path does not read transcripts, run titles, file paths or saved private notes. The goal is user-supplied text: do not include credentials or private material.

Counts are recorded observations, not an independent assessment of quality. Unknown measurements stay unknown. A proposal must reference available metric fields and describe a workflow experiment, but these checks do not establish narrative truth, usefulness or improvement. The cloud agent cannot inspect local files or Git.

## Deploy

Use Python 3.12 with `pip` and `boto3`, an AWS credential profile outside the repository, and permission to manage this service's IAM role, Lambda function, DynamoDB table and CloudWatch log group. Bedrock access to the configured Claude Haiku 4.5 US inference profile must be available.

Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` in the deployment environment. Use the public anon key, never a service-role key. Do not commit credentials or environment files.

From the repository root:

```sh
python3.12 cloud/package.py /tmp/agentgrinder-private-coach.zip
python3.12 cloud/deploy.py /tmp/agentgrinder-private-coach.zip --region us-east-1
```

Packaging installs the pinned dependencies from `cloud/requirements.txt` as Linux ARM64 wheels and includes `coach_handler.py`. Deployment creates or updates `agentgrinder-private-coach` and prints its function URL. Set `window.GRINDER_COACH_URL` in `site/cloud-coach-config.js` to that URL, then deploy the web app. With no configured endpoint, the button stays hidden. The configured browser origin is `https://agentgrinder.vercel.app`.

Verify the packaged function imports successfully, unauthenticated calls are rejected, and an authorized private-run request returns a matching `run_id` and `measurement_revision`. A successful paid request is needed to establish live model execution. Local tests use substitutes and do not prove deployment or inference:

```sh
python3.12 -m pytest tests/test_cloud_coach.py -q
```

## Bounds and storage

- DynamoDB atomically reserves both **10 requests globally per UTC day** and **2 per authenticated user per UTC day** before inference. Failed or ambiguous reservations stop the request. A model failure consumes its reservation; there is no automatic refund.
- Each inference permits at most **4 model stream requests**, **16,000 serialized request bytes per request**, and **1,024 output tokens per request**. HTTP retries are disabled. These limits are not a billing meter and do not bound all hosting charges.
- Lambda has a 120-second timeout; the browser stops waiting after 90 seconds and explains that AWS may still finish. The deployer requests two reserved concurrent executions only when account capacity allows. A small account with a limit of ten has no guaranteed function reservation; daily inference quotas still apply.
- The function runs in `us-east-1`. Its US Bedrock inference profile may route between US regions.
- Quota rows contain account identifiers and daily counts, with expiry set three days ahead; DynamoDB TTL deletion is asynchronous. Proposals and goals are not persisted by the handler.
- Strands SDK logging is suppressed to prevent warnings containing tool arguments from entering application logs. The handler does not log session tokens, goals, metrics or model output. CloudWatch runtime diagnostics have seven-day retention. Provider retention settings are separate.
- The Lambda role can invoke the selected inference profile and its models, update the quota table, and write its own log streams. Supabase reads use the caller's session and public anon key, preserving database access policies.

This service proposes a practice. A builder's later observation is still needed to decide whether to keep, change or drop it.
