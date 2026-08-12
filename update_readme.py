import json
import re

def format_tables():
    with open("results/benchmark_summary.json", mode="r", encoding="utf-8") as f:
        data = json.load(f)

    with open("README.md", mode="r", encoding="utf-8") as f:
        content = f.read()

    platforms = ["CognoDB Cloud", "Neo4j", "Memgraph", "FalkorDB", "Kùzu DB"]

    # 4.1 Ingestion Table
    ingest_rows = [
        "| Platform | Data Source | Specs / Tier | Total Nodes | Total Relationships | Nodes Ingested / sec | Relationships Ingested / sec | Total Wall-Clock Load Time |",
        "|---|---|---|---|---|---|---|---|"
    ]
    for p in platforms:
        if p in data:
            res = data[p]
            ing = res["ingest"]
            ds = res.get("data_source", "UNKNOWN")
            nodes = f"{ing['total_nodes']:,}"
            edges = f"{ing['total_edges']:,}"
            n_sec = f"{ing['nodes_per_sec']:,.0f} / s"
            e_sec = f"{ing['edges_per_sec']:,.0f} / s"
            wall = f"{ing['total_wall_clock_sec']:.1f} s"
            ingest_rows.append(f"| **{p}** | `{ds}` | {res['specs']} | {nodes} | {edges} | {n_sec} | {e_sec} | {wall} |")

    # 4.2 Read Latencies Table
    read_rows = [
        "| Platform | Data Source | 1-Hop Traversal (ms) | 2-Hop Traversal (ms) | 3-Hop Traversal (ms) | Point Lookup (ms) | Indexed Lookup (ms) | Group-By Aggregation (ms) |",
        "|---|---|---|---|---|---|---|---|"
    ]
    for p in platforms:
        if p in data:
            res = data[p]
            r = res["read"]
            ds = res.get("data_source", "UNKNOWN")
            h1 = f"{r['1hop_traversal']['p50']} / {r['1hop_traversal']['p95']}"
            h2 = f"{r['2hop_traversal']['p50']} / {r['2hop_traversal']['p95']}"
            h3 = f"{r['3hop_traversal']['p50']} / {r['3hop_traversal']['p95']}"
            pl = f"{r['point_lookup']['p50']} / {r['point_lookup']['p95']}"
            idx = f"{r['indexed_lookup']['p50']} / {r['indexed_lookup']['p95']}"
            agg = f"{r['aggregations']['p50']} / {r['aggregations']['p95']}"
            read_rows.append(f"| **{p}** | `{ds}` | {h1} | {h2} | {h3} | {pl} | {idx} | {agg} |")

    # 4.3 Cold-Start Table
    cold_rows = [
        "| Platform | Data Source | Cold-Start Latency (First Run) | Warm-State 1-Hop p50 | Warm-State 1-Hop p95 |",
        "|---|---|---|---|---|"
    ]
    for p in platforms:
        if p in data:
            res = data[p]
            r = res["read"]
            ds = res.get("data_source", "UNKNOWN")
            cold = f"{r.get('cold_start_ms', 'N/A')} ms"
            p50 = f"{r['1hop_traversal']['p50']} ms"
            p95 = f"{r['1hop_traversal']['p95']} ms"
            cold_rows.append(f"| **{p}** | `{ds}` | {cold} | {p50} | {p95} |")

    # 4.4 Concurrency Table
    conc_rows = [
        "| Platform | Data Source | 1 Client Worker (QPS) | 10 Client Workers (QPS) | 40 Client Workers (QPS) |",
        "|---|---|---|---|---|"
    ]
    for p in platforms:
        if p in data:
            res = data[p]
            c = res["concurrency"]
            ds = res.get("data_source", "UNKNOWN")
            c1 = c.get(1) or c.get("1", {})
            c10 = c.get(10) or c.get("10", {})
            c40 = c.get(40) or c.get("40", {})
            q1 = f"{c1.get('sustained_qps', 0):,.0f} QPS (p95: {c1.get('p95', 0)}ms)"
            q10 = f"{c10.get('sustained_qps', 0):,.0f} QPS (p95: {c10.get('p95', 0)}ms)"
            q40 = f"{c40.get('sustained_qps', 0):,.0f} QPS (p95: {c40.get('p95', 0)}ms)"
            conc_rows.append(f"| **{p}** | `{ds}` | {q1} | {q10} | {q40} |")

    # 4.5 Footprint Table
    foot_rows = [
        "| Platform | Data Source | Stored Data Disk Size | Memory Allocation Footprint |",
        "|---|---|---|---|"
    ]
    for p in platforms:
        if p in data:
            res = data[p]
            fp = res["footprint"]
            ds = res.get("data_source", "UNKNOWN")
            size = fp.get("stored_size_mb", "N/A")
            mem = fp.get("memory_usage_mb", "N/A")
            foot_rows.append(f"| **{p}** | `{ds}` | {size} | {mem} |")

    # Replace in README content using regex sections
    def replace_section(src, section_title, new_table_rows):
        table_str = "\n".join(new_table_rows)
        pattern = re.compile(rf"({re.escape(section_title)}.*?\n\n)(\|.*?\n)+", re.DOTALL)
        return pattern.sub(rf"\1{table_str}\n\n", src)

    content = replace_section(content, "### 4.1 Data Loading & Ingestion Throughput", ingest_rows)
    content = replace_section(content, "### 4.2 Read Query Workload Latencies (p50 / p95 in milliseconds)", read_rows)
    content = replace_section(content, "### 4.3 Cold-Start vs. Warm-State Latency Separation", cold_rows)
    content = replace_section(content, "### 4.4 Concurrency Sweeps (Sustained Queries/sec at 1, 10, 40 Workers)", conc_rows)
    content = replace_section(content, "### 4.5 Resource & Memory Footprint", foot_rows)

    with open("README.md", mode="w", encoding="utf-8") as f:
        f.write(content)

    print("README.md tables successfully updated from benchmark_summary.json!")

if __name__ == "__main__":
    format_tables()
