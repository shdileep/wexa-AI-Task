"""
Configuration module for Graph Database Cloud Benchmarking Suite.
Handles environment variable loading, CLI default values, and target platform connection parameters.
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

@dataclass
class PlatformConfig:
    name: str
    driver_type: str  # 'bolt', 'falkordb', 'kuzu', etc.
    uri: str
    user: str = ""
    password: str = ""
    host: str = "localhost"
    port: int = 6379
    db_path: str = "./kuzu_db"
    advertised_specs: str = "0.5 vCPU, 256MB-512MB RAM"

@dataclass
class BenchmarkConfig:
    dataset_nodes: int = 25000
    dataset_edges: int = 150000
    batch_size: int = 2000
    warmup_iterations: int = 20
    read_iterations: int = 100
    concurrency_levels: List[int] = field(default_factory=lambda: [1, 10, 40])
    concurrency_duration_sec: int = 10
    output_dir: str = "./results"
    charts_dir: str = "./charts"

    # Platform configurations
    cognodb: PlatformConfig = field(default_factory=lambda: PlatformConfig(
        name="CognoDB Cloud",
        driver_type="bolt_cognodb",
        uri=os.getenv("COGNODB_URI", "bolt+s://demo.databases.cognodb.cloud"),
        user=os.getenv("COGNODB_USER", "cognodb"),
        password=os.getenv("COGNODB_PASSWORD", "secret"),
        advertised_specs="Burstable 0.5 vCPU, 256 MB RAM, 1 GB Disk"
    ))

    neo4j: PlatformConfig = field(default_factory=lambda: PlatformConfig(
        name="Neo4j (Aura/Container)",
        driver_type="bolt_neo4j",
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password123"),
        advertised_specs="0.5 vCPU, 512 MB RAM (Container Capped)"
    ))

    memgraph: PlatformConfig = field(default_factory=lambda: PlatformConfig(
        name="Memgraph",
        driver_type="bolt_memgraph",
        uri=os.getenv("MEMGRAPH_URI", "bolt://localhost:7688"),
        user=os.getenv("MEMGRAPH_USER", ""),
        password=os.getenv("MEMGRAPH_PASSWORD", ""),
        advertised_specs="0.5 vCPU, 512 MB RAM (In-Memory C++ Engine)"
    ))

    falkordb: PlatformConfig = field(default_factory=lambda: PlatformConfig(
        name="FalkorDB",
        driver_type="falkordb",
        uri="",
        host=os.getenv("FALKORDB_HOST", "localhost"),
        port=int(os.getenv("FALKORDB_PORT", "6379")),
        password=os.getenv("FALKORDB_PASSWORD", ""),
        advertised_specs="0.5 vCPU, 512 MB RAM (Redis Graph Module)"
    ))

    kuzu: PlatformConfig = field(default_factory=lambda: PlatformConfig(
        name="Kùzu DB",
        driver_type="kuzu",
        uri="",
        db_path=os.getenv("KUZU_DB_PATH", "./kuzu_db_data"),
        advertised_specs="0.5 vCPU, 512 MB RAM (Embedded Columnar Engine)"
    ))

def get_config() -> BenchmarkConfig:
    return BenchmarkConfig()
