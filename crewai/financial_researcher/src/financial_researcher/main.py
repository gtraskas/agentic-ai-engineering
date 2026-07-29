"""Run the financial researcher crew from the command line.

Usage (from ``crewai/financial_researcher/``)::

    uv run financial_researcher "Company Name"

With no argument, a default company is used. Requires ``OPENAI_API_KEY``
in the environment or in a ``.env`` file (the repo root one works);
``SERPER_API_KEY`` additionally enables live web search.
"""

import sys
from datetime import UTC, datetime

from dotenv import find_dotenv, load_dotenv

from financial_researcher.crew import FinancialResearcher

DEFAULT_COMPANY = "Apple"


def run() -> None:
    """Kick off the crew on the company given as CLI argument (or default)."""
    load_dotenv(find_dotenv(usecwd=True))
    company = " ".join(sys.argv[1:]).strip() or DEFAULT_COMPANY
    inputs = {"company": company, "current_date": str(datetime.now(tz=UTC).date())}
    print(f"Researching: {company} (as of {inputs['current_date']})\n")
    result = FinancialResearcher().crew().kickoff(inputs=inputs)
    print(f"\nReport:\n{result.raw}")
