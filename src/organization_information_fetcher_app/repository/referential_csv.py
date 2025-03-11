import logging
import os
from typing import Callable

import numpy as np
import pandas as pd
from ports.referential import Referential
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

_LOGGER = logging.getLogger(__name__)


class CsvReferential(Referential):

    def __init__(
        self,
        data: pd.DataFrame,
        embedding_model: SentenceTransformer,
        similarity_fn: Callable = cosine_similarity,
    ) -> None:
        _LOGGER.debug("Creating CsvReferential ...")
        self._data = data
        self._embedding_model = embedding_model
        self._similarity_fn = similarity_fn

    def get_closest_match(self, value: str) -> dict:
        query_embedding = self._embedding_model.encode(value, convert_to_numpy=True)

        similarities = self._similarity_fn(
            [query_embedding], np.stack(self._data["embedding"].values)
        )

        return self._data.iloc[np.argmax(similarities)].to_dict()


class CsvReferentialBuilder:

    @classmethod
    def _load_cached_data(cls, cache_path: str) -> pd.DataFrame:
        """Load data from cache if it exists."""
        _LOGGER.info("Loading cached embeddings...")
        data = np.load(cache_path, allow_pickle=True)
        dataframe = pd.DataFrame(data["data"]).astype(str)
        dataframe["embedding"] = list(data["embeddings"])
        return dataframe

    @classmethod
    def _generate_embeddings(
        cls, dataframe: pd.DataFrame, sentence_transformer: SentenceTransformer
    ) -> pd.DataFrame:
        _LOGGER.info("Generating embeddings from CSV...")

        dataframe["embedding"] = dataframe["value"].apply(
            lambda x: sentence_transformer.encode(x, convert_to_numpy=True)
        )
        return dataframe

    @classmethod
    def _save_cache(cls, dataframe: pd.DataFrame, cache_path: str) -> None:
        """Save processed data and embeddings to cache."""
        np.savez(
            cache_path,
            data=dataframe.drop(columns=["embedding"]).to_numpy(),
            embeddings=np.stack(dataframe["embedding"].values),
        )

    @classmethod
    def _load_data(
        cls, csv_path: str, cache_path: str, sentence_transformer: SentenceTransformer
    ) -> pd.DataFrame:
        if os.path.exists(cache_path):
            return cls._load_cached_data(cache_path)
        df = pd.read_csv(csv_path, names=["key", "value"], header=0)
        df["value"] = df["value"].astype(str)
        df["key"] = df["key"].astype(str)
        df = cls._generate_embeddings(df, sentence_transformer)
        cls._save_cache(df, cache_path)
        return df

    @classmethod
    def build(
        cls, file_path: str, sentence_transformer_model: str = "all-MiniLM-L6-v2"
    ) -> CsvReferential:
        cache_path = cls._get_cache_path(file_path)
        sentence_transformer = SentenceTransformer(sentence_transformer_model)
        return CsvReferential(
            cls._load_data(file_path, cache_path, sentence_transformer),
            sentence_transformer,
        )

    @classmethod
    def _get_cache_path(cls, file_path: str) -> str:
        return f"{file_path}.npz"
