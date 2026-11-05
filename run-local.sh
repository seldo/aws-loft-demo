#!/bin/bash
# Run the agent locally on :8080 with Arize credentials from the ax default profile.
cd "$(dirname "$0")"
export ARIZE_API_KEY=$(.venv/bin/python -c "import tomllib,os;print(tomllib.load(open(os.path.expanduser('~/.arize/profiles/default.toml'),'rb'))['auth']['api_key'])")
export ARIZE_SPACE_ID="${ARIZE_SPACE_ID:?set ARIZE_SPACE_ID to your Arize space ID}"
export ARIZE_PROJECT_NAME="${ARIZE_PROJECT_NAME:-wonder-toys-agentcore-local}"
export AWS_REGION=us-west-2
exec .venv/bin/python app.py
