"""Send one turn to the deployed Wonder Toys agent on AgentCore Runtime.

Usage:
  .venv/bin/python invoke.py "I need a gift for a 6 year old who loves dinosaurs"
  .venv/bin/python invoke.py --session <id> "Tell me more about the first one"

Reuse --session to continue a conversation. Session IDs must be 33+ chars.
Requires AGENT_RUNTIME_ARN in the environment.
"""

import argparse
import json
import os
import uuid

import boto3

# The ARN printed by `aws bedrock-agentcore-control create-agent-runtime`.
RUNTIME_ARN = os.environ["AGENT_RUNTIME_ARN"]

client = boto3.client("bedrock-agentcore", region_name="us-west-2")


def invoke(prompt: str, session_id: str, user_id: str = "demo-user") -> str:
    response = client.invoke_agent_runtime(
        agentRuntimeArn=RUNTIME_ARN,
        qualifier="DEFAULT",
        runtimeSessionId=session_id,
        payload=json.dumps({"prompt": prompt, "user_id": user_id}).encode(),
    )
    body = json.loads(response["response"].read())
    return body.get("result") or f"ERROR: {body}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt")
    parser.add_argument("--session", default=f"session-{uuid.uuid4()}")
    args = parser.parse_args()

    print(f"session: {args.session}\n")
    print(invoke(args.prompt, args.session))
