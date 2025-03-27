from typing import Generator, List
from unittest.mock import MagicMock

import pytest
from core.domains.cleaner import Cleaner
from core.ports.fetching import RawOrganizationFetcher
from core.ports.sinker import Sinker
from core.usecases.fetch_organization_information import FetchOrganizationInformation


@pytest.fixture
def mock_fetcher() -> Generator[MagicMock, None, None]:
    fetcher = MagicMock(spec=RawOrganizationFetcher)
    fetcher.get_raw_organization_information.side_effect = lambda x: f"raw_{x}"
    yield fetcher


@pytest.fixture
def mock_cleaner() -> Generator[MagicMock, None, None]:
    cleaner = MagicMock(spec=Cleaner)
    cleaner.serialize_to_organization.side_effect = lambda x: f"clean_{x}"
    yield cleaner


@pytest.fixture
def mock_sinker() -> Generator[MagicMock, None, None]:
    sinker = MagicMock(spec=Sinker)
    sinker.sink_organization.side_effect = lambda x: None
    yield sinker


def test_fetch_organization_information(
    mock_fetcher: MagicMock, mock_cleaner: MagicMock, mock_sinker: MagicMock
) -> None:
    # Given a FetchOrganizationInformation instance
    fetch_organization_info = FetchOrganizationInformation(
        fetcher=mock_fetcher,
        cleaner=mock_cleaner,
        sinker=mock_sinker,
    )

    companies: List[str] = ["CompanyA", "CompanyB"]

    # when calling fetch_organization_info
    fetch_organization_info(companies)

    # Then it should call the fetcher, cleaner, and sinker for each company
    mock_fetcher.get_raw_organization_information.assert_any_call("CompanyA")
    mock_fetcher.get_raw_organization_information.assert_any_call("CompanyB")
    assert mock_fetcher.get_raw_organization_information.call_count == len(companies)

    mock_cleaner.serialize_to_organization.assert_any_call("raw_CompanyA")
    mock_cleaner.serialize_to_organization.assert_any_call("raw_CompanyB")
    assert mock_cleaner.serialize_to_organization.call_count == len(companies)

    mock_sinker.sink_organization.assert_any_call("clean_raw_CompanyA")
    mock_sinker.sink_organization.assert_any_call("clean_raw_CompanyB")
    assert mock_sinker.sink_organization.call_count == len(companies)
