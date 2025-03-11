from typing import Callable
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from repository.referential_csv import CsvReferential, CsvReferentialBuilder


@pytest.fixture
def mock_embedding_model() -> MagicMock:
    model = MagicMock()
    model.encode.side_effect = lambda x, convert_to_numpy: np.array([1.0, 2.0, 3.0])
    return model


@pytest.fixture
def mock_similarity_fn() -> Callable:
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
    mock_similarity_fn: Callable,
    sample_data: pd.DataFrame,
):
    # Given
    csv_referential = CsvReferential(
        sample_data, mock_embedding_model, mock_similarity_fn
    )

    # When
    result = csv_referential.get_closest_match("test query")

    # Then
    assert result["key"] == "Title1"


@pytest.fixture
def mock_cache_path():
    return ".tmp/test_cache.npz"


@patch("os.path.exists", return_value=True)
@patch("numpy.load")
def test_load_cached_data(mock_np_load, mock_os_exists, mock_cache_path):
    # Given: A cached file exists
    mock_np_load.return_value = {
        "data": np.array([["Title1"], ["Title2"], ["Title3"]]),
        "embeddings": np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
    }

    # When: Calling _load_cached_data
    result = CsvReferentialBuilder._load_cached_data(mock_cache_path)

    # Then: The returned dataframe should match expected values
    assert isinstance(result["embedding"].iloc[0], np.ndarray)


@patch("pandas.read_csv")
def test_generate_embeddings(mock_read_csv, mock_embedding_model):
    # Given: A dataframe with key
    mock_read_csv.return_value = pd.DataFrame({"key": ["Test1", "Test2"]})

    # When: Generating embeddings
    result = CsvReferentialBuilder._generate_embeddings(
        mock_read_csv.return_value, mock_embedding_model
    )

    # Then: The dataframe should contain generated embeddings
    assert "embedding" in result.columns
    assert isinstance(result["embedding"].iloc[0], np.ndarray)


@patch("numpy.savez")
def test_save_cache(mock_npy_save, sample_data, mock_cache_path):
    # Given: A dataframe with embeddings
    mock_npy_save.savez = MagicMock()

    # When: Saving cache
    CsvReferentialBuilder._save_cache(sample_data, mock_cache_path)

    # Then: np.savez should be called once
    mock_npy_save.assert_called_once()


@patch("os.path.exists", return_value=False)
@patch("pandas.read_csv")
def test_load_data_without_cache(
    mock_read_csv, mock_os_exists, mock_embedding_model, sample_data, mock_cache_path
):
    # Given: No cache exists, and a CSV file is read
    mock_read_csv.return_value = sample_data.drop(columns=["embedding"])

    # When: Loading data
    result = CsvReferentialBuilder._load_data(
        "dummy.csv", mock_cache_path, mock_embedding_model
    )

    # Then: Dataframe should have embeddings
    assert "embedding" in result.columns
    assert isinstance(result["embedding"].iloc[0], np.ndarray)


@patch("repository.referential_csv.CsvReferentialBuilder._load_data")
def test_build(mock_load_data, mock_cache_path):
    # Given: _load_data returns a sample dataframe
    mock_load_data.return_value = pd.DataFrame(
        {"key": ["Title1"], "embedding": [np.array([1, 0, 0])]}
    )

    # When: Calling build
    result = CsvReferentialBuilder.build("dummy.csv")

    # Then: Result should be an instance of CsvReferential
    assert isinstance(result, CsvReferential)
