"""Run one reproducible PostgreSQL 16 acceptance round for #1844."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PG_BIN = Path(
    os.environ.get(
        "PG_BIN",
        Path(os.environ.get("TEMP", ".")) / "clawhunt-pg16" / "pg" / "pgsql" / "bin",
    )
)
PSQL = PG_BIN / "psql.exe"
PSQL_DB = "clawhunt_1844"
PG_URL = f"postgresql+psycopg2://postgres@127.0.0.1:55432/{PSQL_DB}"
SEED_A = "11111111-1111-1111-1111-111111111111"
SEED_B = "22222222-2222-2222-2222-222222222222"
SESSION_ID = "33333333-3333-3333-3333-333333333333"


def redact(text: str) -> str:
    text = text.replace(str(REPO_ROOT), "<repo>")
    text = text.replace(str(Path(os.environ.get("TEMP", ""))), "<tmp>")
    home = str(Path.home())
    text = text.replace(home, "<home>").replace(home.replace("\\", "/"), "<home>")
    text = text.replace("pytest-of-" + Path.home().name, "pytest-of-user")
    return text


def run(args: list[str], env: dict[str, str], timeout: int = 300) -> tuple[int, str]:
    completed = subprocess.run(
        args,
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return completed.returncode, redact((completed.stdout or "") + (completed.stderr or ""))


def psql(sql: str, env: dict[str, str], database: str | None = None) -> tuple[int, str]:
    return run(
        [
            str(PSQL),
            "-h",
            "127.0.0.1",
            "-p",
            "55432",
            "-U",
            "postgres",
            "-d",
            database or PSQL_DB,
            "-v",
            "ON_ERROR_STOP=1",
            "-tAc",
            sql,
        ],
        env,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="round")
    args = parser.parse_args()

    out_dir = REPO_ROOT / "artifacts" / "pg16" / args.label
    out_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PATH"] = str(PG_BIN) + os.pathsep + env.get("PATH", "")
    env["ACADEMY_DB_URL"] = PG_URL
    env["TEST_DATABASE_URL"] = PG_URL
    env["PYTHONIOENCODING"] = "utf-8"

    code, out = run(
        [str(PSQL), "-h", "127.0.0.1", "-p", "55432", "-U", "postgres", "-d", "postgres", "-tAc",
         "SELECT 1 FROM pg_database WHERE datname='clawhunt_1844';"],
        env,
    )
    if "1" not in out:
        run(
            [str(PSQL), "-h", "127.0.0.1", "-p", "55432", "-U", "postgres", "-d", "postgres", "-c",
             "CREATE DATABASE clawhunt_1844;"],
            env,
        )

    steps: list[tuple[str, int, str]] = []

    def record(name: str, code: int, output: str) -> None:
        steps.append((name, code, output))
        (out_dir / f"{len(steps)-1:02d}-{name}.log").write_text(output, encoding="utf-8")

    def psql_step(name: str, sql: str) -> str:
        code, out = psql(sql, env)
        record(name, code, out)
        return out.strip()

    def alembic_step(name: str, action: str) -> None:
        code, out = run([sys.executable, "-m", "alembic", *action.split()], env)
        record(name, code, out)

    psql_step("reset-empty", "DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    alembic_step("upgrade-empty", "upgrade head")
    empty_tables = psql_step(
        "empty-session-table",
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='acad_course_session';",
    )
    psql_step(
        "empty-column-count",
        "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='acad_course_session';",
    )
    psql_step(
        "empty-check-count",
        "SELECT count(*) FROM pg_constraint WHERE conrelid='acad_course_session'::regclass AND contype='c';",
    )
    alembic_step("check-empty", "check")
    alembic_step("downgrade-empty", "downgrade base")
    after_down_tables = psql_step(
        "after-downgrade-session-table",
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='acad_course_session';",
    )
    after_down_course = psql_step(
        "after-downgrade-course-table",
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='acad_course';",
    )
    alembic_step("upgrade-empty-again", "upgrade head")

    psql_step("reset-seeded", "DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    psql_step("create-seed-course", "CREATE TABLE acad_course (id UUID PRIMARY KEY);")
    psql_step(
        "insert-seed-courses",
        f"INSERT INTO acad_course (id) VALUES ('{SEED_A}'), ('{SEED_B}');",
    )
    alembic_step("upgrade-seeded", "upgrade head")
    psql_step(
        "insert-seed-session",
        "INSERT INTO acad_course_session "
        "(id, org_id, course_id, session_no, label, start_at, end_at, room_name, capacity, "
        "signup_open_at, signup_close_at) VALUES "
        f"('{SESSION_ID}', gen_random_uuid(), '{SEED_A}', 1, 'Session 1', "
        "'2026-12-01 09:00+00', '2026-12-01 11:00+00', 'Room A', 30, "
        "'2026-11-20 09:00+00', '2026-11-30 09:00+00');",
    )
    alembic_step("downgrade-seeded", "downgrade base")
    seeded_down_session = psql_step(
        "seeded-after-downgrade-session-table",
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='acad_course_session';",
    )
    seeded_down_course_rows = psql_step(
        "seeded-after-downgrade-course-rows", "SELECT count(*) FROM acad_course;"
    )
    alembic_step("upgrade-seeded-again", "upgrade head")
    seeded_up_session = psql_step(
        "seeded-after-regrade-session-table",
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='acad_course_session';",
    )
    seeded_up_course_rows = psql_step(
        "seeded-after-regrade-course-rows", "SELECT count(*) FROM acad_course;"
    )

    code, out = run([sys.executable, "-m", "pytest", "tests"], env)
    record("pytest", code, out)
    alembic_step("upgrade-after-tests", "upgrade head")
    alembic_step("check-after-tests", "check")
    psql_step(
        "final-constraint-count",
        "SELECT count(*) FROM pg_constraint WHERE conrelid='acad_course_session'::regclass AND contype='c';",
    )
    psql_step(
        "final-unique-count",
        "SELECT count(*) FROM pg_constraint WHERE conrelid='acad_course_session'::regclass AND contype='u';",
    )
    psql_step(
        "final-index-count",
        "SELECT count(*) FROM pg_indexes WHERE schemaname='public' AND tablename='acad_course_session';",
    )

    passed_match = re.findall(r"(\d+) passed", "\n".join(output for name, _, output in steps if name == "pytest"))
    passed = int(passed_match[-1]) if passed_match else 0
    empty_ok = empty_tables.strip() == "1" and after_down_tables.strip() == "0" and after_down_course.strip() == "1"
    seeded_ok = (
        seeded_down_session.strip() == "0"
        and seeded_down_course_rows.strip() == "2"
        and seeded_up_session.strip() == "1"
        and seeded_up_course_rows.strip() == "2"
    )
    all_steps_ok = all(code == 0 for _, code, _ in steps)
    check_ok = any(name.startswith("check") and code == 0 for name, code, _ in steps)
    ok = all_steps_ok and check_ok and empty_ok and seeded_ok and passed > 0

    summary = [
        f"# PostgreSQL 16 acceptance · {args.label}",
        "",
        f"- PostgreSQL: 16.15 at 127.0.0.1:55432 / database {PSQL_DB}",
        f"- Generated: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"- Tests: {passed} passed",
        f"- Empty-DB upgrade/downgrade: {'PASS' if empty_ok else 'FAIL'}",
        f"- Seeded-DB upgrade/downgrade: {'PASS' if seeded_ok else 'FAIL'}",
        f"- Alembic check: {'PASS' if check_ok else 'FAIL'}",
        f"- Overall: {'PASS' if ok else 'FAIL'}",
        "",
        "## Steps",
        "",
        "| # | Step | Exit |",
        "| --- | --- | --- |",
    ]
    for index, (name, code, _) in enumerate(steps):
        summary.append(f"| {index} | {name} | {code} |")
    summary += ["", "## Evidence", "", "Logs 00-21 in this directory; pytest.log in artifacts/ is the combined acceptance log.", ""]
    (out_dir / "SUMMARY.md").write_text("\n".join(summary), encoding="utf-8")
    print("\n".join(summary))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
