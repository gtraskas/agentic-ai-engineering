# OpenAI Agents SDK

A single notebook, [openai_agents_sdk.ipynb](openai_agents_sdk.ipynb),
covering the framework end to end:

1. Agents and the agent loop
2. Tracing and streaming
3. Function tools
4. Memory — manual history passing and `SQLiteSession`
5. Orchestrating by code — parallel drafts plus a picker agent
6. Orchestrating by LLM — agents as tools, and handoffs
7. Structured outputs (Pydantic)
8. Guardrails — the framework feature and the plain-code equivalent

The running example is a small writing team: three agents draft a short
LinkedIn post in different voices, an editor picks the best one, and a tool
saves it. Nothing is sent anywhere — the "save" tool appends to a local list.

## Run

Dependencies come from the repo root project:

```bash
uv sync
```

Set `OPENAI_API_KEY` in the repo-root `.env` (the notebook calls OpenAI
directly so run traces appear at
[platform.openai.com/traces](https://platform.openai.com/traces)), then open
the notebook with Jupyter or your editor and run top to bottom.
