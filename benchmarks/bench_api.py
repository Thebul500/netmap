"""API endpoint benchmarks — measures requests/sec, p50/p95/p99 latency."""

import statistics
import time

from starlette.testclient import TestClient

from netmap.app import create_app

ITERATIONS = 1000
WARMUP = 50


def bench_endpoint(client: TestClient, method: str, path: str, n: int = ITERATIONS) -> dict:
    """Benchmark a single endpoint, return timing stats."""
    # Warmup
    for _ in range(WARMUP):
        getattr(client, method)(path)

    latencies_us: list[float] = []
    start = time.perf_counter()
    for _ in range(n):
        t0 = time.perf_counter()
        resp = getattr(client, method)(path)
        t1 = time.perf_counter()
        assert resp.status_code == 200, f"{path} returned {resp.status_code}"
        latencies_us.append((t1 - t0) * 1_000_000)  # microseconds
    wall = time.perf_counter() - start

    latencies_us.sort()
    return {
        "endpoint": f"{method.upper()} {path}",
        "iterations": n,
        "rps": n / wall,
        "p50_us": latencies_us[int(n * 0.50)],
        "p95_us": latencies_us[int(n * 0.95)],
        "p99_us": latencies_us[int(n * 0.99)],
        "mean_us": statistics.mean(latencies_us),
        "min_us": latencies_us[0],
        "max_us": latencies_us[-1],
        "stdev_us": statistics.stdev(latencies_us),
    }


def run_benchmarks() -> list[dict]:
    app = create_app()
    results = []
    with TestClient(app) as client:
        # Scenario 1: Health check (Pydantic serialization + datetime)
        results.append(bench_endpoint(client, "get", "/health"))

        # Scenario 2: Readiness probe (minimal dict response)
        results.append(bench_endpoint(client, "get", "/ready"))

        # Scenario 3: OpenAPI schema (large JSON payload generation)
        results.append(bench_endpoint(client, "get", "/openapi.json"))

    return results


def format_results(results: list[dict]) -> str:
    lines = []
    lines.append("=" * 78)
    lines.append("NETMAP API BENCHMARK RESULTS")
    lines.append("=" * 78)
    lines.append(f"Iterations per endpoint: {ITERATIONS} (+ {WARMUP} warmup)")
    lines.append("")

    for r in results:
        lines.append(f"--- {r['endpoint']} ---")
        lines.append(f"  Requests/sec:  {r['rps']:>10.1f}")
        lines.append(f"  Latency (us):  p50={r['p50_us']:.0f}  p95={r['p95_us']:.0f}  p99={r['p99_us']:.0f}")
        lines.append(f"  Mean (us):     {r['mean_us']:.0f}  stdev={r['stdev_us']:.0f}")
        lines.append(f"  Min/Max (us):  {r['min_us']:.0f} / {r['max_us']:.0f}")
        lines.append("")

    lines.append("=" * 78)
    return "\n".join(lines)


if __name__ == "__main__":
    results = run_benchmarks()
    print(format_results(results))
