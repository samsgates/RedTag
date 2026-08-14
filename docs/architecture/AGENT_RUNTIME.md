# Agent Runtime deployment

RedTag separates model reasoning from the operational control plane.

`services/agent_runtime/app/agent.py` is a deployable Google ADK application containing a deterministic SequentialAgent pipeline with three specialist LLM agents:

1. Incident Agent
2. Trace Agent
3. Risk Agent

The runtime intentionally cannot directly quarantine inventory or export customer data. Execution goes through the FastAPI control plane where policy, idempotency, connector permissions, Action Receipts, and independent verification are enforced.

With Google Agents CLI installed and authenticated, use the root `agents-cli-manifest.yaml` as the deployment descriptor. Agent Runtime deployment can then be driven by the current Agents CLI workflow.
