# Agentic AI Engineering

Agentic AI projects and experiments.

## Projects

- **[AskGeorge](askgeorge/)** — an AI representative for recruiters and hiring managers. It answers questions in the first person as George Traskas, grounded strictly in his real background, and it assesses how well he fits a job description you paste in, gaps stated plainly. Hybrid retrieval over a Markdown knowledge base, streaming replies in Gradio, any LLM via OpenRouter, deployed on Modal. **[Live here](https://gtraskas--askgeorge-web.modal.run)** — the build walkthrough is in [askgeorge.ipynb](askgeorge.ipynb).

- **[OpenAI Agents SDK](openai_agents_sdk/)** — a single notebook covering the framework end to end: agents and the agent loop, tracing, streaming, function tools, memory, orchestration by code and by LLM (agents as tools and handoffs), structured outputs and guardrails. The running example is a small writing team — three agents draft a LinkedIn post in different voices, an editor picks the best one, and a tool saves it.

- **[CrewAI](crewai/)** — multi-agent crews where agents and tasks are declared in YAML, each crew a self-contained uv project. [debate](crewai/debate/): a debater argues both sides of a motion and a judge picks the winner on the merits alone. [financial_researcher](crewai/financial_researcher/): a researcher gathers live information on a company via web search and an analyst turns it into a structured report. [stock_picker](crewai/stock_picker/): a manager agent delegates finding, researching and picking a trending company — hierarchical process, structured outputs, a custom notification tool, and memory across runs.

## Setup

Uses [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

## License

MIT — see [LICENSE](LICENSE).
