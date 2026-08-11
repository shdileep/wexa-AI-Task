"""
Data Ingestion Engine.
Reads nodes & edges CSV datasets and batch-ingests into target graph database adapter.
Measures wall-clock load time, nodes/sec, relationships/sec.
"""

import csv
import time
from typing import Dict, Any, Tuple
from adapters.base_adapter import BaseGraphAdapter
from engine.metrics import MetricsCalculator

class IngestEngine:
    def __init__(self, adapter: BaseGraphAdapter, batch_size: int = 2000):
        self.adapter = adapter
        self.batch_size = batch_size

    def run_ingest(self, nodes_csv_path: str, edges_csv_path: str) -> Dict[str, Any]:
        print(f"[{self.adapter.name}] Starting data ingestion from CSV datasets...")
        
        # Determine expected counts from source CSV files for dataset parity assertion
        with open(nodes_csv_path, mode="r", encoding="utf-8") as f:
            expected_nodes = max(0, sum(1 for _ in f) - 1)
        with open(edges_csv_path, mode="r", encoding="utf-8") as f:
            expected_edges = max(0, sum(1 for _ in f) - 1)

        # 1. Reset database & create schema
        self.adapter.clear_database()
        self.adapter.create_schema_and_indexes()

        # 2. Read and Ingest Nodes
        nodes_batch = []
        total_nodes = 0
        t0_nodes = time.perf_counter()

        with open(nodes_csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                # row: id, username, age, category, created_at
                nodes_batch.append((int(row[0]), row[1], int(row[2]), row[3], row[4]))
                if len(nodes_batch) >= self.batch_size:
                    total_nodes += self.adapter.ingest_nodes_batch(nodes_batch)
                    nodes_batch = []
            if nodes_batch:
                total_nodes += self.adapter.ingest_nodes_batch(nodes_batch)

        t1_nodes = time.perf_counter()
        nodes_duration = t1_nodes - t0_nodes
        nodes_per_sec = MetricsCalculator.calculate_throughput(total_nodes, nodes_duration)

        # 3. Read and Ingest Edges
        edges_batch = []
        total_edges = 0
        t0_edges = time.perf_counter()

        with open(edges_csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                # row: src_id, dst_id, weight, interaction_count
                edges_batch.append((int(row[0]), int(row[1]), float(row[2]), int(row[3])))
                if len(edges_batch) >= self.batch_size:
                    total_edges += self.adapter.ingest_edges_batch(edges_batch)
                    edges_batch = []
            if edges_batch:
                total_edges += self.adapter.ingest_edges_batch(edges_batch)

        t1_edges = time.perf_counter()
        edges_duration = t1_edges - t0_edges
        edges_per_sec = MetricsCalculator.calculate_throughput(total_edges, edges_duration)

        total_wall_clock_time = nodes_duration + edges_duration

        # Dataset parity assertion
        if total_nodes != expected_nodes:
            raise ValueError(
                f"[{self.adapter.name}] Dataset Parity Failure: Ingested {total_nodes} nodes, expected {expected_nodes} from {nodes_csv_path}"
            )
        if total_edges != expected_edges:
            raise ValueError(
                f"[{self.adapter.name}] Dataset Parity Failure: Ingested {total_edges} edges, expected {expected_edges} from {edges_csv_path}"
            )

        results = {
            "platform": self.adapter.name,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "nodes_ingest_time_sec": round(nodes_duration, 2),
            "edges_ingest_time_sec": round(edges_duration, 2),
            "total_wall_clock_sec": round(total_wall_clock_time, 2),
            "nodes_per_sec": nodes_per_sec,
            "edges_per_sec": edges_per_sec,
            "overall_items_per_sec": MetricsCalculator.calculate_throughput(total_nodes + total_edges, total_wall_clock_time)
        }

        print(f"[{self.adapter.name}] Ingestion complete: {total_nodes:,} nodes & {total_edges:,} edges loaded in {total_wall_clock_time:.2f}s ({results['overall_items_per_sec']:,} items/sec).")
        return results
