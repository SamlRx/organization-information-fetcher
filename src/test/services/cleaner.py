from datetime import date
from unittest.mock import MagicMock

import pytest
from domains.models import EmployeeRange, Organization, RawOrganization
from ports.referential import Referential
from services.cleaner import Cleaner


@pytest.fixture
def mock_referentials():
    cpc_mock = MagicMock(spec=Referential)
    isic_mock = MagicMock(spec=Referential)

    # Mock CPC referential
    cpc_mock.get_closest_match.side_effect = lambda x: (
        {0: "CPC-123", 1: x} if x else None
    )

    # Mock ISIC referential
    isic_mock.get_closest_match.side_effect = lambda x: (
        {0: "ISIC-456", 1: x} if x else None
    )

    return cpc_mock, isic_mock


@pytest.fixture
def cleaner(mock_referentials):
    cpc_mock, isic_mock = mock_referentials
    return Cleaner(cpc_mock, isic_mock)


@pytest.fixture
def raw_organization():
    return RawOrganization(
        company_name="Test Company",
        creation_date="2020-01-01",
        employees=25,
        economic_activity="Software Development",
        products=["SaaS Platform"],
        countries=["USA"],
        main_company_domains=["test.com"],
    )


def test_serialize_to_organization(cleaner, raw_organization):
    # Given a raw organization with valid data

    # When calling serialize_to_organization
    result = cleaner.serialize_to_organization(raw_organization)

    # Then it should return an Organization object with expected values
    assert isinstance(result, Organization)
    assert result.company_name == "Test Company"
    assert result.creation_date == date(2020, 1, 1)
    assert result.employees == EmployeeRange.RANGE_11_50
    assert result.economic_activity.isic_id == "ISIC-456"
    assert result.economic_activity.value == "Software Development"
    assert result.products[0].cpc_id == "CPC-123"
    assert result.products[0].value == "SaaS Platform"
    assert result.countries == ["USA"]
    assert result.main_company_domains == ["test.com"]


def test_serialize_to_organization_invalid_activity(
    cleaner, raw_organization, mock_referentials
):
    # Given a raw organization with an invalid economic activity
    raw_organization.economic_activity = "Unknown Activity"
    mock_referentials[1].get_closest_match.return_value = (
        None  # ISIC referential returns no match
    )

    # When / Then: Expect ValueError
    with pytest.raises(
        ValueError, match="No ISIC classification found for: Unknown Activity"
    ):
        cleaner.serialize_to_organization(raw_organization)


def test_serialize_to_organization_empty_products(
    cleaner, raw_organization, mock_referentials
):
    # Given a raw organization with no products
    raw_organization.products = []
    mock_referentials[0].get_closest_match.side_effect = (
        lambda x: None
    )  # CPC referential returns no match

    # When calling serialize_to_organization
    result = cleaner.serialize_to_organization(raw_organization)

    # Then it should return an Organization object with an empty products list
    assert isinstance(result, Organization)
    assert result.products == []
