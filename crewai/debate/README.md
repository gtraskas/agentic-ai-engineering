# Debate crew

Two agents, three sequential tasks: a debater argues both sides of a motion,
then a judge picks the winner on the merits of the arguments alone.

| Task | Agent | Writes |
| --- | --- | --- |
| propose | debater | `output/propose.md` |
| oppose | debater | `output/oppose.md` |
| decide | judge | `output/decide.md` |

The same debater agent takes both sides — only the task changes. The judge is
instructed to weigh the two arguments without factoring in its own views.

## Run

```bash
uv sync
uv run debate "Remote work makes engineering teams more productive"
```

With no argument a default motion is used. One run makes three `gpt-5.4-mini`
calls. Requires `OPENAI_API_KEY` in the repo-root `.env` — see
[../README.md](../README.md) for shared setup.

## Layout

- [src/debate/config/agents.yaml](src/debate/config/agents.yaml) — who the agents are: role, goal, backstory, model
- [src/debate/config/tasks.yaml](src/debate/config/tasks.yaml) — what they do, in declaration order
- [src/debate/crew.py](src/debate/crew.py) — wires the YAML into a sequential crew
- [src/debate/main.py](src/debate/main.py) — entry point: reads the motion, kicks off

The `{motion}` placeholders in the YAML are filled from the `inputs` dict
passed to `kickoff()`, so the same crew debates any motion.
