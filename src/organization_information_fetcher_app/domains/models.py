from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class EmployeeRange(str, Enum):
    SELF_EMPLOYED = "Self Employee"
    RANGE_2_10 = "2 - 10 employees"
    RANGE_11_50 = "11 - 50 employees"
    RANGE_51_200 = "51 - 200 employees"
    RANGE_201_500 = "201 - 500 employees"
    RANGE_501_1000 = "501 - 1000 employees"
    RANGE_1001_5000 = "1001 - 5000 employees"
    RANGE_5001_10000 = "5001 - 10 000 employees"
    RANGE_10000_PLUS = "10 000+ employees"


class Industry(BaseModel):
    isic_id: str
    value: str


class Product(BaseModel):
    cpc_id: str
    value: str


class RawOrganization(BaseModel):
    company_name: str
    creation_date: str
    employees: int
    economic_activity: str
    products: List[str]
    product_names: List[str]
    country_origin: str
    countries_activity: List[str]
    main_company_domains: List[str]


class Organization(BaseModel):
    company_name: str
    creation_date: date
    employees: EmployeeRange
    economic_activity_raw: str
    economic_activity: Industry
    products_raw: List[str]
    products: List[Product]
    country_origin: str
    countries_activity: List[str]
    main_company_domains: List[str]
