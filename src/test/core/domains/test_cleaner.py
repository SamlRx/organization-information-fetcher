from datetime import date
from unittest.mock import MagicMock

import pytest
from core.domains.cleaner import Cleaner
from core.entities.organizations import EmployeeRange, Organization, RawOrganization
from core.ports.referential import Referential


# Adding explicit return type for mock_referentials fixture
@pytest.fixture
def mock_referentials() -> (
    tuple[Referential, Referential]
):  # Specify the return type explicitly
    cpc_mock: MagicMock = MagicMock(spec=Referential)
    isic_mock: MagicMock = MagicMock(spec=Referential)

    # Mock CPC referential
    cpc_mock.get_closest_match.side_effect = lambda x: (
        {0: "CPC-123", 1: x} if x else None
    )

    # Mock ISIC referential
    isic_mock.get_closest_match.side_effect = lambda x: (
        {0: "ISIC-456", 1: x} if x else None
    )

    return cpc_mock, isic_mock


# Adding explicit return type for cleaner fixture
@pytest.fixture
def cleaner(mock_referentials: tuple[Referential, Referential]) -> Cleaner:
    cpc_mock, isic_mock = mock_referentials
    return Cleaner(cpc_mock, isic_mock)


# Explicitly typing raw_organization return value
@pytest.fixture
def raw_organization() -> RawOrganization:
    return RawOrganization(
        company_name="Test Company",
        creation_date="2020-01-01",
        employees=25,
        economic_activity="Software Development",
        product_names=["SaaS Platform"],
        products=["SaaS Platform"],
        country_origin="USA",
        countries_activity=["USA"],
        main_company_domains=["test.com"],
    )


# Test functions don't need to be typed explicitly, since pytest handles them.
def test_serialize_to_organization(
    cleaner: Cleaner, raw_organization: RawOrganization
) -> None:
    # Given a raw organization with valid data

    # When calling serialize_to_organization
    result: Organization = cleaner.serialize_to_organization(raw_organization)

    # Then it should return an Organization object with expected values
    assert isinstance(result, Organization)
    assert result.company_name == "Test Company"
    assert result.creation_date == date(2020, 1, 1)
    assert result.employees == EmployeeRange.RANGE_11_50
    assert result.economic_activity.isic_id == "ISIC-456"
    assert result.economic_activity.value == "Software Development"
    assert result.products[0].cpc_id == "CPC-123"
    assert result.products[0].value == "SaaS Platform"
    assert result.country_origin == "USA"  # Changed to match the expected attribute
    assert result.main_company_domains == ["test.com"]


def test_serialize_to_organization_empty_products(
    cleaner: Cleaner,
    raw_organization: RawOrganization,
    mock_referentials: tuple[Referential, Referential],
) -> None:
    # Given a raw organization with no products
    raw_organization.products = []
    mock_referentials[0].get_closest_match.side_effect = (
        lambda x: None
    )  # CPC referential returns no match

    # When calling serialize_to_organization
    result: Organization = cleaner.serialize_to_organization(raw_organization)

    # Then it should return an Organization object with an empty products list
    assert isinstance(result, Organization)
    assert result.products == []
