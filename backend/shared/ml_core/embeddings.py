from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np


class EmbeddingGenerator:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

    def generate(self, text: Union[str, List[str]]) -> np.ndarray:
        return self.model.encode(text, convert_to_numpy=True)

    def generate_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        return self.model.encode(
            texts, batch_size=batch_size, show_progress_bar=True, convert_to_numpy=True
        )
