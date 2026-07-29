# CrewAI

Multi-agent projects built with [CrewAI](https://docs.crewai.com/), a framework
where "crews" of role-playing agents collaborate on a sequence of tasks. Agents
and tasks are declared in YAML, and a small Python class wires them together —
most of the behaviour lives in prompts, not code.

## Crews

- **[debate](debate/)** — a debater argues both sides of a motion; a judge
  picks the winner on the merits alone. The smallest useful crew: YAML
  agents, sequential tasks, output files.
- **[financial_researcher](financial_researcher/)** — a researcher gathers
  current information on a company (live web search when a key is set) and
  an analyst turns it into a structured report. Adds agent tools, task
  context passing, and runtime inputs.
- **[stock_picker](stock_picker/)** — a manager agent delegates finding,
  researching and picking a trending company in a sector. Adds hierarchical
  process, structured Pydantic outputs, a custom notification tool, and
  persistent memory.

Each crew's README covers what it does, what it demonstrates, and how to
run it.

## Setup

Each crew is a self-contained [uv](https://docs.astral.sh/uv/) project with
its own `pyproject.toml`, lockfile and `.venv`, independent of the repo root
environment. The `crewai` CLI is not required: `crewai run` is a wrapper
around the project's own entry script, so `uv run` does the same job.

To set up a crew:

```bash
cd crewai/debate
uv sync
```

API keys are read from the repo-root `.env` (gitignored). The crews here use
OpenAI, so `OPENAI_API_KEY` must be set there. `SERPER_API_KEY`
([serper.dev](https://serper.dev/), free tier) is optional and enables live
web search where a crew supports it.

## Anatomy of a crew

```
debate/
├── pyproject.toml              # own project: crewai[tools] pinned, entry script
└── src/debate/
    ├── config/
    │   ├── agents.yaml         # who the agents are: role, goal, backstory, llm
    │   └── tasks.yaml          # what they do: description, expected output, output file
    ├── crew.py                 # @CrewBase class wiring YAML into a Crew
    └── main.py                 # entry point: load env, kickoff with inputs
```

`{placeholders}` in the YAML are filled from the `inputs` dict passed to
`kickoff()` — that is how the same crew runs on any topic.

## Adding a new crew

Copy the `debate/` layout as a starting point: rename the package under
`src/`, adjust `pyproject.toml` (project name and entry script), and describe
the new agents and tasks in the two YAML files. Each crew stays independent —
its own lockfile, its own `.venv`, no shared state between crews.
