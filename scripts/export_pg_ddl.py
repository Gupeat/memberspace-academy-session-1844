"""Export the final PostgreSQL DDL for #1844 from a fresh alembic upgrade."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = REPO_ROOT / "artifacts"
PG_BIN = Path(
    os.environ.get(
        "PG_BIN",
        Path(os.environ.get("TEMP", ".")) / "clawhunt-pg16" / "pg" / "pgsql" / "bin",
    )
)
PSQL = PG_BIN / "psql.exe"
PG_DUMP = PG_BIN / "pg_dump.exe"
DB = "clawhunt_1844_ddl"
PG_URL = f"postgresql+psycopg2://postgres@127.0.0.1:55432/{DB}"


def run(args: list[str], env: dict[str, str], check: bool = False) -> subprocess.CompletedProcess:
    completed = subprocess.run(
        args,
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and completed.returncode != 0:
        raise SystemExit(f"command failed ({completed.returncode}): {' '.join(args)}\n{completed.stdout}{completed.stderr}")
    return completed


def main() -> int:
    env = os.environ.copy()
    env["PATH"] = str(PG_BIN) + os.pathsep + env.get("PATH", "")
    env["ACADEMY_DB_URL"] = PG_URL
    env["PYTHONIOENCODING"] = "utf-8"
    for binary in (PSQL, PG_DUMP):
        if not binary.is_file():
            raise SystemExit(
                f"not found: {binary}\n"
                "Set PG_BIN to the PostgreSQL 16 bin directory before running this script."
            )
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    exists = run([str(PSQL), "-h", "127.0.0.1", "-p", "55432", "-U", "postgres", "-d", "postgres", "-tAc",
                  f"SELECT 1 FROM pg_database WHERE datname='{DB}';"], env)
    if "1" not in exists.stdout:
        run([str(PSQL), "-h", "127.0.0.1", "-p", "55432", "-U", "postgres", "-d", "postgres",
             "-c", f"CREATE DATABASE {DB};"], env, check=True)

    run([sys.executable, "-m", "alembic", "upgrade", "head"], env, check=True)
    dumped = run([str(PG_DUMP), "-h", "127.0.0.1", "-p", "55432", "-U", "postgres",
                  "--schema-only", "--no-owner", "--no-privileges", DB], env, check=True)
    out = ARTIFACTS / "schema-postgres.sql"
    out.write_text(dumped.stdout, encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(REPO_ROOT).as_posix()} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
