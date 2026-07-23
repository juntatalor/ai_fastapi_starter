"""Worker CLI entry-point."""

import uvicorn

from src.workers.worker.config import get_worker_settings


def main() -> None:
    s = get_worker_settings()
    uvicorn.run(
        "src.workers.worker.app:app",
        host="0.0.0.0",
        port=s.worker_metrics_port,
        log_level=s.log_level.lower(),
    )


if __name__ == "__main__":
    main()
