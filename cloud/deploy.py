"""Deploy the private metrics coach using the operator's existing AWS credentials.

No credentials enter the bundle or Vercel. The Lambda role can invoke the selected
Bedrock model, update its quota table and write its own logs only.
"""
import argparse
import json
import os
from pathlib import Path

import boto3

NAME = "agentgrinder-private-coach"
MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


def deploy(bundle, region, public_key, supabase_url):
    session = boto3.Session(region_name=region)
    iam, db, lam = (session.client(x) for x in ("iam", "dynamodb", "lambda"))
    account = session.client("sts").get_caller_identity()["Account"]
    profile = session.client("bedrock").get_inference_profile(inferenceProfileIdentifier=MODEL)
    table_arn = f"arn:aws:dynamodb:{region}:{account}:table/{NAME}"
    try:
        db.describe_table(TableName=NAME)
    except db.exceptions.ResourceNotFoundException:
        db.create_table(TableName=NAME, KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
                        AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}],
                        BillingMode="PAY_PER_REQUEST")
        db.get_waiter("table_exists").wait(TableName=NAME)
        db.update_time_to_live(TableName=NAME, TimeToLiveSpecification={"Enabled": True, "AttributeName": "expires_at"})
    trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    try:
        role = iam.get_role(RoleName=NAME)["Role"]
    except iam.exceptions.NoSuchEntityException:
        role = iam.create_role(RoleName=NAME, AssumeRolePolicyDocument=json.dumps(trust))["Role"]
    policy = {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
         "Resource": [profile["inferenceProfileArn"], *[m["modelArn"] for m in profile["models"]]]},
        {"Effect": "Allow", "Action": ["dynamodb:UpdateItem"], "Resource": table_arn},
        {"Effect": "Allow", "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
         "Resource": f"arn:aws:logs:{region}:{account}:log-group:/aws/lambda/{NAME}:*"},
    ]}
    iam.put_role_policy(RoleName=NAME, PolicyName="private-coach-only", PolicyDocument=json.dumps(policy))
    logs = session.client("logs")
    try:
        logs.create_log_group(logGroupName=f"/aws/lambda/{NAME}")
    except logs.exceptions.ResourceAlreadyExistsException:
        pass
    logs.put_retention_policy(logGroupName=f"/aws/lambda/{NAME}", retentionInDays=7)
    config = dict(FunctionName=NAME, Runtime="python3.12", Role=role["Arn"],
                  Handler="coach_handler.handler", Timeout=120, MemorySize=512,
                  Environment={"Variables": {"SUPABASE_URL": supabase_url,
                    "SUPABASE_ANON_KEY": public_key, "COACH_QUOTA_TABLE": NAME}},
                  Architectures=["arm64"])
    try:
        lam.get_function(FunctionName=NAME)
    except lam.exceptions.ResourceNotFoundException:
        lam.create_function(**config, Code={"ZipFile": bundle.read_bytes()}, Publish=True)
        lam.get_waiter("function_active_v2").wait(FunctionName=NAME)
    else:
        lam.update_function_code(FunctionName=NAME, ZipFile=bundle.read_bytes(), Publish=True)
        lam.get_waiter("function_updated_v2").wait(FunctionName=NAME)
        lam.update_function_configuration(**config)
        lam.get_waiter("function_updated_v2").wait(FunctionName=NAME)
    lam.put_function_concurrency(FunctionName=NAME, ReservedConcurrentExecutions=2)
    # Application authentication happens before metrics retrieval and quota reservation.
    cors = {"AllowOrigins": ["https://agentgrinder.vercel.app"], "AllowMethods": ["POST"],
            "AllowHeaders": ["authorization", "content-type"], "MaxAge": 300}
    try:
        url = lam.get_function_url_config(FunctionName=NAME)["FunctionUrl"]
        lam.update_function_url_config(FunctionName=NAME, AuthType="NONE", Cors=cors)
    except lam.exceptions.ResourceNotFoundException:
        url = lam.create_function_url_config(FunctionName=NAME, AuthType="NONE", Cors=cors)["FunctionUrl"]
    for sid, action, condition in [
        ("public-url-authenticated-in-handler", "lambda:InvokeFunctionUrl", {"FunctionUrlAuthType": "NONE"}),
        ("url-only-invocation", "lambda:InvokeFunction", {"InvokedViaFunctionUrl": True}),
    ]:
        try:
            lam.add_permission(FunctionName=NAME, StatementId=sid, Action=action, Principal="*", **condition)
        except lam.exceptions.ResourceConflictException:
            pass
    print(json.dumps({"function": NAME, "region": region, "url": url, "quota_table": NAME}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()
    deploy(args.bundle, args.region, os.environ["SUPABASE_ANON_KEY"], os.environ["SUPABASE_URL"])
