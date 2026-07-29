# Financial researcher crew

A two-stage research pipeline: a researcher gathers current information on a
company, an analyst turns it into a structured report. Demonstrates agent
tools and task context passing.

| Task | Agent | Writes |
| --- | --- | --- |
| research_task | researcher | — (feeds the next task) |
| analysis_task | analyst | `output/report.md` |

The analysis task declares `context: [research_task]` in the YAML, so the
analyst receives the researcher's findings as input. The report opens with an
executive summary and is explicitly not investment advice.

## Run

```bash
uv sync
uv run financial_researcher "NVIDIA"
```

With no argument a default company is used. The company name and the current
date are runtime inputs interpolated into every prompt.

Requires `OPENAI_API_KEY` in the repo-root `.env` — see
[../README.md](../README.md) for shared setup. With `SERPER_API_KEY`
([serper.dev](https://serper.dev/), free tier) also set, the researcher
searches the web live; without it the crew still runs on the model's own
knowledge, so the report is not current.

## Layout

- [src/financial_researcher/config/agents.yaml](src/financial_researcher/config/agents.yaml) — who the agents are: role, goal, backstory, model
- [src/financial_researcher/config/tasks.yaml](src/financial_researcher/config/tasks.yaml) — what they do, and the context link between them
- [src/financial_researcher/crew.py](src/financial_researcher/crew.py) — wires the YAML into a sequential crew; attaches the search tool when the key is present
- [src/financial_researcher/main.py](src/financial_researcher/main.py) — entry point: reads the company, kicks off
