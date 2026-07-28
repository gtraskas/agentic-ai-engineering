"""Debate crew: one debater argues both sides of a motion, a judge decides.

Agents and tasks are declared in ``config/agents.yaml`` and
``config/tasks.yaml``; this module wires them together into a sequential
crew (propose -> oppose -> decide).
"""

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class Debate:
    """Sequential two-agent crew that debates a motion and picks a winner."""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def debater(self) -> Agent:
        """The debater argues each side of the motion in turn."""
        return Agent(config=self.agents_config["debater"], verbose=True)

    @agent
    def judge(self) -> Agent:
        """The judge weighs both arguments and declares a winner."""
        return Agent(config=self.agents_config["judge"], verbose=True)

    @task
    def propose(self) -> Task:
        """Argue in favor of the motion; writes ``output/propose.md``."""
        return Task(config=self.tasks_config["propose"])

    @task
    def oppose(self) -> Task:
        """Argue against the motion; writes ``output/oppose.md``."""
        return Task(config=self.tasks_config["oppose"])

    @task
    def decide(self) -> Task:
        """Judge the two arguments; writes ``output/decide.md``."""
        return Task(config=self.tasks_config["decide"])

    @crew
    def crew(self) -> Crew:
        """Assemble the crew; tasks run in the order declared above."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
