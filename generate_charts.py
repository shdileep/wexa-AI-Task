"""
Chart Generation Utility.
Renders clean, publication-ready visual benchmark charts and saves them to ./charts/
"""

import os
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'figure.titlesize': 18
    })
except ImportError:
    MATPLOTLIB_AVAILABLE = False

PALETTE = ["#3498db", "#2ecc71", "#e74c3c", "#9b59b6", "#f1c40f"]

def generate_benchmark_charts(results_dict: dict, output_dir: str = "./charts"):
    if not MATPLOTLIB_AVAILABLE:
        print("[Chart Generator] Warning: matplotlib/seaborn not installed. Install via pip install matplotlib seaborn.")
        return
    os.makedirs(output_dir, exist_ok=True)
    platforms = list(results_dict.keys())
    
    # Check if results are mock simulated
    is_mock = any(results_dict[p].get("data_source") == "MOCK_SIMULATED" for p in platforms)
    watermark_text = "Data Source: MOCK_SIMULATED (Simulated Baseline)" if is_mock else "Data Source: LIVE_MEASURED (Live Production)"
    watermark_color = "#c0392b" if is_mock else "#27ae60"

    # 1. Ingest Throughput Chart
    fig, ax = plt.subplots(figsize=(10, 6.5))
    edges_per_sec = [results_dict[p]["ingest"]["edges_per_sec"] for p in platforms]
    
    bars = ax.bar(platforms, edges_per_sec, color=PALETTE[:len(platforms)], width=0.55)
    ax.set_ylabel("Ingest Throughput (Relationships / sec)")
    ax.set_title("Data Ingestion Speed (150,000 Relationships)")
    
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:,.0f}/s',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontweight='bold')

    fig.text(0.5, 0.02, watermark_text, ha='center', fontsize=11, color=watermark_color, fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.3", fc="#f8f9fa", ec=watermark_color, lw=1.5))
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(os.path.join(output_dir, "ingest_throughput.png"), dpi=300)
    plt.close()

    # 2. Traversal Latency Chart (1-hop, 2-hop, 3-hop p95)
    fig, ax = plt.subplots(figsize=(12, 6.5))
    x = np.arange(len(platforms))
    width = 0.25

    p1_hop = [results_dict[p]["read"]["1hop_traversal"]["p95"] for p in platforms]
    p2_hop = [results_dict[p]["read"]["2hop_traversal"]["p95"] for p in platforms]
    p3_hop = [results_dict[p]["read"]["3hop_traversal"]["p95"] for p in platforms]

    ax.bar(x - width, p1_hop, width, label='1-Hop Traversal (p95)', color='#2ecc71')
    ax.bar(x, p2_hop, width, label='2-Hop Traversal (p95)', color='#3498db')
    ax.bar(x + width, p3_hop, width, label='3-Hop Traversal (p95)', color='#e74c3c')

    ax.set_ylabel("Latency (ms) - Lower is better")
    ax.set_title("Graph Traversal Latency by Hop Depth (p95 Percentile)")
    ax.set_xticks(x)
    ax.set_xticklabels(platforms)
    ax.legend()

    fig.text(0.5, 0.02, watermark_text, ha='center', fontsize=11, color=watermark_color, fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.3", fc="#f8f9fa", ec=watermark_color, lw=1.5))
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(os.path.join(output_dir, "traversal_latencies.png"), dpi=300)
    plt.close()

    # 3. Concurrency Scaling Chart
    fig, ax = plt.subplots(figsize=(10, 6.5))
    for idx, p in enumerate(platforms):
        concurrency_data = results_dict[p]["concurrency"]
        clients = sorted([int(c) for c in concurrency_data.keys()])
        qps_values = [concurrency_data.get(c, concurrency_data.get(str(c), {})).get("sustained_qps", 0) for c in clients]
        ax.plot(clients, qps_values, marker='o', linewidth=2.5, label=p, color=PALETTE[idx % len(PALETTE)])

    ax.set_xlabel("Concurrent Client Workers")
    ax.set_ylabel("Sustained QPS (Queries / sec)")
    ax.set_title("Concurrency Scaling (1 / 10 / 40 Clients - Mixed 80/20 Read/Write)")
    ax.set_xticks([1, 10, 40])
    ax.legend()

    fig.text(0.5, 0.02, watermark_text, ha='center', fontsize=11, color=watermark_color, fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.3", fc="#f8f9fa", ec=watermark_color, lw=1.5))
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(os.path.join(output_dir, "concurrency_scaling.png"), dpi=300)
    plt.close()

    # 4. Cold vs Warm Latency Comparison Chart
    fig, ax = plt.subplots(figsize=(10, 6.5))
    cold_lats = [results_dict[p]["read"].get("cold_start_ms", 15.0) for p in platforms]
    warm_lats = [results_dict[p]["read"]["1hop_traversal"]["p50"] for p in platforms]

    x = np.arange(len(platforms))
    width = 0.35

    rects1 = ax.bar(x - width/2, cold_lats, width, label='Cold-Start Latency (First Run)', color='#e74c3c')
    rects2 = ax.bar(x + width/2, warm_lats, width, label='Warm-State p50 Latency', color='#2ecc71')

    ax.set_ylabel("Latency (ms) - Lower is better")
    ax.set_title("Cold-Start Execution vs Warm-State Query Latency")
    ax.set_xticks(x)
    ax.set_xticklabels(platforms)
    ax.legend()

    fig.text(0.5, 0.02, watermark_text, ha='center', fontsize=11, color=watermark_color, fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.3", fc="#f8f9fa", ec=watermark_color, lw=1.5))
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(os.path.join(output_dir, "cold_vs_warm.png"), dpi=300)
    plt.close()

    print(f"[Chart Generator] Successfully saved visual charts to {output_dir}/")
