# CrewAI

Multi-agent projects built with [CrewAI](https://docs.crewai.com/), a framework
where "crews" of role-playing agents collaborate on a sequence of tasks. Agents
and tasks are declared in YAML, and a small Python class wires them together —
most of the behaviour lives in prompts, not code.

## Setup

Each crew in this folder is a self-contained [uv](https://docs.astral.sh/uv/)
project with its own `pyproject.toml`, lockfile and `.venv`, independent of the
repo root environment. The `crewai` CLI is not required: `crewai run` is a
wrapper around the project's own entry script, so `uv run` does the same job.

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

## Crews

### debate

The smallest useful crew: two agents, three sequential tasks.

- A **debater** argues *for* a motion (`propose`), then argues *against* the
  same motion (`oppose`) — the same agent takes both sides.
- A **judge** reads both arguments and declares a winner on the merits alone
  (`decide`).

Each task writes its result to `output/*.md`.

```bash
cd crewai/debate
uv run debate "Remote work makes engineering teams more productive"
```

With no argument a default motion is used. One run makes three
`gpt-5.4-mini` calls.

### financial_researcher

A two-stage pipeline showing tools and task context passing.

- A **researcher** gathers current information on a company — using live web
  search (`SerperDevTool`) when `SERPER_API_KEY` is set, or the model's own
  knowledge otherwise (the report is then not current).
- An **analyst** receives the research through the task's `context`
  declaration and writes a structured report — executive summary, analysis,
  outlook — to `output/report.md`. The report is explicitly not investment
  advice.

```bash
cd crewai/financial_researcher
uv run financial_researcher "NVIDIA"
```

With no argument a default company is used.

## Adding a new crew

Copy the `debate/` layout as a starting point: rename the package under
`src/`, adjust `pyproject.toml` (project name and entry script), and describe
the new agents and tasks in the two YAML files. Each crew stays independent —
its own lockfile, its own `.venv`, no shared state between crews.
