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
            parent_dir = os.path.dirname(os.path.abspath(self.db_path))
            os.makedirs(parent_dir, exist_ok=True)
            if os.path.exists(self.db_path) and os.path.isdir(self.db_path) and not os.listdir(self.db_path):
                os.rmdir(self.db_path)
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
        if not self.conn:
            if not self.connect():
                return False
        try:
            self.conn.execute("DROP TABLE FOLLOWS")
        except Exception:
            pass
        try:
            self.conn.execute("DROP TABLE User")
        except Exception:
            pass
        return True

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
        
        batch = [
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
        self.conn.execute(query, {"batch": batch})
        return len(nodes_batch)

    def ingest_edges_batch(self, edges_batch: List[Tuple]) -> int:
        if not self.conn or not edges_batch:
            return 0

        batch = [
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
        self.conn.execute(query, {"batch": batch})
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
