"""Run the debate crew from the command line.

Usage (from ``crewai/debate/``)::

    uv run debate "The motion to debate"

With no argument, a default motion is used. Requires ``OPENAI_API_KEY``
in the environment or in a ``.env`` file (the repo root one works).
"""

import sys

from dotenv import find_dotenv, load_dotenv

from debate.crew import Debate

DEFAULT_MOTION = "There need to be strict laws to regulate LLMs"


def run() -> None:
    """Kick off the crew on the motion given as CLI argument (or default)."""
    load_dotenv(find_dotenv(usecwd=True))
    motion = " ".join(sys.argv[1:]).strip() or DEFAULT_MOTION
    print(f"Motion: {motion}\n")
    result = Debate().crew().kickoff(inputs={"motion": motion})
    print(f"\nVerdict:\n{result.raw}")
