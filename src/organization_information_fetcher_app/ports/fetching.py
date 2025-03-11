from abc import ABC, abstractmethod

from domains.models import RawOrganization


class RawOrganizationFetcher(ABC):

    @abstractmethod
    def fetch(self, value: str) -> RawOrganization:
        pass
