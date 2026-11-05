"""AgentCore Runtime entrypoint for the Wonder Toys agent.

BedrockAgentCoreApp serves the HTTP protocol contract on port 8080:
GET /ping for health checks and POST /invocations for requests.

Invoke with a JSON payload: {"prompt": "...", "user_id": "..."}.
The AgentCore runtime session ID identifies the conversation.
"""

import asyncio

import agent.tracing  # noqa: F401 — must be imported before strands

from bedrock_agentcore.runtime import BedrockAgentCoreApp, RequestContext
from opentelemetry import trace

from agent.agent import run_agent

app = BedrockAgentCoreApp()


@app.entrypoint
async def invoke(payload: dict, context: RequestContext) -> dict:
    session_id = context.session_id or "local-session"
    user_id = payload.get("user_id", session_id)

    reply = await run_agent(payload["prompt"], session_id, user_id)

    # Export this turn's spans now rather than waiting for the batch timer,
    # since AgentCore can stop an idle session's microVM at any time.
    await asyncio.to_thread(trace.get_tracer_provider().force_flush)

    return {"result": reply}


if __name__ == "__main__":
    app.run()
