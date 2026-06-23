"""Установка pgqueuer-схемы из PGQUEUER_DSN.

pgqueuer CLI 1.0 не принимает ``--dsn``, читает стандартные libpq env-vars
(``PGUSER``/``PGPASSWORD``/``PGHOST``/``PGPORT``/``PGDATABASE``). Парсим
``PGQUEUER_DSN`` и пробрасываем их перед вызовом ``pgq install``.
"""

from __future__ import annotations

import os
import subprocess
import sys
import urllib.parse


def main() -> int:
    dsn = os.environ.get("PGQUEUER_DSN")
    if not dsn:
        print("PGQUEUER_DSN is not set, skipping pgqueuer install")
        return 0
    p = urllib.parse.urlparse(dsn)
    env = os.environ.copy()
    env.update(
        PGUSER=p.username or "postgres",
        PGPASSWORD=p.password or "",
        PGHOST=p.hostname or "localhost",
        PGPORT=str(p.port or 5432),
        PGDATABASE=p.path.lstrip("/") or "app",
    )
    return subprocess.run(["pgq", "install"], env=env, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
