# Agentic AI Engineering

Production agentic AI systems in Python: retrieval-grounded assistants, multi-agent
crews, and the engineering around them — evaluation, guardrails, cost control and
deployment.

**Live demo: [AskGeorge](https://gtraskas.github.io/askgeorge/)** — an AI
representative that answers recruiter questions and assesses fit against a job
description you paste in.

| Project | What it is | Run it |
| --- | --- | --- |
| **[AskGeorge](askgeorge/)** | A deployed AI representative: hybrid retrieval over a Markdown knowledge base, streaming replies, job-fit analysis with a score computed in code so it cannot flatter | `uv run python -m askgeorge.app` |
| **[OpenAI Agents SDK](openai_agents_sdk/)** | One notebook covering the framework end to end: tools, memory, orchestration by code and by LLM, structured outputs, guardrails | open [the notebook](openai_agents_sdk/openai_agents_sdk.ipynb) |
| **[CrewAI](crewai/)** | Four crews of increasing sophistication, from a two-agent debate to a four-agent team that writes and tests its own code inside Docker | `cd crewai/<crew> && uv run <crew>` |

Engineering behind the demo: a 23-question retrieval eval that blocks a deploy when
recall regresses, an LLM guardrail running in parallel with generation, per-IP and
global rate limits, two interchangeable agent backends (framework and from-scratch),
and continuous deployment to Modal that scales to zero.

## Projects

### AskGeorge

An AI representative for recruiters and hiring managers. It answers questions in the
first person as George Traskas, grounded strictly in his real background, and it
assesses how well he fits a job description you paste in, with gaps stated plainly.
Hybrid dense and sparse retrieval over a Markdown corpus, streaming replies in Gradio,
any LLM via OpenRouter, deployed on Modal.

The design decisions and their reasoning are written up in
[askgeorge/README.md](askgeorge/README.md); the build walkthrough is in
[askgeorge.ipynb](askgeorge.ipynb) (run it from the repo root).

### OpenAI Agents SDK

A single notebook covering the framework end to end: agents and the agent loop,
tracing, streaming, function tools, memory, orchestration by code and by LLM (agents
as tools and handoffs), structured outputs and guardrails. The running example is a
small writing team — three agents draft a LinkedIn post in different voices, an editor
picks the best one, and a tool saves it.

### CrewAI

Multi-agent crews where agents and tasks are declared in YAML, each crew a
self-contained uv project.

- [debate](crewai/debate/) — a debater argues both sides of a motion and a judge picks
  the winner on the merits alone.
- [financial_researcher](crewai/financial_researcher/) — a researcher gathers live
  information on a company via web search and an analyst turns it into a structured
  report.
- [stock_picker](crewai/stock_picker/) — a manager agent delegates finding, researching
  and picking a trending company: hierarchical process, structured outputs, a custom
  notification tool, and memory across runs.
- [engineering_team](crewai/engineering_team/) — four agents design, build, demo and
  test a working system from a paragraph of requirements, executing their own code
  inside Docker and consulting live documentation over MCP.

## Setup

Uses [uv](https://docs.astral.sh/uv/). From the repo root:

```bash
uv sync
```

Copy `.env.example` to `.env` and fill in the keys you need. Each CrewAI crew is a
separate project with its own dependencies — see [crewai/README.md](crewai/README.md).

## License

MIT — see [LICENSE](LICENSE).
