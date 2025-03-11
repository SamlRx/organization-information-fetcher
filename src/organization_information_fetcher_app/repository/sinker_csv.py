import csv
from typing import Iterable, List

from ports.sinker import Sinker
from pydantic import BaseModel
from streamable import Stream


class SinkerCsv(Sinker):
    def __init__(self, file_path):
        self.file_path = file_path

    def sink(self, data: Iterable[BaseModel]) -> None:
        with open(self.file_path, mode="w") as file:
            writer = csv.DictWriter(
                file, fieldnames=self._get_keys(Stream(data).first())
            )
            writer.writeheader()
            writer.writerows(Stream(data).map(lambda x: x.dict()))

    def _get_keys(self, param: dict) -> List[str]:
        pass
