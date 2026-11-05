"""Arize AX tracing initialization for AWS Strands on AgentCore Runtime.

This module MUST be imported before any `strands` imports so that the
OpenTelemetry tracer provider is set globally before Strands' singleton
tracer caches its reference to it.

Strands emits its own OpenTelemetry spans. The
`StrandsAgentsToOpenInferenceProcessor` reshapes them in-place into
OpenInference format before they are exported to Arize AX.

Credentials:
  ARIZE_SPACE_ID / ARIZE_API_KEY from the environment (local dev), or else
  from the Secrets Manager secret named by ARIZE_SECRET_ID (on AgentCore,
  where secrets must not go in runtime environment variables). The secret is
  JSON: {"space_id": "...", "api_key": "..."}.

  ARIZE_PROJECT_NAME — project name in Arize AX (not a secret).
"""

import json
import os

import boto3
from arize.otel import BatchSpanProcessor, PROJECT_NAME, Resource
from openinference.instrumentation.strands_agents import (
    StrandsAgentsToOpenInferenceProcessor,
)
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider


def _arize_credentials() -> tuple[str, str]:
    space_id = os.environ.get("ARIZE_SPACE_ID")
    api_key = os.environ.get("ARIZE_API_KEY")
    if space_id and api_key:
        return space_id, api_key

    secret = boto3.client("secretsmanager").get_secret_value(
        SecretId=os.environ["ARIZE_SECRET_ID"]
    )
    creds = json.loads(secret["SecretString"])
    return creds["space_id"], creds["api_key"]


space_id, api_key = _arize_credentials()

tracer_provider = TracerProvider(
    resource=Resource.create({PROJECT_NAME: os.environ["ARIZE_PROJECT_NAME"]})
)

# Processor ordering matters: the OpenInference processor mutates spans
# in-place, so it must run before the exporter sees them.
tracer_provider.add_span_processor(StrandsAgentsToOpenInferenceProcessor())
tracer_provider.add_span_processor(
    BatchSpanProcessor(space_id=space_id, api_key=api_key)
)
trace.set_tracer_provider(tracer_provider)
