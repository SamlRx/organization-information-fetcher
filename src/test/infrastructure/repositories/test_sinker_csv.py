import csv

import pytest
from pydantic import BaseModel

from organization_information_fetcher_app.infrastructure.repositories.sinker_csv import (
    SinkerCsv,
)


class MockModel(BaseModel):
    name: str
    id: int


@pytest.fixture
def temp_csv_file(tmp_path) -> str:
    return str(tmp_path / "test_output.csv")


@pytest.fixture
def sinker(temp_csv_file: str) -> SinkerCsv:
    return SinkerCsv(file_path=temp_csv_file, batch_size=2)


def test_sink_organization(temp_csv_file: str, sinker: SinkerCsv) -> None:
    data1 = MockModel(name="CompanyA", id=1)
    data2 = MockModel(name="CompanyB", id=2)
    data3 = MockModel(name="CompanyC", id=3)

    # Sink two records, triggering a flush
    sinker.sink_organization(data1)
    sinker.sink_organization(data2)

    # Ensure the file is created and contains the first batch
    with open(temp_csv_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["name"] == "CompanyA"
        assert rows[1]["name"] == "CompanyB"

    # Sink another record, which should remain in buffer
    sinker.sink_organization(data3)

    with open(temp_csv_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        assert len(rows) == 2  # Still 2, buffer not flushed yet

    # Force flush and check again
    sinker._flush()
    with open(temp_csv_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        assert len(rows) == 3
        assert rows[2]["name"] == "CompanyC"


def test_del_triggers_flush(temp_csv_file: str) -> None:
    sinker = SinkerCsv(file_path=temp_csv_file, batch_size=5)
    data = MockModel(name="CompanyX", id=99)
    sinker.sink_organization(data)

    # Delete object, which should trigger __del__ and flush remaining buffer
    del sinker

    with open(temp_csv_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["name"] == "CompanyX"
