import logging
from typing import Any, Dict, Optional, Self

import requests
from bs4 import BeautifulSoup
from domains.models import RawOrganization
from googlesearch import search
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import Tool
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_mistralai import ChatMistralAI
from ports.fetching import RawOrganizationFetcher
from streamable import Stream

_LOGGER = logging.getLogger(__name__)


class RawOrganizationFetcherFromCompanyName(RawOrganizationFetcher):

    def __init__(
        self, agent: AgentExecutor, llm: BaseChatModel, max_iterations: int = 5
    ) -> None:
        _LOGGER.debug(
            "Creating RawOrganizationFetcherFromCompanyName with agent: %s and LLM: %s",
            agent,
            llm,
        )
        self._agent = agent
        self._llm = llm
        self._max_iterations = max_iterations

    def _format_result(self, raw_value: Dict[str, Any]) -> Dict | RawOrganization:
        return self._llm.with_structured_output(RawOrganization).invoke(
            f"Extract and structure the following company data: {raw_value.get("properties")}"
        )

    @staticmethod
    def _is_complete(org: RawOrganization) -> bool:
        return all(value is not None for value in org.model_dump().values())

    @staticmethod
    def _get_missing_fields(org: RawOrganization) -> list[str]:
        return list(
            Stream(org.model_dump().items())
            .filter(lambda x: x[1] is None)
            .map(lambda x: x[0])
        )

    def fetch(self, value: str) -> RawOrganization:
        initial_prompt = f"""
            Compile company information for {value} by crawling the web using the following search query: "{value} company information".
            Use all the pages to compile the most complete information possible for this object: {RawOrganization.model_json_schema()}.
            If they are still incomplete you will search for "{value} and the missing information" to find the missing information and compile it with the previous result.
        """

        raw_result = self._agent.invoke({"input": initial_prompt})
        structured_result = self._format_result(raw_result)

        if self._is_complete(structured_result):
            return structured_result

        structured_result = self._refine_result(structured_result, value)

        return structured_result

    def _refine_result(
        self, structured_result: RawOrganization, value: str
    ) -> RawOrganization:
        self._cache: Dict[str, Dict[str, Any]]
        for _ in range(self._max_iterations):
            missing_fields = self._get_missing_fields(structured_result)
            if not missing_fields:
                break

            missing_fields_str = ", ".join(missing_fields)
            refinement_prompt = f"""
                You previously gathered some information for {value}. However, the following fields are still missing: {missing_fields_str}.
                Please find and provide the missing information using relevant web searches.
                Compile the new information with the existing data: {structured_result.model_dump()}.
                Output the result as a complete {RawOrganization.model_json_schema()}.
            """

            raw_result = self._agent.invoke({"input": refinement_prompt})
            structured_result = self._format_result(raw_result)
        return structured_result


class RawOrganizationFetcherFromCompanyNameBuilder:
    _llm: Optional[BaseChatModel] = None
    _rate_limiter: Optional[InMemoryRateLimiter] = None

    def with_standard_rate_limiter(self) -> Self:
        self._rate_limiter = InMemoryRateLimiter(
            requests_per_second=0.5, check_every_n_seconds=0.1
        )
        return self

    def with_mistral_ai(self) -> Self:
        if not self._rate_limiter:
            raise ValueError("Rate limiter must be set before initializing LLM.")

        self._llm = ChatMistralAI(
            model="mistral-small-2501", temperature=0.1, rate_limiter=self._rate_limiter  # type: ignore
        )
        return self

    @staticmethod
    def retrieve_page(url: str) -> str:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.text
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error retrieving {url}.", e)

    @staticmethod
    def parse_page(html: str) -> str:
        try:
            soup = BeautifulSoup(html, "html.parser")
            return soup.get_text()
        except Exception as e:
            raise ValueError("Error parsing.", e)

    @staticmethod
    def search_company(company_name: str) -> list[str]:
        try:
            print(f"Searching for company: {company_name}")
            return next(search(company_name))
        except Exception as e:
            raise ValueError(f"Error searching for company {company_name}.", e)

    def build(self) -> RawOrganizationFetcherFromCompanyName:
        if not self._llm:
            raise ValueError(
                "LLM must be set before building the RawOrganizationFetcherFromCompanyName."
            )

        search_tool = Tool(
            name="Company Web Search",
            func=self.search_company,
            description="Searches for company relative URLs.",
        )

        page_retriever = Tool(
            name="Page Retriever",
            func=self.retrieve_page,
            description="Retrieves the company page.",
        )

        page_parser = Tool(
            name="Page Parser",
            func=self.parse_page,
            description="Parses the company information from the page.",
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an helpful research assistant. "
                    "You have been tasked with compiling information about a company. "
                    "You will search for the company and compile the information you find.",
                ),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        return RawOrganizationFetcherFromCompanyName(
            AgentExecutor(
                agent=create_tool_calling_agent(
                    self._llm,
                    tools=[search_tool, page_retriever, page_parser],
                    prompt=prompt,
                ),
                tools=[search_tool, page_retriever, page_parser],
                verbose=True,
                handle_parsing_errors=True,
            ),
            llm=self._llm,
        )
