from abc import ABC, abstractmethod

from pydantic import BaseModel


class Sinker(ABC):

    @abstractmethod
    def sink_organization(self, data: BaseModel) -> None:
        pass
