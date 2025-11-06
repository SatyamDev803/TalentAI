import faiss
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional


class FAISSIndex:
    def __init__(self, dimension: int, index_path: Optional[str] = None):
        self.dimension = dimension
        self.index_path = index_path
        self.index = faiss.IndexFlatL2(dimension)
        self.id_map = {}

        if index_path and Path(index_path).exists():
            self.load()

    def add(self, embeddings: np.ndarray, ids: List[str]):
        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Expected dimension {self.dimension}, got {embeddings.shape[1]}"
            )

        start_idx = self.index.ntotal
        self.index.add(embeddings.astype("float32"))

        for i, entity_id in enumerate(ids):
            self.id_map[start_idx + i] = entity_id

    def search(
        self, query_embedding: np.ndarray, k: int = 10
    ) -> List[Tuple[str, float]]:
        distances, indices = self.index.search(
            query_embedding.astype("float32").reshape(1, -1), k
        )

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx in self.id_map:
                results.append((self.id_map[idx], float(dist)))

        return results

    def save(self):
        if self.index_path:
            faiss.write_index(self.index, self.index_path)

    def load(self):
        if self.index_path:
            self.index = faiss.read_index(self.index_path)
