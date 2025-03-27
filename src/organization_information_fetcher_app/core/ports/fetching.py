from abc import ABC, abstractmethod

from core.entities.organizations import RawOrganization


class RawOrganizationFetcher(ABC):

    @abstractmethod
    def get_raw_organization_information(self, value: str) -> RawOrganization:
        pass
