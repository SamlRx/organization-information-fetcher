import os

from adaptors.fetching_domain_crewai import FetchingDomainCrewAI
from dotenv import load_dotenv
from repository.referential_csv import CsvReferentialBuilder
from services.cleaner import Cleaner


def main():

    # Environment variables
    load_dotenv()
    os.environ["MISTRAL_API_KEY"] = os.getenv("MISTRAL_API_KEY")

    cpc_referential = CsvReferentialBuilder.build("resources/cpc_ver3.csv")
    isic_referential = CsvReferentialBuilder.build("resources/isic_rev5.csv")

    cleaner = Cleaner(cpc_referential, isic_referential)

    fetcher = FetchingDomainCrewAI()

    company_name = "Hubspot"
    raw_organization = fetcher.fetch(company_name)
    cleaned_data = cleaner.serialize_to_organization(raw_organization)

    print(cleaned_data)


if __name__ == "__main__":
    main()
