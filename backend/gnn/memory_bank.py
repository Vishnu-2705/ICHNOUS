"""
Graph Memory Bank module for TraceMind.
Stores historical graph vectors and performs fast K-NN vector similarity search over trace motifs.
"""

import math
from typing import Dict, List, Tuple


class GraphMemoryBank:
    """
    In-memory vector store indexing global graph embeddings z_G for nearest-neighbor motif matching.
    """

    def __init__(self) -> None:
        # Pre-seed memory bank with canonical failure graph embeddings
        self._index: Dict[str, List[float]] = {}
        self._seed_default_motifs()

    def _seed_default_motifs(self) -> None:
        """Seed memory bank with initial canonical trace vectors."""
        # Seeding vectors matching 64d graph embeddings
        self._index["retrieval_failure_motif_v1"] = [0.85 if i % 4 == 0 else 0.15 for i in range(64)]
        self._index["tool_failure_motif_v1"] = [0.92 if i % 3 == 0 else 0.10 for i in range(64)]
        self._index["coordination_loop_motif_v1"] = [0.88 if i % 2 == 0 else 0.12 for i in range(64)]
        self._index["golden_normal_run_v1"] = [0.05 for _ in range(64)]

    def add_graph_vector(self, trace_id: str, embedding: List[float]) -> None:
        """Add or update a graph embedding vector in the memory bank."""
        self._index[trace_id] = embedding

    def search_similar_motifs(self, query_vector: List[float], top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Cosine similarity search over graph memory bank.
        Returns Top-K (trace_id, similarity_score).
        """
        if not self._index or not query_vector:
            return []

        q_norm = math.sqrt(sum(x * x for x in query_vector)) or 1.0
        results: List[Tuple[str, float]] = []

        for tid, vec in self._index.items():
            dim = min(len(query_vector), len(vec))
            dot = sum(query_vector[i] * vec[i] for i in range(dim))
            v_norm = math.sqrt(sum(x * x for x in vec[:dim])) or 1.0
            similarity = round(max(0.0, min(1.0, dot / (q_norm * v_norm))), 4)
            results.append((tid, similarity))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


# Global singleton instance
_GLOBAL_MEMORY_BANK = GraphMemoryBank()


def get_memory_bank() -> GraphMemoryBank:
    return _GLOBAL_MEMORY_BANK
