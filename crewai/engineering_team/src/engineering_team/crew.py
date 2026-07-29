"""Engineering team crew: design, build, demo and test a system.

Four agents work in sequence in a shared sandbox directory. The lead
designs on a stronger model and consults live documentation over MCP;
the three engineers implement, demo and test using the sandbox tools.
Agents and tasks are declared in ``config/agents.yaml`` and
``config/tasks.yaml``.
"""

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from engineering_team.tools.sandbox_tools import sandbox_tools

# Documentation server the lead and frontend engineer consult for current APIs.
CONTEXT7_MCP = "https://mcp.context7.com/mcp"


@CrewBase
class EngineeringTeam:
    """Sequential four-agent crew that builds a working system in a sandbox."""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def engineering_lead(self) -> Agent:
        """Writes the design only; consults live docs over MCP."""
        return Agent(
            config=self.agents_config["engineering_lead"],
            mcps=[CONTEXT7_MCP],
            verbose=True,
        )

    @agent
    def backend_engineer(self) -> Agent:
        """Implements the design as standard-library Python."""
        return Agent(
            config=self.agents_config["backend_engineer"],
            tools=sandbox_tools,
            verbose=True,
        )

    @agent
    def frontend_engineer(self) -> Agent:
        """Writes the Gradio app and validates that it constructs."""
        return Agent(
            config=self.agents_config["frontend_engineer"],
            tools=sandbox_tools,
            mcps=[CONTEXT7_MCP],
            verbose=True,
        )

    @agent
    def test_engineer(self) -> Agent:
        """Writes and runs unit tests, fixing defects until they pass."""
        return Agent(
            config=self.agents_config["test_engineer"],
            tools=sandbox_tools,
            verbose=True,
        )

    @task
    def design_task(self) -> Task:
        """Produce the design; writes ``sandbox/design.md``."""
        return Task(config=self.tasks_config["design_task"])

    @task
    def code_task(self) -> Task:
        """Implement the backend in the sandbox."""
        return Task(config=self.tasks_config["code_task"])

    @task
    def frontend_task(self) -> Task:
        """Write and validate the Gradio app in the sandbox."""
        return Task(config=self.tasks_config["frontend_task"])

    @task
    def test_task(self) -> Task:
        """Test the backend; writes ``sandbox/test_summary.md``."""
        return Task(config=self.tasks_config["test_task"])

    @crew
    def crew(self) -> Crew:
        """Assemble the crew; tasks run in the order declared above."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
