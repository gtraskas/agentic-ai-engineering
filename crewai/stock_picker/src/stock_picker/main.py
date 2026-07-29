"""Run the stock picker crew from the command line.

Usage (from ``crewai/stock_picker/``)::

    uv run stock_picker "Sector Name"

With no argument, a default sector is used. Requires ``OPENAI_API_KEY``
in the environment or in a ``.env`` file (the repo root one works).
``SERPER_API_KEY`` enables live news search; ``GMAIL_ADDRESS`` and
``GMAIL_APP_PASSWORD`` enable the email notification. Crew memory is
stored under this project's ``memory/`` directory (gitignored).
"""

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from stock_picker.crew import StockPicker

DEFAULT_SECTOR = "Technology"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run() -> None:
    """Kick off the crew on the sector given as CLI argument (or default)."""
    load_dotenv(find_dotenv(usecwd=True))
    os.environ.setdefault("CREWAI_STORAGE_DIR", str(PROJECT_ROOT / "memory"))
    sector = " ".join(sys.argv[1:]).strip() or DEFAULT_SECTOR
    inputs = {"sector": sector, "current_date": str(datetime.now(tz=UTC).date())}
    print(f"Picking a stock in: {sector} (as of {inputs['current_date']})\n")
    result = StockPicker().crew().kickoff(inputs=inputs)
    print(f"\nDecision:\n{result.raw}")
