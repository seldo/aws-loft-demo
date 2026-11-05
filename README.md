# Wonder Toys: a Strands agent on AgentCore, evaluated with Arize AX

The demo agent from the "Stop vibe-testing your agents" talk at the AWS Loft, San Francisco, October 2026.

Wonder Toys is a shopping assistant for a toy store. It's built with [Strands Agents](https://strandsagents.com/), runs on [Amazon Bedrock AgentCore Runtime](https://aws.amazon.com/bedrock/agentcore/), uses Claude Haiku 4.5 on Amazon Bedrock, and sends OpenTelemetry traces to [Arize AX](https://arize.com/docs/ax). The agent is adapted from the Strands variant in [Project Rosetta Stone](https://github.com/Arize-ai/project-rosetta-stone).

The agent has one known bug, left in on purpose: valid categories like `board-games` aren't listed in the `search_products` tool description, so the model guesses "board games" and gets zero results. Arize's Signal found it without being told to look.

## What's here

| Path | What it is |
|---|---|
| `app.py` | AgentCore Runtime entrypoint (HTTP protocol: `/ping`, `/invocations` on port 8080) |
| `agent/agent.py` | The Strands agent. The Bedrock model ID comes from `MODEL_ID` |
| `agent/tracing.py` | Arize AX tracing: a tracer provider, the OpenInference processor for Strands, and an exporter |
| `agent/tools.py` | Search, product details, purchase, order status, cancel |
| `agent/index_products.py` | Builds the embedded ChromaDB product index (run at image build time) |
| `Dockerfile` | ARM64 image for AgentCore |
| `invoke.py` | Send one turn to the deployed agent |
| `traffic.py` | 40 scripted conversations, some designed to trip the agent up |
| `run-local.sh` | Run the agent locally on port 8080 |
| `evals/` | Prompts for the three LLM judges: Catalog Grounding, Age Appropriateness, Capability Honesty |
| `infra/` | IAM policies (replace `ACCOUNT_ID`) and a script that stores Arize credentials in Secrets Manager |

## Run it locally

Needs Python 3.12, [uv](https://docs.astral.sh/uv/), AWS credentials with Bedrock access, and the [`ax` CLI](https://arize.com/docs/ax) logged in to Arize.

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -m agent.index_products
ARIZE_SPACE_ID=<your space ID> ./run-local.sh
```

Then, in another terminal:

```bash
curl -s localhost:8080/invocations -H "Content-Type: application/json" \
  -H "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id: local-session-0001-abcdefghijklmnopq" \
  -d '{"prompt": "A birthday present for a 6 year old who loves dinosaurs, around $40"}'
```

## Deploy to AgentCore

1. **Bedrock access.** Submit the Anthropic use-case form once per account, and accept each model's Marketplace agreement (`aws bedrock create-foundation-model-agreement`) before first use. New models can also arrive with a token quota of zero, which shows up as "not available for this account".
2. **Arize credentials.** `ARIZE_SPACE_ID=<your space ID> .venv/bin/python infra/create_arize_secret.py` stores them in Secrets Manager as `aws-loft-demo/arize`, so they never go in runtime environment variables.
3. **Image.** Build for ARM64 and push to ECR:
   ```bash
   docker buildx build --platform linux/arm64 -t <ecr-repo-uri>:v1 --push .
   ```
4. **Execution role.** Create a role trusted by `bedrock-agentcore.amazonaws.com` using `infra/trust-policy.json` and `infra/execution-policy.json`, with your account ID in place of `ACCOUNT_ID`.
5. **Runtime.**
   ```bash
   aws bedrock-agentcore-control create-agent-runtime --region us-west-2 \
     --agent-runtime-name wonder_toys_agent \
     --agent-runtime-artifact '{"containerConfiguration":{"containerUri":"<ecr-repo-uri>:v1"}}' \
     --role-arn <execution-role-arn> \
     --network-configuration '{"networkMode":"PUBLIC"}' \
     --protocol-configuration '{"serverProtocol":"HTTP"}' \
     --environment-variables '{"ARIZE_SECRET_ID":"aws-loft-demo/arize","ARIZE_PROJECT_NAME":"wonder-toys-agentcore","MODEL_ID":"us.anthropic.claude-haiku-4-5-20251001-v1:0"}'
   ```
6. **Traffic.** `export AGENT_RUNTIME_ARN=<runtime ARN>`, then `.venv/bin/python traffic.py`.

## Evals in Arize AX

The judges run in Arize AX on Claude Sonnet 4.5 through a Bedrock AI integration, so the agent (Haiku) is judged by a different model. The integration assumes a role in your account. Start from the trust and permissions policies AX generates, add an `sts:ExternalId` condition, and scope `bedrock:InvokeModel` to the models you use. The role also needs `aws-marketplace:ViewSubscriptions`, or Bedrock intermittently denies calls on Marketplace models. `infra/arize-invoke-policy-scoped.json` is the permissions policy used for the demo.

Two gotchas from setting it up:
- Bedrock evaluators need `--provider-params '{"region": "us-west-2"}'`.
- Put span-kind filters on the task, not on the evaluator, and use `attributes.openinference.span.kind = 'LLM'`.

## License

MIT. See `LICENSE`.
