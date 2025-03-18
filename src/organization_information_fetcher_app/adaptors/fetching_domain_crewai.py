import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
from domains.models import RawOrganization
from googlesearch import search
from ports.fetching import RawOrganizationFetcher

_LOGGER = logging.getLogger(__name__)


@CrewBase
class _FetchingDomainCrew:

    @staticmethod
    @tool("Page Parser")
    def _page_parer_tool(html: str) -> str:
        """Parses the html information to get the raw text from the page."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            return soup.get_text()
        except Exception as e:
            raise RuntimeError(f"Error parsing page: {e}", e)

    @staticmethod
    @tool("Company Web Search")
    def _search_company_tool(company_name: str) -> list[str]:
        """Searches for company relative URLs using {company_name}."""
        try:
            return next(search(company_name))
        except Exception as e:
            raise RuntimeError(f"Error searching for company: {e}", e)

    @staticmethod
    @tool("Page Retriever")
    def _page_retriever_tool(url: str) -> str:
        """Retrieves the page content using the provided URL."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error retrieving page: {e}", e)

    @agent
    def _retriever_agent(self) -> Agent:
        return Agent(
            role="research assistant",
            backstory="You are an helpful research assistant. You have been tasked with compiling information about a company. ",
            goal="You will diligently search for information the best you can.",
            llm="mistral/mistral-tiny",
            max_rpm=60,
            max_execution_time=30,
            tools=[
                self._page_parer_tool,
                self._search_company_tool,
                self._page_retriever_tool,
            ],
            verbose=True,
        )

    @task
    def _formatting_task(self):
        return Task(
            agent=self._retriever_agent(),
            description="Format the company information in the output format",
            expected_output=f"A json object following this schema: {RawOrganization.model_json_schema()}",
            output_pydantic=RawOrganization,
        )

    @task
    def _retrieving_task(self) -> Task:
        return Task(
            agent=self._retriever_agent(),
            description=(
                "Compile company information for {company_name} by crawling the web using the following search query: "
                '"{company_name} company information". '
                "If they are still incomplete you will search for "
                '"{company_name} and the missing information" to find the missing information and compile it with the previous result.'
            ),
            expected_output=f"A json object following this schema: {RawOrganization.model_json_schema()}",
            tools=[
                self._search_company_tool,
                self._page_parer_tool,
                self._page_retriever_tool,
            ],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self._retriever_agent()],
            tasks=[self._formatting_task(), self._retrieving_task()],
            process=Process.sequential,
            verbose=True,
        )


class FetchingDomainCrewAI(RawOrganizationFetcher):

    def __init__(self, fetching_crew: Optional[Crew]) -> None:
        self._crew = fetching_crew or _FetchingDomainCrew().crew()

    def fetch(self, value: str) -> RawOrganization:
        if result := self._crew.kickoff({"company_name": value}).pydantic:
            print(f"Raw Output: {result.raw}")
            if result.json_dict:
                print(f"JSON Output: {result.dumps(result.json_dict, indent=2)}")
            if result.pydantic:
                print(f"Pydantic Output: {result.pydantic}")
            print(f"Tasks Output: {result.tasks_output}")
            print(f"Token Usage: {result.token_usage}")
            if isinstance(result, RawOrganization):
                return result
        else:
            raise RuntimeError("Error fetching company information")
