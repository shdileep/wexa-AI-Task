"""
Dataset generator & downloader for Graph Database Benchmarking.
Generates a realistic social/citation graph dataset with >100,000 relationships
and realistic property distributions (IDs, names, creation dates, weights, tags).
"""

import os
import sys
import csv
import random
import time
from typing import Tuple, List, Dict

# Ensure reproducibility
RANDOM_SEED = 42

def generate_graph_dataset(
    num_nodes: int = 25000,
    num_edges: int = 150000,
    output_dir: str = "./dataset/data"
) -> Tuple[str, str, Dict[str, int]]:
    """
    Generates synthetic nodes and edges CSV files.
    Nodes: User (id: INT, username: STRING, age: INT, category: STRING, created_at: STRING)
    Edges: FOLLOWS (src_id: INT, dst_id: INT, weight: FLOAT, interaction_count: INT)
    """
    os.makedirs(output_dir, exist_ok=True)
    random.seed(RANDOM_SEED)

    nodes_file = os.path.join(output_dir, "nodes.csv")
    edges_file = os.path.join(output_dir, "edges.csv")

    categories = ["Tech", "Science", "Arts", "Finance", "Gaming", "Education", "Healthcare"]
    usernames_prefix = ["alex", "jordan", "taylor", "morgan", "sam", "riley", "casey", "quinn", "skyler", "avery"]

    print(f"[Dataset Generator] Generating {num_nodes:,} nodes and {num_edges:,} relationships...")
    start_time = time.time()

    # 1. Generate Nodes
    nodes = []
    with open(nodes_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "username", "age", "category", "created_at"])
        
        for node_id in range(1, num_nodes + 1):
            uname = f"{random.choice(usernames_prefix)}_{node_id}"
            age = random.randint(18, 75)
            cat = random.choice(categories)
            created_at = f"2024-{(node_id % 12) + 1:02d}-{(node_id % 28) + 1:02d}"
            writer.writerow([node_id, uname, age, cat, created_at])
            nodes.append(node_id)

    # 2. Generate Edges (Power-law like degree distribution using preferential attachment approximation)
    edges = set()
    edge_count = 0

    # Ensure a connected core
    with open(edges_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["src_id", "dst_id", "weight", "interaction_count"])

        # High-degree hub nodes (top 5% of nodes)
        hubs = list(range(1, max(2, int(num_nodes * 0.05))))

        while edge_count < num_edges:
            # Pick source node (70% probability from all, 30% from hubs)
            if random.random() < 0.3:
                src = random.choice(hubs)
            else:
                src = random.randint(1, num_nodes)

            # Pick target node
            dst = random.randint(1, num_nodes)
            if src == dst:
                continue

            pair = (src, dst)
            if pair in edges:
                continue

            edges.add(pair)
            weight = round(random.uniform(0.1, 1.0), 3)
            interactions = random.randint(1, 500)

            writer.writerow([src, dst, weight, interactions])
            edge_count += 1

            if edge_count % 50000 == 0:
                print(f"  Progress: {edge_count:,} / {num_edges:,} edges created...")

    duration = time.time() - start_time
    stats = {
        "node_count": num_nodes,
        "relationship_count": edge_count,
        "nodes_file_bytes": os.path.getsize(nodes_file),
        "edges_file_bytes": os.path.getsize(edges_file),
        "generation_time_sec": round(duration, 2)
    }

    print(f"[Dataset Generator] Complete! Created {stats['node_count']:,} nodes & {stats['relationship_count']:,} relationships in {duration:.2f}s.")
    return nodes_file, edges_file, stats

if __name__ == "__main__":
    generate_graph_dataset()
