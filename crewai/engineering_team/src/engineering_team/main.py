"""Run the engineering team crew from the command line.

Usage (from ``crewai/engineering_team/``)::

    uv run engineering_team                   # build the default system
    uv run engineering_team requirements.md   # build from your own file

Requires ``OPENAI_API_KEY`` in the environment or in a ``.env`` file (the
repo root one works), and a running Docker daemon: the engineers execute
their code inside a container.
"""

import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

import engineering_team.patch  # noqa: F401 — applies the MCP fix on import
from engineering_team.crew import EngineeringTeam
from engineering_team.tools.sandbox_tools import (
    SANDBOX_DIR,
    ensure_docker_available,
    reset_sandbox,
)

DEFAULT_REQUIREMENTS = """
A simple account management system for a trading simulation platform.
The system should allow users to create an account, deposit funds, and withdraw funds.
The system should allow users to record that they have bought or sold shares, providing a quantity.
The system should calculate the total value of the user's portfolio, and the profit or loss from the initial deposit.
The system should be able to report the holdings of the user at any point in time.
The system should be able to report the profit or loss of the user at any point in time.
The system should be able to list the transactions that the user has made over time.
The system should prevent the user from withdrawing funds that would leave them with a negative balance, or
 from buying more shares than they can afford, or selling shares that they don't have.
 The system has access to a function get_share_price(symbol) which returns the current price of a share, and includes a test implementation that returns fixed prices for AAPL, TSLA, GOOGL.
"""


def _load_requirements() -> str:
    """Return the requirements text from a file argument, or the default.

    Returns:
        The requirements the crew should build.

    Raises:
        SystemExit: If a path was given but no file exists there.
    """
    if len(sys.argv) <= 1:
        return DEFAULT_REQUIREMENTS
    path = Path(sys.argv[1])
    if not path.is_file():
        raise SystemExit(f"No such requirements file: {path}")
    return path.read_text(encoding="utf-8")


def run() -> None:
    """Reset the sandbox and kick off the crew on the requirements."""
    load_dotenv(find_dotenv(usecwd=True))
    ensure_docker_available()
    requirements = _load_requirements()
    print("Preparing a fresh sandbox...\n")
    reset_sandbox()
    result = EngineeringTeam().crew().kickoff(inputs={"requirements": requirements})
    print(f"\n{result.raw}")
    print(f"\nThe team's work is in {SANDBOX_DIR}")
