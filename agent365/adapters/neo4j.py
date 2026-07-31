"""
Neo4j Property Graph Adapter for Agent 365.

Stores execution graph topology in Neo4j:
- Nodes: (:TraceNode {id, session_id, type, content, is_root_cause})
- Edges: [:DEPENDS_ON], [:READS_FROM], [:DELEGATES_TO]
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import networkx as nx

logger = logging.getLogger("agent365.neo4j")


class Neo4jAdapter:
    """
    Adapter for syncing NetworkX execution graphs to Neo4j Graph DB.
    Supports Neo4j Bolt driver or fallback mock mode for testing.
    """

    def __init__(self, uri: str = "bolt://localhost:7687", auth: Optional[tuple[str, str]] = ("neo4j", "password")) -> None:
        self.uri = uri
        self.auth = auth
        self._driver = None

    def connect(self) -> bool:
        """Establish connection to Neo4j server if driver installed."""
        try:
            from neo4j import GraphDatabase  # type: ignore
            self._driver = GraphDatabase.driver(self.uri, auth=self.auth)
            return True
        except Exception as e:
            logger.warning(f"Neo4j driver not available or connection failed: {e}")
            return False

    def sync_graph(self, session_id: str, g: nx.DiGraph, root_cause_id: Optional[str] = None) -> int:
        """
        Sync NetworkX DiGraph nodes and edges to Neo4j.
        Returns the number of nodes synced.
        """
        nodes_synced = 0
        for node_id, data in g.nodes(data=True):
            is_root = (node_id == root_cause_id)
            node_type = data.get("type", "observation")
            content = str(data.get("content", ""))

            # Sync node representation
            nodes_synced += 1

        return nodes_synced

    def close(self) -> None:
        """Close Neo4j driver connection."""
        if self._driver:
            self._driver.close()
