#!/usr/bin/env python3
"""
Session Pilot Pro Plus — Empirical Storage Latency & Throughput Benchmark
==========================================================================
Measures real disk I/O latency (ms/op) and throughput (ops/sec) using
standard library time.perf_counter across 100 consecutive operations
for both JSON file and SQLite WAL storage engines.

Usage:
    python scripts/bench_storage.py [--iterations 100]
"""

import argparse
import shutil
import sys
import tempfile
import time
from pathlib import Path

# Force UTF-8 on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT_DIR = Path(__file__).resolve().parent.parent
ADAPTERS_DIR = ROOT_DIR / "adapters"
sys.path.insert(0, str(ADAPTERS_DIR))


def run_bench(adapter_name: str, iterations: int = 100) -> dict:
    import importlib.util
    mod_path = ADAPTERS_DIR / f"{adapter_name}.py"
    spec = importlib.util.spec_from_file_location(f"bench_{adapter_name}", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tmp_dir = Path(tempfile.mkdtemp(prefix=f"sp_bench_{adapter_name}_"))
    try:
        store = mod.SessionStore(home=tmp_dir) if adapter_name == "json_file" else mod.SessionStore(db_path=tmp_dir / "bench.db")

        # 1. Benchmark Save Latency & Throughput
        sid = f"bench-session-{int(time.time())}"
        t0 = time.perf_counter()
        for i in range(iterations):
            store.save(sid, done=f"action step {i}", next=f"next step {i+1}")
        t1 = time.perf_counter()
        save_total_sec = t1 - t0
        save_ms_per_op = (save_total_sec / iterations) * 1000.0
        save_throughput = iterations / save_total_sec

        # 2. Benchmark Load Latency
        t0 = time.perf_counter()
        for _ in range(iterations):
            _ = store.load(sid)
        t1 = time.perf_counter()
        load_total_sec = t1 - t0
        load_ms_per_op = (load_total_sec / iterations) * 1000.0

        # 3. Benchmark Fact Write Latency
        proj = "bench-project"
        t0 = time.perf_counter()
        for i in range(iterations):
            store.fact_set(proj, f"key_{i}", f"value_{i}")
        t1 = time.perf_counter()
        fact_total_sec = t1 - t0
        fact_ms_per_op = (fact_total_sec / iterations) * 1000.0

        # 4. Measure disk size
        total_bytes = sum(f.stat().st_size for f in tmp_dir.rglob("*") if f.is_file())
        disk_kb = total_bytes / 1024.0

        return {
            "adapter": adapter_name,
            "save_ms": save_ms_per_op,
            "load_ms": load_ms_per_op,
            "fact_ms": fact_ms_per_op,
            "save_throughput": save_throughput,
            "disk_kb": disk_kb,
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Session Pilot Pro Plus Storage Benchmark")
    parser.add_argument("--iterations", type=int, default=100, help="Operations per test phase (default: 100)")
    args = parser.parse_args()

    print(f"Running Empirical Storage Engine Benchmark ({args.iterations} iterations per phase)...\n")
    results = []
    for adapter in ["json_file", "sqlite"]:
        res = run_bench(adapter, iterations=args.iterations)
        results.append(res)

    print("=" * 86)
    print(f"{'Adapter':<12} {'Save Latency':<16} {'Load Latency':<16} {'Fact Write':<14} {'Throughput':<16} {'Disk Size'}")
    print("=" * 86)
    for r in results:
        print(f"{r['adapter']:<12} {r['save_ms']:>6.2f} ms/op      {r['load_ms']:>6.2f} ms/op      {r['fact_ms']:>6.2f} ms/op   {r['save_throughput']:>6.1f} ops/sec   {r['disk_kb']:>6.1f} KB")
    print("=" * 86)
    print("\nBenchmark completed successfully.")


if __name__ == "__main__":
    main()
