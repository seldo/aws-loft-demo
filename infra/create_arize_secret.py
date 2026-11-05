"""Store the Arize AX credentials in Secrets Manager for the AgentCore runtime.

Reads the API key from the ax CLI's default profile so it never appears on
screen or in a file. Run from the repo root:

  ARIZE_SPACE_ID=<your space ID> .venv/bin/python infra/create_arize_secret.py
"""

import json
import os
import tomllib

import boto3

SECRET_NAME = "aws-loft-demo/arize"
SPACE_ID = os.environ["ARIZE_SPACE_ID"]

profile = os.path.expanduser("~/.arize/profiles/default.toml")
api_key = tomllib.load(open(profile, "rb"))["auth"]["api_key"]

secret = boto3.client("secretsmanager", region_name="us-west-2").create_secret(
    Name=SECRET_NAME,
    Description="Arize AX credentials for the Wonder Toys AgentCore demo",
    SecretString=json.dumps({"space_id": SPACE_ID, "api_key": api_key}),
    Tags=[{"Key": "project", "Value": "aws-loft-demo"}],
)
print(f"Created {secret['ARN']}")
