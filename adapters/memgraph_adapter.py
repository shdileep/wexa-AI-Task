"""
Memgraph Database Adapter.
Connects to Memgraph via Bolt protocol (port 7688 / 7687).
In-memory C++ graph database engine.
"""

import time
from typing import Dict, Any, List, Tuple, Optional
try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    GraphDatabase = None
    Driver = None
    NEO4J_AVAILABLE = False
from adapters.base_adapter import BaseGraphAdapter

class MemgraphAdapter(BaseGraphAdapter):
    def __init__(self, uri: str = "bolt://localhost:7688", user: str = "", password: str = "", advertised_specs: str = "0.5 vCPU, 512 MB RAM"):
        super().__init__(name="Memgraph", advertised_specs=advertised_specs)
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[Driver] = None

    def connect(self) -> bool:
        if not NEO4J_AVAILABLE:
            print(f"[{self.name}] Warning: 'neo4j' module not installed. Install via pip install neo4j.")
            self.is_connected = False
            return False
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password) if self.password else None,
                max_connection_lifetime=300,
                max_connection_pool_size=50
            )
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                record = result.single()
                if record and record["test"] == 1:
                    self.is_connected = True
                    print(f"[{self.name}] Successfully connected to {self.uri}")
                    return True
        except Exception as e:
            print(f"[{self.name}] Connection failed: {e}")
            self.is_connected = False
            return False

    def close(self) -> None:
        if self.driver:
            self.driver.close()
            self.is_connected = False

    def clear_database(self) -> bool:
        if not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            return True
        except Exception as e:
            print(f"[{self.name}] Error clearing database: {e}")
            return False

    def create_schema_and_indexes(self) -> bool:
        if not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run("CREATE INDEX ON :User(id)")
                session.run("CREATE INDEX ON :User(category)")
            return True
        except Exception as e:
            print(f"[{self.name}] Note during index creation: {e}")
            return False

    def ingest_nodes_batch(self, nodes_batch: List[Tuple]) -> int:
        if not self.driver or not nodes_batch:
            return 0
        
        data = [
            {
                "id": row[0],
                "username": row[1],
                "age": row[2],
                "category": row[3],
                "created_at": row[4]
            }
            for row in nodes_batch
        ]

        query = """
        UNWIND $batch AS row
        CREATE (u:User {
            id: row.id,
            username: row.username,
            age: row.age,
            category: row.category,
            created_at: row.created_at
        })
        """
        with self.driver.session() as session:
            session.run(query, batch=data)
        return len(nodes_batch)

    def ingest_edges_batch(self, edges_batch: List[Tuple]) -> int:
        if not self.driver or not edges_batch:
            return 0

        data = [
            {
                "src_id": row[0],
                "dst_id": row[1],
                "weight": row[2],
                "interactions": row[3]
            }
            for row in edges_batch
        ]

        query = """
        UNWIND $batch AS row
        MATCH (src:User {id: row.src_id})
        MATCH (dst:User {id: row.dst_id})
        CREATE (src)-[:FOLLOWS {weight: row.weight, interactions: row.interactions}]->(dst)
        """
        with self.driver.session() as session:
            session.run(query, batch=data)
        return len(edges_batch)

    def run_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Tuple[List[Any], float]:
        if not self.driver:
            return [], 0.0
        
        params = params or {}
        t0 = time.perf_counter()
        with self.driver.session() as session:
            result = session.run(query, params)
            records = [r.data() for r in result]
        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000.0
        return records, latency_ms

    def get_storage_footprint(self) -> Dict[str, Any]:
        if not self.driver:
            return {"stored_size_mb": "not observable", "memory_usage_mb": "not observable"}
        try:
            with self.driver.session() as session:
                res = session.run("SHOW STORAGE INFO")
                info = [r.data() for r in res]
                return {
                    "stored_size_mb": "In-memory RAM pool",
                    "memory_usage_mb": "RAM usage allocated dynamically (< 512 MB Container Cap)",
                    "details": info
                }
        except Exception:
            return {"stored_size_mb": "In-memory", "memory_usage_mb": "< 512 MB Capped"}
