from abc import ABC, abstractmethod
from typing import Optional


class Referential(ABC):

    @abstractmethod
    def get_closest_match(self, value: str) -> Optional[dict]:
        pass
