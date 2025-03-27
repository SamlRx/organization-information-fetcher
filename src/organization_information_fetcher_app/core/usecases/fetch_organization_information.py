from typing import Iterable

from core.domains.cleaner import Cleaner
from core.ports.fetching import RawOrganizationFetcher
from core.ports.sinker import Sinker
from streamable import Stream


class FetchOrganizationInformation:

    def __init__(
        self, fetcher: RawOrganizationFetcher, cleaner: Cleaner, sinker: Sinker
    ) -> None:
        self._fetcher = fetcher
        self._cleaner = cleaner
        self._sinker = sinker

    def __call__(self, companies: Iterable[str]) -> None:
        list(
            Stream(companies)
            .map(self._fetcher.get_raw_organization_information)  # adapters
            .map(self._cleaner.serialize_to_organization)  # domains
            .map(self._sinker.sink_organization)  # repositories
        )
