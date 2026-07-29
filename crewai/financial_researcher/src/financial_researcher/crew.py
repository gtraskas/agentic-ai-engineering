"""Financial researcher crew: web research on a company, then an analyst report.

Agents and tasks are declared in ``config/agents.yaml`` and
``config/tasks.yaml``; this module wires them together into a sequential
crew (research_task -> analysis_task). The analysis task receives the
research output through its ``context`` declaration in the YAML.
"""

import os

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool


def _research_tools() -> list[SerperDevTool]:
    """Return the web-search tool when a Serper API key is configured.

    Without ``SERPER_API_KEY`` the researcher agent falls back to the
    model's own knowledge, so the crew still runs — the report is just
    not current.
    """
    return [SerperDevTool()] if os.getenv("SERPER_API_KEY") else []


@CrewBase
class FinancialResearcher:
    """Sequential two-agent crew that researches a company and writes a report."""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def researcher(self) -> Agent:
        """The researcher gathers current information, searching the web if possible."""
        return Agent(
            config=self.agents_config["researcher"],
            tools=_research_tools(),
            verbose=True,
        )

    @agent
    def analyst(self) -> Agent:
        """The analyst turns the research into a structured report."""
        return Agent(config=self.agents_config["analyst"], verbose=True)

    @task
    def research_task(self) -> Task:
        """Research the company; output feeds the analysis task."""
        return Task(config=self.tasks_config["research_task"])

    @task
    def analysis_task(self) -> Task:
        """Write the report from the research; writes ``output/report.md``."""
        return Task(config=self.tasks_config["analysis_task"])

    @crew
    def crew(self) -> Crew:
        """Assemble the crew; tasks run in the order declared above."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
