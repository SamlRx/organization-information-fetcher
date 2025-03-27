import csv
import os
from typing import Iterator

from core.application import InformationFetcher
from core.domains.cleaner import Cleaner
from dotenv import load_dotenv
from infrastructure.adapters.fetching_agent import (
    RawOrganizationFetcherFromCompanyNameBuilder,
)
from infrastructure.repositories.referential_csv import CsvReferentialBuilder
from infrastructure.repositories.sinker_csv import SinkerCsv


def companies(path: str) -> Iterator[str]:
    with open(path, newline="", encoding="utf-8") as file:
        for row in csv.reader(file):
            yield row[0]


def main():

    # Environment variables
    load_dotenv()
    os.environ["MISTRAL_API_KEY"] = os.getenv("MISTRAL_API_KEY")

    cpc_referential = CsvReferentialBuilder.build("resources/cpc_ver3.csv")
    isic_referential = CsvReferentialBuilder.build("resources/isic_rev5.csv")

    # Load the company_names
    cleaner = Cleaner(cpc_referential, isic_referential)
    fetcher = (
        RawOrganizationFetcherFromCompanyNameBuilder()
        .with_standard_rate_limiter()
        .with_mistral_ai()
        .build()
    )
    sinker = SinkerCsv("./organizations.csv")

    # Run the application
    InformationFetcher(fetcher, cleaner, sinker)(companies("resources/companies.csv"))


if __name__ == "__main__":
    main()
