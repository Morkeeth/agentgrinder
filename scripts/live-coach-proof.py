"""Run one bounded, opt-in Bedrock proof on the bundled safe fixture only.

Requires AWS credentials and incurs inference charges. It never discovers local sessions.
"""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--allow-paid-bedrock', action='store_true')
    args = parser.parse_args()
    if not args.allow_paid_bedrock:
        parser.error('Explicit --allow-paid-bedrock is required; this sends the bundled fixture to AWS.')
    from strands.models import BedrockModel
    from botocore.config import Config
    from agentgrinder.coach.agent import create_coach, dispatched, report, COACH_TASK, run_coach
    from agentgrinder.coach.tools import CoachContext, attach

    class BoundedModel(BedrockModel):
        calls = 0
        async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
            encoded = json.dumps([messages, tool_specs, system_prompt, kwargs], default=str).encode()
            if self.calls >= 8 or len(encoded) > 30000:
                raise RuntimeError('Paid proof limit reached before next model call')
            self.calls += 1
            print(f'Bedrock inference request {self.calls}/8', flush=True)
            async for event in super().stream(messages, tool_specs, system_prompt, **kwargs):
                yield event

    os.chdir(ROOT)
    args.output.mkdir(parents=True, exist_ok=True)
    model_id = 'us.anthropic.claude-haiku-4-5-20251001-v1:0'
    model = BoundedModel(model_id=model_id, region_name='us-east-1', max_tokens=2048,
        boto_client_config=Config(retries={'total_max_attempts': 1}, read_timeout=90))
    ctx = CoachContext('samples/sample_session.jsonl', athlete='BUNDLED TEST')
    agent = create_coach(ctx, model=model)
    started = datetime.now(timezone.utc).isoformat()
    print('LIVE BEDROCK · bundled fixture, not a real user session', flush=True)
    print(model_id, flush=True)
    result = agent(COACH_TASK)
    label = 'strands agent loop · live Amazon Bedrock · Claude Haiku 4.5'
    attach(ctx, label)
    text = report(ctx, label, dispatched(agent), str(result).strip(), 'bedrock')
    (args.output/'live-report.txt').write_text(text+'\n')
    if not ctx.verdict or not ctx.verdict.get('matches_card'):
        raise RuntimeError('Live model did not produce an accepted matching verdict')
    local_ctx, local_text = run_coach('samples/sample_session.jsonl', mode='local', athlete='BUNDLED TEST')
    (args.output/'local-report.txt').write_text(local_text+'\n')
    usage = dict(getattr(result.metrics, 'accumulated_usage', {}))
    receipt = {'started_at':started,'finished_at':datetime.now(timezone.utc).isoformat(),
        'revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'model_id':model_id,'region':'us-east-1','fixture':'samples/sample_session.jsonl',
        'label':'LIVE MODEL ON BUNDLED TEST DATA · not independent adoption',
        'model_calls':model.calls,'request_limits':{'calls':8,'serialized_bytes_per_call':30000,'max_output_tokens_per_call':2048},
        'tool_order':dispatched(agent),'dispatch':ctx.dispatch,'verdict':ctx.verdict,
        'usage':usage,'numbers_match_local':ctx.verdict['numbers']==local_ctx.verdict['numbers'],
        'cost_note':'Token usage is measured; invoice cost is not yet available. No billing total is claimed.'}
    (args.output/'receipt.json').write_text(json.dumps(receipt,indent=2,default=str)+'\n')
    print(text, flush=True)
    print('Usage:',json.dumps(usage),flush=True)
    print('Numbers match scripted baseline:',receipt['numbers_match_local'],flush=True)
    if not receipt['numbers_match_local']:
        raise RuntimeError('Live and scripted measured numbers differ')


if __name__=='__main__':
    main()
