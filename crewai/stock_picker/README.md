# Stock picker crew

A manager agent delegates to three specialists to find trending companies in
a sector, research them, and pick the most promising one. Educational demo of
hierarchical multi-agent orchestration — not investment advice.

## Demonstrates

- **Hierarchical process** — `Process.hierarchical` with a dedicated manager
  agent (`allow_delegation=True`) that decides who works when, instead of a
  fixed task sequence.
- **Structured outputs** — tasks return validated Pydantic objects
  (`output_pydantic`), so downstream tasks consume typed data, not prose.
- **Custom tool** — a `@tool`-decorated function the picker agent calls to
  notify the user of the decision.
- **Memory** — short-term, long-term and entity memory persisted under
  `memory/` (gitignored), which is how repeat runs avoid picking the same
  company twice.

| Task | Agent | Writes |
| --- | --- | --- |
| find_trending_companies | trending_company_finder | `output/trending_companies.json` |
| research_trending_companies | financial_researcher | `output/research_report.json` |
| pick_best_company | stock_picker | `output/decision.md` |

## Run

```bash
uv sync
uv run stock_picker "Energy"
```

With no argument a default sector is used. The sector and the current date
are runtime inputs interpolated into every prompt.

Requires `OPENAI_API_KEY` in the repo-root `.env` — see
[../README.md](../README.md) for shared setup. Optional extras, same
graceful-fallback pattern:

- `SERPER_API_KEY` ([serper.dev](https://serper.dev/), free tier) — live news
  search for the finder and researcher agents; without it they rely on the
  model's own knowledge.
- `GMAIL_ADDRESS` + `GMAIL_APP_PASSWORD` (a Gmail App Password) — the
  decision notification arrives by email; without them it is appended to
  `output/notifications.log`.

A hierarchical run makes noticeably more LLM calls than a sequential one —
the manager plans and delegates between every step.

## Layout

- [src/stock_picker/config/agents.yaml](src/stock_picker/config/agents.yaml) — the three specialists plus the manager
- [src/stock_picker/config/tasks.yaml](src/stock_picker/config/tasks.yaml) — what they do, and the context links between tasks
- [src/stock_picker/crew.py](src/stock_picker/crew.py) — Pydantic output models and the hierarchical crew wiring
- [src/stock_picker/tools/notify_tool.py](src/stock_picker/tools/notify_tool.py) — the custom notification tool
- [src/stock_picker/main.py](src/stock_picker/main.py) — entry point: reads the sector, kicks off
