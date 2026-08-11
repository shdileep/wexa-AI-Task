"""
Dataset generator & loader for Graph Database Benchmarking.
Loads & samples the SNAP soc-Pokec social network dataset (soc-pokec-relationships.txt)
or generates synthetic power-law graph dataset with >100,000 relationships.
"""

import os
import sys
import csv
import random
import time
from typing import Tuple, List, Dict

RANDOM_SEED = 42

def load_pokec_dataset(
    pokec_path: str,
    target_edges: int = 150000,
    output_dir: str = "./dataset/data"
) -> Tuple[str, str, Dict[str, int]]:
    """
    Parses and samples the SNAP soc-Pokec relationships text file.
    Creates nodes.csv and edges.csv with node attributes and relationship weights.
    """
    os.makedirs(output_dir, exist_ok=True)
    random.seed(RANDOM_SEED)

    nodes_file = os.path.join(output_dir, "nodes.csv")
    edges_file = os.path.join(output_dir, "edges.csv")

    categories = ["Tech", "Science", "Arts", "Finance", "Gaming", "Education", "Healthcare"]
    usernames_prefix = ["alex", "jordan", "taylor", "morgan", "sam", "riley", "casey", "quinn", "skyler", "avery"]

    print(f"[Pokec Dataset Loader] Reading relationships from {pokec_path} (Target: {target_edges:,} edges)...")
    t0 = time.time()

    edges_list = []
    unique_nodes = set()

    with open(pokec_path, mode="r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                src, dst = int(parts[0]), int(parts[1])
                edges_list.append((src, dst))
                unique_nodes.add(src)
                unique_nodes.add(dst)
                if len(edges_list) >= target_edges:
                    break

    print(f"  Extracted {len(edges_list):,} edges across {len(unique_nodes):,} unique Pokec nodes.")

    # 1. Write Nodes CSV
    with open(nodes_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "username", "age", "category", "created_at"])
        for node_id in sorted(unique_nodes):
            uname = f"{random.choice(usernames_prefix)}_{node_id}"
            age = (node_id % 50) + 18
            cat = categories[node_id % len(categories)]
            created_at = f"2024-{(node_id % 12) + 1:02d}-{(node_id % 28) + 1:02d}"
            writer.writerow([node_id, uname, age, cat, created_at])

    # 2. Write Edges CSV
    with open(edges_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["src_id", "dst_id", "weight", "interaction_count"])
        for idx, (src, dst) in enumerate(edges_list):
            weight = round((idx % 100) / 100.0 + 0.01, 2)
            interactions = (idx % 50) + 1
            writer.writerow([src, dst, weight, interactions])

    duration = time.time() - t0
    stats = {
        "node_count": len(unique_nodes),
        "relationship_count": len(edges_list),
        "nodes_file_bytes": os.path.getsize(nodes_file),
        "edges_file_bytes": os.path.getsize(edges_file),
        "dataset_source": "SNAP soc-Pokec Social Network",
        "load_time_sec": round(duration, 2)
    }

    print(f"[Pokec Dataset Loader] Complete! Processed {stats['node_count']:,} nodes & {stats['relationship_count']:,} edges in {duration:.2f}s.")
    return nodes_file, edges_file, stats


def generate_graph_dataset(
    num_nodes: int = 25000,
    num_edges: int = 150000,
    output_dir: str = "./dataset/data"
) -> Tuple[str, str, Dict[str, int]]:
    # Check if official SNAP Pokec dataset exists in project root or dataset directory
    pokec_paths = [
        "soc-pokec-relationships.txt",
        "./soc-pokec-relationships.txt",
        "../soc-pokec-relationships.txt"
    ]
    for p in pokec_paths:
        if os.path.exists(p):
            return load_pokec_dataset(p, target_edges=num_edges, output_dir=output_dir)

    # Fallback to synthetic generator if file not found
    os.makedirs(output_dir, exist_ok=True)
    random.seed(RANDOM_SEED)

    nodes_file = os.path.join(output_dir, "nodes.csv")
    edges_file = os.path.join(output_dir, "edges.csv")

    categories = ["Tech", "Science", "Arts", "Finance", "Gaming", "Education", "Healthcare"]
    usernames_prefix = ["alex", "jordan", "taylor", "morgan", "sam", "riley", "casey", "quinn", "skyler", "avery"]

    print(f"[Dataset Generator] Generating {num_nodes:,} nodes and {num_edges:,} relationships...")
    start_time = time.time()

    with open(nodes_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "username", "age", "category", "created_at"])
        for node_id in range(1, num_nodes + 1):
            uname = f"{random.choice(usernames_prefix)}_{node_id}"
            age = random.randint(18, 75)
            cat = random.choice(categories)
            created_at = f"2024-{(node_id % 12) + 1:02d}-{(node_id % 28) + 1:02d}"
            writer.writerow([node_id, uname, age, cat, created_at])

    edges = set()
    edge_count = 0
    with open(edges_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["src_id", "dst_id", "weight", "interaction_count"])
        hubs = list(range(1, max(2, int(num_nodes * 0.05))))

        while edge_count < num_edges:
            src = random.choice(hubs) if random.random() < 0.3 else random.randint(1, num_nodes)
            dst = random.randint(1, num_nodes)
            if src == dst or (src, dst) in edges:
                continue
            edges.add((src, dst))
            weight = round(random.uniform(0.1, 1.0), 3)
            interactions = random.randint(1, 500)
            writer.writerow([src, dst, weight, interactions])
            edge_count += 1

    duration = time.time() - start_time
    stats = {
        "node_count": num_nodes,
        "relationship_count": edge_count,
        "nodes_file_bytes": os.path.getsize(nodes_file),
        "edges_file_bytes": os.path.getsize(edges_file),
        "dataset_source": "Synthetic Power-Law Social Network",
        "load_time_sec": round(duration, 2)
    }
    return nodes_file, edges_file, stats

if __name__ == "__main__":
    generate_graph_dataset()
