# Financial researcher crew

A two-stage research pipeline: a researcher gathers current information on a
company, an analyst turns it into a structured report.

## Demonstrates

- **Agent tools** — the researcher carries a web-search tool
  (`SerperDevTool`), attached only when its API key is present, so the crew
  degrades gracefully instead of failing.
- **Task context passing** — the analysis task declares
  `context: [research_task]`, receiving the researcher's findings as input.
- **Runtime inputs** — `{company}` and `{current_date}` are interpolated
  into every prompt from the `kickoff()` inputs.

| Task | Agent | Writes |
| --- | --- | --- |
| research_task | researcher | — (feeds the next task) |
| analysis_task | analyst | `output/report.md` |

The report opens with an executive summary and is explicitly not investment
advice.

## Run

```bash
uv sync
uv run financial_researcher "NVIDIA"
```

With no argument a default company is used.

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
