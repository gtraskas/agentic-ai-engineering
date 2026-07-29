# Engineering team crew

Four agents build a working system from a paragraph of requirements: a lead
designs it, a backend engineer implements it, a frontend engineer wraps it in
a Gradio app, and a test engineer writes and runs unit tests until they pass.
All four share one sandbox directory, and every line of code they write is
executed inside a container rather than on the host.

## Demonstrates

- **Sandboxed code execution** — the agents' `run` tool starts an ephemeral
  Docker container with only `sandbox/` mounted, runs the file, and discards
  the container. Model-written code never executes directly on your machine,
  and the file tools refuse any path that resolves outside the sandbox.
- **MCP tools** — the lead and frontend engineer connect to
  [Context7](https://context7.com/), a live documentation server, so they can
  check current library APIs instead of relying on training data.
- **Mixed models per agent** — the lead designs on a stronger model
  (`gpt-5.5`) because every later stage inherits its decisions; the engineers
  implement on `gpt-5.4-mini`.
- **Shared workspace pipeline** — four tasks chained by `context`, all
  reading and writing the same directory, so later agents build on real files
  rather than on descriptions of files.
- **Tool cache opt-out** — sandbox state changes between calls, so these
  tools refuse CrewAI's default result caching.

| Task | Agent | Produces |
| --- | --- | --- |
| design_task | engineering_lead | `sandbox/design.md` |
| code_task | backend_engineer | backend module in `sandbox/` |
| frontend_task | frontend_engineer | `sandbox/app.py` plus a validation script |
| test_task | test_engineer | test file and `sandbox/test_summary.md` |

## Run

Docker must be installed and running — the crew checks before making any LLM
call and stops with a clear message if it is not.

```bash
uv sync
uv run engineering_team
```

To build something else, pass a file containing your own requirements:

```bash
uv run engineering_team my_requirements.md
```

The default requirements build an account management system for a trading
simulation: deposits and withdrawals, share transactions, portfolio
valuation, profit and loss reporting, and rules preventing overdrafts or
selling shares the user does not hold.

Requires `OPENAI_API_KEY` in the repo-root `.env` — see
[../README.md](../README.md) for shared setup. This crew costs noticeably
more per run than the others here: four agents, each iterating with tools,
one of them on a larger model.

When the run finishes, the generated app can be launched from the sandbox:

```bash
cd sandbox
uv run app.py
```

## The sandbox

`sandbox/` is wiped and re-created as a fresh uv project on every run, so it
is gitignored and nothing in it is precious. Dependencies are declared on the
host but installed inside the container, so no host virtual environment is
left there.

The container mounts only this directory and is removed after each call,
including when a script overruns the five minute timeout — it is named on
creation so it can be force-removed rather than left running in the Docker
daemon. It does have network access, because installing the project's
dependencies requires it.

Filenames come from the agents, so the read, write and run tools resolve every
path and refuse anything landing outside the sandbox — an absolute path, a
`..` segment or a symlink pointing out. Without that check an agent could
overwrite files elsewhere in the repo.

The runner image is pulled once on first use and then cached by Docker.
To remove it later:

```bash
docker rmi ghcr.io/astral-sh/uv:python3.13-bookworm-slim
```

## Layout

- [src/engineering_team/config/agents.yaml](src/engineering_team/config/agents.yaml) — the lead and the three engineers, including each one's model
- [src/engineering_team/config/tasks.yaml](src/engineering_team/config/tasks.yaml) — what they do, and the context links between tasks
- [src/engineering_team/crew.py](src/engineering_team/crew.py) — wires the YAML into a sequential crew and attaches tools and MCP servers
- [src/engineering_team/tools/sandbox_tools.py](src/engineering_team/tools/sandbox_tools.py) — list, read, write and containerised run
- [src/engineering_team/patch.py](src/engineering_team/patch.py) — see below
- [src/engineering_team/main.py](src/engineering_team/main.py) — entry point: checks Docker, resets the sandbox, kicks off

### Why patch.py exists

CrewAI 1.14.4 renames remote MCP tools when it discovers them
(`resolve-library-id` becomes `resolve_library_id`) and then sends the renamed
version back to the server, which does not recognise it. Any MCP server using
hyphens in tool names, including Context7, silently returns nothing.

`patch.py` replaces one method so the server's original name is used for the
call while the model still sees the safe name. It is scoped to this pinned
version: on a CrewAI upgrade, check whether the bug is fixed upstream and
delete the file and its import in `main.py` if so.
