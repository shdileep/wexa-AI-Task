"""
FalkorDB Database Adapter.
Connects to FalkorDB (RedisGraph successor) over Redis protocol.
Cypher-compliant graph engine.
"""

import time
from typing import Dict, Any, List, Tuple, Optional
from adapters.base_adapter import BaseGraphAdapter

try:
    from falkordb import FalkorDB as FalkorDBClient
    FALKORDB_AVAILABLE = True
except ImportError:
    FALKORDB_AVAILABLE = False

class FalkorDBAdapter(BaseGraphAdapter):
    def __init__(self, host: str = "localhost", port: int = 6379, password: str = "", graph_name: str = "benchmark_graph", advertised_specs: str = "0.5 vCPU, 512 MB RAM"):
        super().__init__(name="FalkorDB", advertised_specs=advertised_specs)
        self.host = host
        self.port = port
        self.password = password
        self.graph_name = graph_name
        self.db = None
        self.graph = None

    def connect(self) -> bool:
        if not FALKORDB_AVAILABLE:
            print(f"[{self.name}] Warning: 'falkordb' module not installed. Install via pip install falkordb.")
            self.is_connected = False
            return False
        try:
            self.db = FalkorDBClient(host=self.host, port=self.port, password=self.password if self.password else None)
            self.graph = self.db.select_graph(self.graph_name)
            # Test ping/query
            res = self.graph.query("RETURN 1 AS test")
            if res and res.result_set:
                self.is_connected = True
                print(f"[{self.name}] Successfully connected to FalkorDB at {self.host}:{self.port}")
                return True
        except Exception as e:
            print(f"[{self.name}] Connection failed: {e}")
            self.is_connected = False
            return False

    def close(self) -> None:
        self.graph = None
        self.db = None
        self.is_connected = False

    def clear_database(self) -> bool:
        if not self.graph:
            return False
        try:
            self.graph.delete()
            self.graph = self.db.select_graph(self.graph_name)
            return True
        except Exception as e:
            # If graph didn't exist, ignore
            return True

    def create_schema_and_indexes(self) -> bool:
        if not self.graph:
            return False
        try:
            self.graph.query("CREATE INDEX FOR (u:User) ON (u.id)")
            self.graph.query("CREATE INDEX FOR (u:User) ON (u.category)")
            return True
        except Exception as e:
            print(f"[{self.name}] Note during index creation: {e}")
            return False

    def ingest_nodes_batch(self, nodes_batch: List[Tuple]) -> int:
        if not self.graph or not nodes_batch:
            return 0
        
        # FalkorDB / RedisGraph Cypher query string batching
        statements = []
        for row in nodes_batch:
            uid, uname, age, cat, created_at = row
            # Escape strings safely
            uname_clean = uname.replace("'", "\\'")
            cat_clean = cat.replace("'", "\\'")
            stmt = f"CREATE (:User {{id: {uid}, username: '{uname_clean}', age: {age}, category: '{cat_clean}', created_at: '{created_at}'}})"
            statements.append(stmt)
        
        full_cypher = " ".join(statements)
        self.graph.query(full_cypher)
        return len(nodes_batch)

    def ingest_edges_batch(self, edges_batch: List[Tuple]) -> int:
        if not self.graph or not edges_batch:
            return 0

        statements = []
        for row in edges_batch:
            src, dst, weight, interactions = row
            stmt = f"MATCH (src:User {{id: {src}}}), (dst:User {{id: {dst}}}) CREATE (src)-[:FOLLOWS {{weight: {weight}, interactions: {interactions}}}]->(dst)"
            statements.append(stmt)

        full_cypher = " ".join(statements)
        self.graph.query(full_cypher)
        return len(edges_batch)

    def run_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Tuple[List[Any], float]:
        if not self.graph:
            return [], 0.0

        t0 = time.perf_counter()
        res = self.graph.query(query, params or {})
        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000.0

        records = []
        if res and res.result_set:
            for row in res.result_set:
                records.append(row)
        return records, latency_ms

    def get_storage_footprint(self) -> Dict[str, Any]:
        if not self.db:
            return {"stored_size_mb": "not observable", "memory_usage_mb": "not observable"}
        try:
            info = self.db.redis.info("memory")
            used_mb = round(info.get("used_memory", 0) / (1024 * 1024), 2)
            return {
                "stored_size_mb": f"{used_mb} MB (Redis in-memory dataset)",
                "memory_usage_mb": f"{used_mb} MB RAM",
                "details": info
            }
        except Exception:
            return {"stored_size_mb": "In-memory", "memory_usage_mb": "< 512 MB Container Cap"}
