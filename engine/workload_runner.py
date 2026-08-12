"""
Workload Harness & Concurrency Sweep Engine.
Runs read workloads (1-hop, 2-hop, 3-hop traversals, point lookups, indexed lookups, aggregations)
with warm-up phase and percentile reporting (p50, p95).
Runs concurrent read/write throughput sweeps (1, 10, 40 parallel clients).
"""

import time
import random
import concurrent.futures
from typing import Dict, Any, List
from adapters.base_adapter import BaseGraphAdapter
from engine.queries import QueryWorkloads
from engine.metrics import MetricsCalculator

class BenchmarkRunner:
    def __init__(self, adapter: BaseGraphAdapter, iterations: int = 100, warmup_iterations: int = 20, num_nodes: int = 25000):
        self.adapter = adapter
        self.iterations = max(100, iterations)
        self.warmup_iterations = warmup_iterations
        self.num_nodes = num_nodes

    def run_read_workloads(self) -> Dict[str, Any]:
        print(f"[{self.adapter.name}] Executing Warm-up & Read Workloads ({self.iterations} iterations)...")
        random.seed(42)

        categories = ["Tech", "Science", "Arts", "Finance", "Gaming", "Education", "Healthcare"]

        # 0. Cold-Start Measurement (First execution latency before warm-up cache)
        cold_id = random.randint(1, self.num_nodes)
        q_cold, params_cold = QueryWorkloads.get_1hop_traversal(cold_id)
        _, cold_start_lat = self.adapter.run_query(q_cold, params_cold)

        # 1. Warm-Up Phase
        print(f"  Warm-up phase ({self.warmup_iterations} iterations)...")
        for _ in range(self.warmup_iterations):
            start_id = random.randint(1, self.num_nodes)
            q_w1, p_w1 = QueryWorkloads.get_1hop_traversal(start_id)
            self.adapter.run_query(q_w1, p_w1)
            q_wp, p_wp = QueryWorkloads.get_point_lookup(start_id)
            self.adapter.run_query(q_wp, p_wp)

        # 2. Benchmark 1-Hop Traversal
        print("  Benchmarking 1-Hop Traversals...")
        l_1hop = []
        for _ in range(self.iterations):
            start_id = random.randint(1, self.num_nodes)
            q, params = QueryWorkloads.get_1hop_traversal(start_id)
            _, lat = self.adapter.run_query(q, params)
            l_1hop.append(lat)

        # 3. Benchmark 2-Hop Traversal
        print("  Benchmarking 2-Hop Traversals...")
        l_2hop = []
        for _ in range(self.iterations):
            start_id = random.randint(1, self.num_nodes)
            q, params = QueryWorkloads.get_2hop_traversal(start_id)
            _, lat = self.adapter.run_query(q, params)
            l_2hop.append(lat)

        # 4. Benchmark 3-Hop Traversal
        print("  Benchmarking 3-Hop Traversals...")
        l_3hop = []
        for _ in range(self.iterations):
            start_id = random.randint(1, self.num_nodes)
            q, params = QueryWorkloads.get_3hop_traversal(start_id)
            _, lat = self.adapter.run_query(q, params)
            l_3hop.append(lat)

        # 5. Benchmark Point Lookup
        print("  Benchmarking Point Lookups...")
        l_lookup = []
        for _ in range(self.iterations):
            user_id = random.randint(1, self.num_nodes)
            q, params = QueryWorkloads.get_point_lookup(user_id)
            _, lat = self.adapter.run_query(q, params)
            l_lookup.append(lat)

        # 6. Benchmark Indexed Filtered Lookup
        print("  Benchmarking Indexed Filtered Lookups...")
        l_indexed = []
        for _ in range(self.iterations):
            cat = random.choice(categories)
            q, params = QueryWorkloads.get_indexed_lookup(cat)
            _, lat = self.adapter.run_query(q, params)
            l_indexed.append(lat)

        # 7. Benchmark Aggregations (Count / Group-By)
        print("  Benchmarking Aggregations (Group-By)...")
        l_agg = []
        for _ in range(self.iterations):
            q, params = QueryWorkloads.get_aggregation_groupby()
            _, lat = self.adapter.run_query(q, params)
            l_agg.append(lat)

        results = {
            "platform": self.adapter.name,
            "cold_start_ms": round(cold_start_lat, 2),
            "1hop_traversal": MetricsCalculator.calculate_latencies(l_1hop),
            "2hop_traversal": MetricsCalculator.calculate_latencies(l_2hop),
            "3hop_traversal": MetricsCalculator.calculate_latencies(l_3hop),
            "point_lookup": MetricsCalculator.calculate_latencies(l_lookup),
            "indexed_lookup": MetricsCalculator.calculate_latencies(l_indexed),
            "aggregations": MetricsCalculator.calculate_latencies(l_agg),
        }
        return results

    def run_concurrency_sweep(self, concurrency_levels: List[int] = [1, 10, 40], duration_sec: int = 5) -> Dict[int, Dict[str, Any]]:
        print(f"[{self.adapter.name}] Running Concurrency Sweeps (Clients: {concurrency_levels})...")
        sweep_results = {}

        for num_clients in concurrency_levels:
            print(f"  Testing with {num_clients} concurrent client(s) for {duration_sec}s...")
            
            total_ops = 0
            latencies = []
            stop_time = time.time() + duration_sec

            def worker_client():
                nonlocal total_ops
                client_ops = 0
                while time.time() < stop_time:
                    # 80% Read / 20% Write workload mix
                    if random.random() < 0.8:
                        start_id = random.randint(1, self.num_nodes)
                        q, params = QueryWorkloads.get_1hop_traversal(start_id)
                    else:
                        src = random.randint(1, self.num_nodes)
                        dst = random.randint(1, self.num_nodes)
                        q, params = QueryWorkloads.get_write_transaction(src, dst, round(random.uniform(0.1, 1.0), 2))
                    
                    _, lat = self.adapter.run_query(q, params)
                    latencies.append(lat)
                    client_ops += 1
                return client_ops

            t0 = time.perf_counter()
            actual_num_clients = num_clients
            futures = []
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=num_clients) as executor:
                    for _ in range(num_clients):
                        try:
                            futures.append(executor.submit(worker_client))
                        except RuntimeError:
                            break
                    for f in concurrent.futures.as_completed(futures):
                        try:
                            total_ops += f.result()
                        except Exception:
                            pass
            except RuntimeError:
                pass
            t1 = time.perf_counter()
            actual_duration = t1 - t0

            qps = MetricsCalculator.calculate_throughput(total_ops, actual_duration)
            stats = MetricsCalculator.calculate_latencies(latencies)
            stats["sustained_qps"] = qps
            sweep_results[num_clients] = stats
            print(f"    Result for {num_clients} clients: {qps:,} ops/sec (p50: {stats['p50']}ms, p95: {stats['p95']}ms)")

        return sweep_results
