"""Prometheus-метрики воркера."""

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

# 1 — pgqueuer consumer в фазе pgq.run (LISTEN активен), 0 — down или ждёт retry.
# Живёт под супервизором в src.common.queue.pgqueuer.PgQueuerQueue.
pgqueuer_dispatch_up = Gauge(
    "pgqueuer_dispatch_up", "1 если consumer в pgq.run, иначе 0"
)
# Инкрементится каждый раз, когда pgq.run упал и супервизор запускает
# заново. По этой метрике алерт «consumer перезапускается чаще N раз в час».
pgqueuer_dispatch_restarts_total = Counter(
    "pgqueuer_dispatch_restarts_total", "Сколько раз супервизор рестартил consumer"
)
