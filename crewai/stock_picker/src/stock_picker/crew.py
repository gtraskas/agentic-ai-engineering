"""Stock picker crew: find trending companies, research them, pick one.

A manager agent runs the show (``Process.hierarchical``) and delegates
to three specialists declared in ``config/agents.yaml``. Tasks return
validated Pydantic objects (``output_pydantic``), and crew memory keeps
earlier picks out of later runs. Educational demo — not investment
advice.
"""

import os

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field

from stock_picker.tools.notify_tool import send_notification


class TrendingCompany(BaseModel):
    """A company that is in the news and attracting attention."""

    name: str = Field(description="Company name")
    ticker: str = Field(description="Stock ticker symbol")
    reason: str = Field(description="Reason this company is trending in the news")


class TrendingCompanyList(BaseModel):
    """List of multiple trending companies that are in the news."""

    companies: list[TrendingCompany] = Field(description="List of companies trending in the news")


class TrendingCompanyResearch(BaseModel):
    """Detailed research on a company."""

    name: str = Field(description="Company name")
    market_position: str = Field(description="Current market position and competitive analysis")
    future_outlook: str = Field(description="Future outlook and growth prospects")
    investment_potential: str = Field(description="Investment potential and suitability for investment")


class TrendingCompanyResearchList(BaseModel):
    """A list of detailed research on all the companies."""

    research_list: list[TrendingCompanyResearch] = Field(
        description="Comprehensive research on all trending companies"
    )


def _search_tools() -> list[SerperDevTool]:
    """Return the web-search tool when a Serper API key is configured.

    Without ``SERPER_API_KEY`` the agents fall back to the model's own
    knowledge, so the crew still runs — the picks are just not current.
    """
    return [SerperDevTool()] if os.getenv("SERPER_API_KEY") else []


@CrewBase
class StockPicker:
    """Hierarchical crew that finds, researches and picks a company."""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def trending_company_finder(self) -> Agent:
        """Scans the news for 2-3 companies trending in the sector."""
        return Agent(
            config=self.agents_config["trending_company_finder"],
            tools=_search_tools(),
            memory=True,
        )

    @agent
    def financial_researcher(self) -> Agent:
        """Researches each trending company in depth."""
        return Agent(
            config=self.agents_config["financial_researcher"],
            tools=_search_tools(),
            memory=True,
        )

    @agent
    def stock_picker(self) -> Agent:
        """Picks the best company and notifies the user with its tool."""
        return Agent(
            config=self.agents_config["stock_picker"],
            tools=[send_notification],
            memory=True,
        )

    @task
    def find_trending_companies(self) -> Task:
        """Find trending companies; returns a validated TrendingCompanyList."""
        return Task(
            config=self.tasks_config["find_trending_companies"],
            output_pydantic=TrendingCompanyList,
        )

    @task
    def research_trending_companies(self) -> Task:
        """Research each company; returns a validated TrendingCompanyResearchList."""
        return Task(
            config=self.tasks_config["research_trending_companies"],
            output_pydantic=TrendingCompanyResearchList,
        )

    @task
    def pick_best_company(self) -> Task:
        """Pick the winner, notify the user, write ``output/decision.md``."""
        return Task(config=self.tasks_config["pick_best_company"])

    @crew
    def crew(self) -> Crew:
        """Assemble the hierarchical crew under a delegating manager.

        The manager is created here rather than with ``@agent`` so it
        stays out of ``self.agents`` — a hierarchical crew requires the
        manager to not be one of the worker agents.
        """
        manager = Agent(config=self.agents_config["manager"], allow_delegation=True)
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=manager,
            memory=True,
            verbose=True,
        )
