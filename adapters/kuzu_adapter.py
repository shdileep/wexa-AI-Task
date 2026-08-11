"""
Kùzu Database Adapter.
Embedded high-performance column-oriented graph database engine.
C++ graph query kernel running in process or embedded instance.
"""

import os
import shutil
import time
from typing import Dict, Any, List, Tuple, Optional
from adapters.base_adapter import BaseGraphAdapter

try:
    import kuzu
    KUZU_AVAILABLE = True
except ImportError:
    KUZU_AVAILABLE = False

class KuzuAdapter(BaseGraphAdapter):
    def __init__(self, db_path: str = "./kuzu_db_data", advertised_specs: str = "0.5 vCPU, 512 MB RAM"):
        super().__init__(name="Kùzu DB", advertised_specs=advertised_specs)
        self.db_path = db_path
        self.db = None
        self.conn = None

    def connect(self) -> bool:
        if not KUZU_AVAILABLE:
            print(f"[{self.name}] Warning: 'kuzu' module not installed. Install via pip install kuzu.")
            self.is_connected = False
            return False
        try:
            os.makedirs(self.db_path, exist_ok=True)
            # Kùzu database initialization
            self.db = kuzu.Database(self.db_path, buffer_pool_size=256 * 1024 * 1024) # 256MB buffer pool
            self.conn = kuzu.Connection(self.db)
            self.is_connected = True
            print(f"[{self.name}] Successfully initialized Kùzu DB at {self.db_path}")
            return True
        except Exception as e:
            print(f"[{self.name}] Connection failed: {e}")
            self.is_connected = False
            return False

    def close(self) -> None:
        self.conn = None
        self.db = None
        self.is_connected = False

    def clear_database(self) -> bool:
        self.close()
        try:
            if os.path.exists(self.db_path):
                shutil.rmtree(self.db_path)
            return self.connect()
        except Exception as e:
            print(f"[{self.name}] Error clearing database directory: {e}")
            return False

    def create_schema_and_indexes(self) -> bool:
        if not self.conn:
            return False
        try:
            # Create Node Table
            self.conn.execute("CREATE NODE TABLE User(id INT64, username STRING, age INT64, category STRING, created_at STRING, PRIMARY KEY (id))")
            # Create Rel Table
            self.conn.execute("CREATE REL TABLE FOLLOWS(FROM User TO User, weight DOUBLE, interactions INT64)")
            return True
        except Exception as e:
            print(f"[{self.name}] Note during Kuzu schema creation: {e}")
            return False

    def ingest_nodes_batch(self, nodes_batch: List[Tuple]) -> int:
        if not self.conn or not nodes_batch:
            return 0
        
        # Batch insert into Kuzu via query
        for row in nodes_batch:
            uid, uname, age, cat, created_at = row
            uname_clean = uname.replace("'", "\\'")
            cat_clean = cat.replace("'", "\\'")
            query = f"CREATE (:User {{id: {uid}, username: '{uname_clean}', age: {age}, category: '{cat_clean}', created_at: '{created_at}'}})"
            self.conn.execute(query)
        return len(nodes_batch)

    def ingest_edges_batch(self, edges_batch: List[Tuple]) -> int:
        if not self.conn or not edges_batch:
            return 0

        for row in edges_batch:
            src, dst, weight, interactions = row
            query = f"MATCH (src:User {{id: {src}}}), (dst:User {{id: {dst}}}) CREATE (src)-[:FOLLOWS {{weight: {weight}, interactions: {interactions}}}]->(dst)"
            self.conn.execute(query)
        return len(edges_batch)

    def run_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Tuple[List[Any], float]:
        if not self.conn:
            return [], 0.0

        t0 = time.perf_counter()
        res = self.conn.execute(query, params or {})
        records = []
        while res.has_next():
            records.append(res.get_next())
        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000.0
        return records, latency_ms

    def get_storage_footprint(self) -> Dict[str, Any]:
        if not os.path.exists(self.db_path):
            return {"stored_size_mb": "0 MB", "memory_usage_mb": "256 MB Buffer Pool"}
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(self.db_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            size_mb = round(total_size / (1024 * 1024), 2)
            return {
                "stored_size_mb": f"{size_mb} MB",
                "memory_usage_mb": "256 MB Buffer Pool Allocation",
                "path": self.db_path
            }
        except Exception:
            return {"stored_size_mb": "not observable", "memory_usage_mb": "256 MB"}
