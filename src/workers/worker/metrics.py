"""Prometheus-метрики worker'а."""

from prometheus_client import Counter, Gauge, Histogram

jobs_processed_total = Counter(
    "jobs_processed_total", "Total processed jobs", ["task", "status"]
)
job_duration_seconds = Histogram(
    "job_duration_seconds",
    "Time spent in handler",
    ["task"],
    buckets=(0.1, 0.5, 1.0, 5.0, 30.0, 60.0, 300.0),
)
worker_uptime_seconds = Gauge("worker_uptime_seconds", "Seconds since worker start")
