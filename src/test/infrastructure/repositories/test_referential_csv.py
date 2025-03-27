import os
from typing import Callable
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from infrastructure.repositories.referential_csv import (
    CsvReferential,
    CsvReferentialBuilder,
)


@pytest.fixture
def mock_embedding_model() -> MagicMock:
    model: MagicMock = MagicMock()
    model.encode.side_effect = lambda x, convert_to_numpy: np.array([1.0, 2.0, 3.0])
    return model


@pytest.fixture
def mock_similarity_fn() -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
    return lambda x, y: np.array([[0.9, 0.8, 0.7]])


@pytest.fixture
def sample_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "key": ["Title1", "Title2", "Title3"],
            "value": ["Value1", "Value2", "Value3"],
            "embedding": [
                np.array([1, 0, 0]),
                np.array([0, 1, 0]),
                np.array([0, 0, 1]),
            ],
        }
    )


def test_get_closest_match(
    mock_embedding_model: MagicMock,
    mock_similarity_fn: Callable[[np.ndarray, np.ndarray], np.ndarray],
    sample_data: pd.DataFrame,
) -> None:
    csv_referential = CsvReferential(
        sample_data, mock_embedding_model, mock_similarity_fn
    )
    result = csv_referential.get_closest_match("test query")
    assert isinstance(result, dict)
    assert result["key"] == "Title1"


@pytest.fixture
def mock_cache_path() -> str:
    return ".tmp/test_cache.npz"


@patch("os.path.exists", return_value=True)
@patch("numpy.load")
def test_load_cached_data(mock_np_load: MagicMock, mock_cache_path: str) -> None:
    mock_np_load.return_value = {
        "data": np.array(["Title1", "Title2", "Title3"]),
        "embeddings": np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
    }
    result = CsvReferentialBuilder._load_cached_data(mock_cache_path)
    assert isinstance(result, pd.DataFrame)
    assert isinstance(result["embedding"].iloc[0], np.ndarray)


@patch("pandas.read_csv")
def test_generate_embeddings(
    mock_read_csv: MagicMock, mock_embedding_model: MagicMock
) -> None:
    mock_read_csv.return_value = pd.DataFrame(
        {"key": ["Test1", "Test2"], "value": ["Value1", "Value2"]}
    )
    result = CsvReferentialBuilder._generate_embeddings(
        mock_read_csv.return_value, mock_embedding_model
    )
    assert "embedding" in result.columns
    assert isinstance(result["embedding"].iloc[0], np.ndarray)


@patch("numpy.savez")
def test_save_cache(
    mock_npy_save: MagicMock, sample_data: pd.DataFrame, mock_cache_path: str
) -> None:
    CsvReferentialBuilder._save_cache(sample_data, mock_cache_path)
    mock_npy_save.assert_called_once()


@patch("pandas.read_csv")
def test_load_data_without_cache(
    mock_read_csv: MagicMock,
    mock_embedding_model: MagicMock,
    sample_data: pd.DataFrame,
    mock_cache_path: str,
) -> None:
    os.makedirs(os.path.dirname(mock_cache_path), exist_ok=True)

    mock_read_csv.return_value = sample_data.drop(columns=["embedding"])
    result = CsvReferentialBuilder._load_data(
        "dummy.csv", mock_cache_path, mock_embedding_model
    )
    assert "embedding" in result.columns
    assert isinstance(result["embedding"].iloc[0], np.ndarray)


@patch("infrastructure.repositories.referential_csv.CsvReferentialBuilder._load_data")
def test_build(mock_load_data: MagicMock) -> None:
    mock_load_data.return_value = pd.DataFrame(
        {"key": ["Title1"], "embedding": [np.array([1, 0, 0])]}
    )
    result = CsvReferentialBuilder.build("dummy.csv")
    assert isinstance(result, CsvReferential)
