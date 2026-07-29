"""File and execution tools scoped to the agents' sandbox directory.

The agents write code to ``sandbox/`` and run it inside an ephemeral
Docker container with only that directory mounted, so model-written code
never executes directly on the host. The container is removed after every
call (``--rm``) and each run is bounded by a timeout.

The sandbox is a uv project with gradio declared as a dependency; the
container resolves and installs it on the first run.
"""

import shutil
import subprocess
import uuid
from pathlib import Path

from crewai.tools import tool

SANDBOX_DIR = Path(__file__).parents[3] / "sandbox"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

RUNNER_IMAGE = "ghcr.io/astral-sh/uv:python3.13-bookworm-slim"
RUN_TIMEOUT_SECONDS = 300
MAX_OUTPUT_CHARS = 10_000


def ensure_docker_available() -> None:
    """Raise SystemExit with a clear message when Docker cannot be used.

    Raises:
        SystemExit: If the docker CLI is missing or the daemon is not running.
    """
    if shutil.which("docker") is None:
        raise SystemExit(
            "Docker is required to run this crew: the agents execute their code "
            "inside a container. Install Docker Desktop from "
            "https://www.docker.com/products/docker-desktop/ and try again."
        )
    probe = subprocess.run(["docker", "info"], capture_output=True, text=True, check=False)
    if probe.returncode != 0:
        raise SystemExit(
            "Docker is installed but the daemon is not running. Start Docker "
            "Desktop, wait for it to report Running, and try again."
        )


def reset_sandbox() -> None:
    """Wipe the sandbox and re-initialize it as a uv project with gradio.

    Dependencies are declared but not installed here: the container
    installs them for Linux on the first run, so no host-built virtual
    environment is left behind in the sandbox.
    """
    if SANDBOX_DIR.exists():
        shutil.rmtree(SANDBOX_DIR)
    SANDBOX_DIR.mkdir(parents=True)
    subprocess.run(
        ["uv", "init", "--bare", "--python", "3.13"],
        cwd=SANDBOX_DIR,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["uv", "add", "--no-sync", "gradio"],
        cwd=SANDBOX_DIR,
        check=True,
        capture_output=True,
    )


def _truncate(text: str) -> str:
    """Cap tool output so a chatty script cannot flood the agent's context."""
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return f"{text[:MAX_OUTPUT_CHARS]}\n... output truncated ..."


def _sandbox_path(filename: str) -> Path | None:
    """Resolve a filename inside the sandbox, refusing anything that escapes.

    An agent is free to propose any filename, so absolute paths, ``..``
    segments and symlinks out of the directory must not be honoured: the
    sandbox is the boundary that keeps model-written files away from the
    rest of the machine.

    Args:
        filename: The filename an agent asked for.

    Returns:
        The resolved path, or None if it falls outside the sandbox.
    """
    sandbox = SANDBOX_DIR.resolve()
    candidate = (sandbox / filename).resolve()
    if sandbox not in candidate.parents:
        return None
    return candidate


@tool("List Sandbox Files")
def list_sandbox_files() -> str:
    """List the filenames currently in the sandbox directory.

    Returns:
        A newline-separated list of filenames, or a message if the
        sandbox is empty.
    """
    names = sorted(p.name for p in SANDBOX_DIR.iterdir())
    return "\n".join(names) if names else "The sandbox is empty."


@tool("Read Sandbox File")
def read_sandbox_file(filename: str) -> str:
    """Read and return the text contents of a file in the sandbox directory.

    Args:
        filename: The name of the file to read (e.g. "solution.py").

    Returns:
        The file's contents, or a message if the file does not exist.
    """
    path = _sandbox_path(filename)
    if path is None:
        return f"Refused: {filename} is outside the sandbox directory."
    if not path.is_file():
        return f"No such file in the sandbox: {filename}"
    return _truncate(path.read_text(encoding="utf-8"))


@tool("Write Sandbox File")
def write_sandbox_file(filename: str, content: str) -> str:
    """Write text to a file in the sandbox directory, replacing any existing
    file with the same name.

    Args:
        filename: The name of the file to write (e.g. "solution.py").
        content: The text content to write.

    Returns:
        A confirmation message, or a refusal if the path escapes the sandbox.
    """
    path = _sandbox_path(filename)
    if path is None:
        return f"Refused: {filename} is outside the sandbox directory."
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {filename}."


@tool("Run Sandbox Python File")
def run_sandbox_python(filename: str) -> str:
    """Execute a Python file from the sandbox directory inside an ephemeral
    Docker container, with the sandbox mounted as the working directory, and
    return everything the script printed.

    Both stdout and stderr are returned, so tracebacks and unittest results
    are visible. A non-zero exit code is reported explicitly.

    Args:
        filename: The name of the Python file to run (e.g. "solution.py").

    Returns:
        The script's output, or a message explaining why it could not run.
    """
    path = _sandbox_path(filename)
    if path is None:
        return f"Refused: {filename} is outside the sandbox directory."
    if not path.is_file():
        return f"No such file in the sandbox: {filename}"
    # Naming the container gives us a handle to remove it on timeout: killing the
    # docker client would otherwise leave the container running in the daemon,
    # where --rm never fires because the container never exits.
    container = f"engineering-team-{uuid.uuid4().hex[:12]}"
    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm", "--name", container,
                "-v", f"{SANDBOX_DIR}:/workspace",
                "-w", "/workspace",
                RUNNER_IMAGE,
                "uv", "run", filename,
            ],
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        return "Docker is not available, so the script could not be run."
    except subprocess.TimeoutExpired:
        subprocess.run(
            ["docker", "rm", "--force", container],
            capture_output=True,
            check=False,
        )
        return (
            f"The script did not finish within {RUN_TIMEOUT_SECONDS} seconds, so "
            "it was stopped and its container removed. Check for an infinite loop "
            "or a blocking call such as launch()."
        )

    sections = []
    if result.stdout.strip():
        sections.append(f"stdout:\n{result.stdout}")
    if result.stderr.strip():
        sections.append(f"stderr:\n{result.stderr}")
    if result.returncode != 0:
        sections.append(f"The script exited with code {result.returncode}.")
    if not sections:
        return "The script ran successfully and produced no output."
    return _truncate("\n\n".join(sections))


sandbox_tools = [
    list_sandbox_files,
    read_sandbox_file,
    write_sandbox_file,
    run_sandbox_python,
]


def _never_cache(*_args: object, **_kwargs: object) -> bool:
    """Tool-cache predicate that always refuses to cache."""
    return False


# Sandbox state changes between calls (files appear, change and run), so caching
# tool results would feed agents stale data. Opt out of CrewAI's tool caching.
for _sandbox_tool in sandbox_tools:
    _sandbox_tool.cache_function = _never_cache
