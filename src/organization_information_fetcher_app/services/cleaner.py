from typing import Iterable, List

import dateparser
from domains.models import (EmployeeRange, Industry, Organization, Product,
                            RawOrganization)
from ports.referential import Referential
from streamable import Stream


class Cleaner:

    def __init__(
        self, cpc_referential: Referential, isic_referential: Referential
    ) -> None:
        self._cpc_referential = cpc_referential
        self._isic_referential = isic_referential

    @staticmethod
    def _enrich_employee(employees: int) -> EmployeeRange:
        if employees == 1:
            return EmployeeRange.SELF_EMPLOYED
        elif employees < 11:
            return EmployeeRange.RANGE_2_10
        elif employees < 51:
            return EmployeeRange.RANGE_11_50
        elif employees < 201:
            return EmployeeRange.RANGE_51_200
        elif employees < 501:
            return EmployeeRange.RANGE_201_500
        elif employees < 1001:
            return EmployeeRange.RANGE_501_1000
        elif employees < 5001:
            return EmployeeRange.RANGE_1001_5000
        elif employees < 10001:
            return EmployeeRange.RANGE_5001_10000
        else:
            return EmployeeRange.RANGE_10000_PLUS

    def _get_economic_activity(
        self,
        economic_activity: str,
    ) -> Industry:
        """Retrieve ISIC classification based on economic activity."""
        result = self._isic_referential.get_closest_match(economic_activity)

        if not result:
            raise ValueError(f"No ISIC classification found for: {economic_activity}")

        return Industry(**{"isic_id": result.get(0), "value": result.get(1)})

    def _get_products(self, products: Iterable[str]) -> List[Product]:
        def _serialize_product(result: dict) -> Product:
            return Product(cpc_id=str(result.get(0)), value=result.get(1))

        return list(
            Stream(products)
            .map(self._cpc_referential.get_closest_match)
            .map(_serialize_product)
        )

    def serialize_to_organization(
        self, raw_organization: RawOrganization
    ) -> Organization:
        return Organization(
            company_name=raw_organization.company_name,
            creation_date=dateparser.parse(raw_organization.creation_date).date(),
            employees=self._enrich_employee(raw_organization.employees),
            economic_activity_raw=raw_organization.economic_activity,
            economic_activity=self._get_economic_activity(
                raw_organization.economic_activity
            ),
            products_raw=raw_organization.products,
            products=self._get_products(raw_organization.products),
            country_origin=raw_organization.country_origin,
            countries_activity=raw_organization.countries_activity,
            main_company_domains=raw_organization.main_company_domains,
        )
