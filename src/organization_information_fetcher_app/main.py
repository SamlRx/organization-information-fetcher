import csv
import os
from typing import Iterator

from adaptors.fetching_domain_langchain import (
    RawOrganizationFetcherFromCompanyNameBuilder,
)
from dotenv import load_dotenv
from repository.referential_csv import CsvReferentialBuilder
from repository.sinker_csv import SinkerCsv
from services.cleaner import Cleaner
from streamable import Stream


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

    list(
        Stream(list(companies("resources/company_names.csv")))
        .map(fetcher.fetch)
        .map(cleaner.serialize_to_organization)
        .map(sinker.sink)
    )

    sinker.flush()


if __name__ == "__main__":
    main()
