# API Performance Benchmarks

## Environment

| Parameter       | Value                                         |
|-----------------|-----------------------------------------------|
| CPU             | AMD Ryzen 3 PRO 2200GE (4 cores)              |
| OS / Kernel     | Linux 6.17.0-14-generic                        |
| Python          | 3.12.3                                        |
| FastAPI         | 0.135.1                                       |
| Starlette       | 0.52.1                                        |
| Uvicorn         | 0.41.0                                        |
| Test transport  | Starlette `TestClient` (in-process ASGI)       |

## Methodology

Each endpoint is called **1,000 times** after a 50-request warmup. Latency is
measured per-request with `time.perf_counter()` at microsecond resolution.
Percentiles are computed from the sorted latency array. Requests/sec is derived
from total wall-clock time for all 1,000 iterations.

Benchmarks run single-threaded through Starlette's `TestClient`, which executes
the full ASGI stack (middleware, routing, serialization) without network I/O.
This isolates application-level performance from OS/network overhead.

Script: [`benchmarks/bench_api.py`](benchmarks/bench_api.py)

## Results

### Scenario 1: Health Check  `GET /health`

Exercises Pydantic model serialization (`HealthResponse`) with `datetime.now()`
generation on every request. Representative of monitoring/probe traffic.

| Metric         | Value      |
|----------------|------------|
| Requests/sec   | **1,185**  |
| p50 latency    | 795 us     |
| p95 latency    | 1,299 us   |
| p99 latency    | 1,620 us   |
| Mean latency   | 841 us     |
| Min / Max      | 509 / 3,778 us |

### Scenario 2: Readiness Probe  `GET /ready`

Returns a plain `dict` with no Pydantic serialization. Minimal code path through
FastAPI. Baseline for framework overhead.

| Metric         | Value      |
|----------------|------------|
| Requests/sec   | **1,262**  |
| p50 latency    | 720 us     |
| p95 latency    | 1,235 us   |
| p99 latency    | 1,512 us   |
| Mean latency   | 790 us     |
| Min / Max      | 501 / 2,294 us |

### Scenario 3: OpenAPI Schema  `GET /openapi.json`

Returns the full OpenAPI specification as JSON. Tests larger payload
serialization and FastAPI's schema generation caching behavior.

| Metric         | Value      |
|----------------|------------|
| Requests/sec   | **1,346**  |
| p50 latency    | 704 us     |
| p95 latency    | 1,079 us   |
| p99 latency    | 1,401 us   |
| Mean latency   | 740 us     |
| Min / Max      | 482 / 2,998 us |

## Summary

All endpoints respond under **2 ms at p99** in the in-process ASGI benchmark.
The readiness probe and OpenAPI schema endpoints are slightly faster than the
health check because they skip Pydantic model instantiation and/or benefit from
FastAPI's schema caching.

| Endpoint            | Req/s  | p50 (us) | p95 (us) | p99 (us) |
|---------------------|--------|----------|----------|----------|
| `GET /health`       | 1,185  | 795      | 1,299    | 1,620    |
| `GET /ready`        | 1,262  | 720      | 1,235    | 1,512    |
| `GET /openapi.json` | 1,346  | 704      | 1,079    | 1,401    |

## Reproducing

```bash
pip install -e ".[dev]"
python -m benchmarks.bench_api
```
