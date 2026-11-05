import os

from openinference.instrumentation import using_session
from strands import Agent
from strands.models import BedrockModel

from agent.context import current_user_id
from agent.prompt import SYSTEM_PROMPT
from agent.tools import (
    search_products,
    get_product_detail,
    purchase_product,
    check_order_status,
    cancel_order_tool,
)

# Any Bedrock model or inference profile ID. Swapping models for an
# experiment is a change to this one environment variable.
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")

# AgentCore Runtime gives each session its own microVM, so one cached Agent
# per session ID carries the multi-turn history for that conversation.
_agents: dict[str, Agent] = {}


def _build_agent(session_id: str, user_id: str) -> Agent:
    """Create a Strands Agent wired to Claude on Amazon Bedrock.

    `trace_attributes` adds attributes to every span the Agent emits. We use
    it to inject `session.id` / `user.id` because the Strands OpenInference
    processor doesn't propagate baggage from `using_session()` onto spans.
    """
    model = BedrockModel(
        model_id=MODEL_ID,
        region_name=AWS_REGION,
        max_tokens=4096,
        temperature=0.7,
    )
    return Agent(
        name="WonderToysAgent",
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            search_products,
            get_product_detail,
            purchase_product,
            check_order_status,
            cancel_order_tool,
        ],
        trace_attributes={
            "session.id": session_id,
            "user.id": user_id,
            "llm.model_name": MODEL_ID,
        },
    )


async def run_agent(prompt: str, session_id: str, user_id: str) -> str:
    """Run one conversational turn and return the assistant's reply."""
    agent = _agents.get(session_id)
    if agent is None:
        agent = _build_agent(session_id, user_id)
        _agents[session_id] = agent

    # Tools read the caller from this context var, so the LLM never sees it.
    token = current_user_id.set(user_id)
    try:
        with using_session(session_id):
            result = await agent.invoke_async(prompt)
    finally:
        current_user_id.reset(token)

    return str(result)
