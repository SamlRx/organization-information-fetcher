from abc import ABC, abstractmethod
from typing import Iterable

from pydantic import BaseModel


class Sinker(ABC):

    @abstractmethod
    def sink(self, data: Iterable[BaseModel]) -> None:
        pass
