from typing import List
from unittest.mock import MagicMock, patch

import pytest
import requests
from core.entities.organizations import RawOrganization
from infrastructure.adapters.fetching_agent import (
    RawOrganizationFetcherFromCompanyName,
    RawOrganizationFetcherFromCompanyNameBuilder,
)


def test_with_standard_rate_limiter() -> None:
    # Given a builder instance
    builder = RawOrganizationFetcherFromCompanyNameBuilder()

    # When setting the standard rate limiter
    builder.with_standard_rate_limiter()

    # Then the rate limiter should be set
    assert builder._rate_limiter is not None


def test_with_mistral_ai_without_rate_limiter() -> None:
    # Given a builder without a rate limiter
    builder = RawOrganizationFetcherFromCompanyNameBuilder()

    # When calling with_mistral_ai, Then it should raise a ValueError
    with pytest.raises(
        ValueError, match="Rate limiter must be set before initializing LLM"
    ):
        builder.with_mistral_ai()


def test_retrieve_page_success() -> None:
    # Given a valid URL
    url = "http://example.com"
    mock_response = MagicMock()
    mock_response.text = "<html><body>Test Page</body></html>"

    with patch("requests.get", return_value=mock_response):
        # When calling retrieve_page
        result: str = RawOrganizationFetcherFromCompanyNameBuilder.retrieve_page(url)

        # Then it should return the page HTML
        assert "Test Page" in result


def test_retrieve_page_failure() -> None:
    # Given an invalid URL
    url = "http://invalid-url.com"
    with patch(
        "requests.get",
        side_effect=requests.exceptions.RequestException("Network error"),
    ):
        # When calling retrieve_page, Then it should raise a ValueError
        with pytest.raises(
            ValueError, match="Error retrieving http://invalid-url.com."
        ):
            RawOrganizationFetcherFromCompanyNameBuilder.retrieve_page(url)


def test_parse_page_success() -> None:
    # Given a valid HTML string
    html = "<html><body><p>Company Info</p></body></html>"

    # When calling parse_page
    result: str = RawOrganizationFetcherFromCompanyNameBuilder.parse_page(html)

    # Then it should return parsed text
    assert "Company Info" in result


def test_search_company_success() -> None:
    # Given a company name
    company_name = "Test Company"
    mock_results: List[str] = [
        "http://testcompany.com",
        "http://linkedin.com/testcompany",
    ]

    with patch(
        "infrastructure.adapters.fetching_agent.search", return_value=mock_results
    ):
        # When calling search_company
        result: List[str] = RawOrganizationFetcherFromCompanyNameBuilder.search_company(
            company_name
        )

        # Then it should return search results
        assert result == mock_results


def test_search_company_failure() -> None:
    # Given a company name that causes an exception
    with patch(
        "infrastructure.adapters.fetching_agent.search",
        side_effect=Exception("Search error"),
    ):
        # When calling search_company, Then it should raise a ValueError
        with pytest.raises(
            ValueError, match="Error searching for company Test Company"
        ):
            RawOrganizationFetcherFromCompanyNameBuilder.search_company("Test Company")


def test_fetch_incomplete_result() -> None:
    # Given a fetcher instance with an incomplete result
    agent_mock = MagicMock()
    agent_mock.invoke.return_value = {"properties": {"name": "Test Corp"}}

    llm_mock = MagicMock()
    llm_mock.with_structured_output.return_value.invoke.return_value = RawOrganization(
        company_name="Test Corp",
        creation_date="2021-01-01",
        employees=20,
        economic_activity="Software development",
        products=["A", "B"],
        product_names=["Product A", "Product B"],
        country_origin="US",
        countries_activity=["US"],
        main_company_domains=["testcorp.com"],
    )

    fetcher = RawOrganizationFetcherFromCompanyName(agent_mock, llm_mock)

    # When calling fetch
    result: RawOrganization = fetcher.get_raw_organization_information("Test Corp")

    # Then it should return a structured RawOrganization object
    assert isinstance(result, RawOrganization)
    assert result.company_name == "Test Corp"
    assert result.creation_date == "2021-01-01"
    assert result.employees == 20
    assert result.economic_activity == "Software development"
    assert result.products == ["A", "B"]
    assert result.product_names == ["Product A", "Product B"]
    assert result.country_origin == "US"
    assert result.countries_activity == ["US"]
    assert result.main_company_domains == ["testcorp.com"]
    agent_mock.invoke.assert_called_once()
