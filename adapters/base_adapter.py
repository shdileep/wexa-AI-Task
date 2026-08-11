"""
Abstract Base Adapter for Graph Database Cloud Benchmarking.
Defines standard interface for connection, ingestion, query execution, and footprint inspection.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
import time

class BaseGraphAdapter(ABC):
    def __init__(self, name: str, advertised_specs: str):
        self.name = name
        self.advertised_specs = advertised_specs
        self.is_connected = False

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the target graph database platform."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Gracefully close database connection and driver handles."""
        pass

    @abstractmethod
    def clear_database(self) -> bool:
        """Drop all nodes, relationships, and indexes to ensure clean state."""
        pass

    @abstractmethod
    def create_schema_and_indexes(self) -> bool:
        """Create primary key constraints and indexes on User(id) and User(category)."""
        pass

    @abstractmethod
    def ingest_nodes_batch(self, nodes_batch: List[Tuple]) -> int:
        """
        Ingest a batch of nodes.
        Tuple format: (id, username, age, category, created_at)
        """
        pass

    @abstractmethod
    def ingest_edges_batch(self, edges_batch: List[Tuple]) -> int:
        """
        Ingest a batch of relationships.
        Tuple format: (src_id, dst_id, weight, interaction_count)
        """
        pass

    @abstractmethod
    def run_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Tuple[List[Any], float]:
        """
        Executes a single query and returns (results_list, latency_ms).
        """
        pass

    @abstractmethod
    def get_storage_footprint(self) -> Dict[str, Any]:
        """
        Retrieve database storage size, memory footprint, or instance specs where observable.
        Returns dictionary with keys like 'stored_size_mb', 'memory_usage_mb', 'notes'.
        """
        pass
