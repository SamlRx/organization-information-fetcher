from abc import ABC, abstractmethod

from pydantic import BaseModel


class Sinker(ABC):

    @abstractmethod
    def sink(self, data: BaseModel) -> None:
        pass
