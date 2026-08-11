# Benchmark Results & Reproducibility Guide

This directory contains the machine-readable JSON metrics output (`benchmark_summary.json`) produced by `run_benchmark.py`.

## Data Artifact Provenance
- `results/benchmark_summary.json`: Comprehensive metrics for data ingestion throughput, read traversal latencies (p50, p90, p95, p99, mean, min, max, std), cold-start performance, and concurrency sweeps across 1, 10, and 40 parallel client workers.
- Each platform entry contains a `"data_source"` key explicitly indicating whether metrics were measured against a live instance (`"LIVE_MEASURED"`) or produced in simulated baseline mode (`"MOCK_SIMULATED"`).

## How to Regenerate All Benchmark Results & Visual Charts

### Option A: Complete Live Evaluation
Ensure your environment `.env` file contains valid credentials for CognoDB Cloud and local competitor containers (Neo4j, Memgraph, FalkorDB) running via Docker Compose (`docker-compose up -d`).

```bash
# Execute standard live benchmark (100 iterations per query workload)
python run_benchmark.py

# Or run fast quick test (20 iterations per query workload)
python run_benchmark.py --quick-run
```

### Option B: Standalone Baseline Simulation Mode
To render visual comparison charts and print summary tables without active external database instances:

```bash
python run_benchmark.py --mock-run
```

### Option C: Re-render Charts from JSON Output
To re-generate visual chart PNGs (`charts/*.png`) from existing `results/benchmark_summary.json`:

```bash
python -c "import json; from generate_charts import generate_benchmark_charts; generate_benchmark_charts(json.load(open('results/benchmark_summary.json')))"
```
