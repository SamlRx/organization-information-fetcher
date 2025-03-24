import csv
from typing import List

from ports.sinker import Sinker
from pydantic import BaseModel


class SinkerCsv(Sinker):
    def __init__(self, file_path: str, batch_size: int = 10) -> None:
        self._file_path = file_path
        self._batch_size = batch_size
        self._buffer: List[BaseModel] = []

    def sink(self, data: BaseModel) -> None:
        self._buffer.append(data)

        if len(self._buffer) >= self._batch_size:
            self._flush()

    def _flush(self) -> None:
        if not self._buffer:
            return

        with open(self._file_path, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file, fieldnames=self._get_keys(self._buffer[0].model_dump())
            )

            if file.tell() == 0:
                writer.writeheader()

            writer.writerows([record.model_dump() for record in self._buffer])

        self._buffer.clear()

    def flush(self) -> None:
        self._flush()

    @staticmethod
    def _get_keys(param: dict) -> List[str]:
        return list(param.keys())
