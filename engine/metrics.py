"""
Metrics helper module for calculating latency percentiles, throughput (QPS), and summary tables.
"""

import numpy as np
from typing import List, Dict, Any

class MetricsCalculator:
    @staticmethod
    def calculate_latencies(latency_ms_list: List[float]) -> Dict[str, float]:
        if not latency_ms_list:
            return {
                "count": 0,
                "p50": 0.0,
                "p90": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std": 0.0
            }
        
        arr = np.array(latency_ms_list)
        return {
            "count": int(len(arr)),
            "p50": round(float(np.percentile(arr, 50)), 2),
            "p90": round(float(np.percentile(arr, 90)), 2),
            "p95": round(float(np.percentile(arr, 95)), 2),
            "p99": round(float(np.percentile(arr, 99)), 2),
            "mean": round(float(np.mean(arr)), 2),
            "min": round(float(np.min(arr)), 2),
            "max": round(float(np.max(arr)), 2),
            "std": round(float(np.std(arr)), 2)
        }

    @staticmethod
    def calculate_throughput(total_operations: int, duration_sec: float) -> float:
        if duration_sec <= 0:
            return 0.0
        return round(total_operations / duration_sec, 2)
