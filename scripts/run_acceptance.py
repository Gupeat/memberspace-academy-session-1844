"""Run the #1844 acceptance checks and write a reproducible evidence report."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = REPO_ROOT / "artifacts"
PYTHON = sys.executable
PG_EVIDENCE = [
    "artifacts/pg16/round1/SUMMARY.md",
    "artifacts/pg16/round2/SUMMARY.md",
]


def redact(text: str, tmp: str) -> str:
    text = text.replace(str(REPO_ROOT), "<repo>")
    text = text.replace(tmp, "<tmp>")
    home = os.environ.get("USERPROFILE") or os.environ.get("HOME") or ""
    if home:
        text = text.replace(home, "<home>").replace(home.replace("\\", "/"), "<home>")
        text = text.replace("pytest-of-" + Path(home).name, "pytest-of-user")
    return text


def run(args: list[str], env: dict[str, str], tmp: str) -> tuple[int, str]:
    completed = subprocess.run(
        args,
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, redact(output, tmp)


def main() -> int:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="academy-acceptance-")
    db = "sqlite:///" + str(Path(tmp) / "acceptance.db")
    env = os.environ.copy()
    env["ACADEMY_DB_URL"] = db
    env.pop("TEST_DATABASE_URL", None)
    env["PYTHONIOENCODING"] = "utf-8"

    steps: list[dict[str, object]] = []
    logs: list[str] = []

    def step(name: str, args: list[str]) -> int:
        code, output = run(args, env, tmp)
        display_args = ["python" if arg == PYTHON else arg for arg in args]
        command_text = redact(" ".join(display_args), tmp)
        steps.append({"name": name, "command": command_text, "exit": code})
        logs.append(f"$ {name}\n" + command_text + "\n" + output)
        return code

    ac1 = [
        step("AC1 end_at and signup_close constraints", [PYTHON, "-m", "pytest", "-q", "tests/test_constraints.py", "-k", "end_at or signup_close"]),
    ]
    ac2 = [
        step("AC2 session_no uniqueness", [PYTHON, "-m", "pytest", "-q", "tests/test_constraints.py", "-k", "duplicate_session_no or different_courses"]),
    ]
    ac3 = [
        step("AC3 upgrade/downgrade on empty database", [PYTHON, "-m", "pytest", "-q", "tests/test_migration.py::test_upgrade_downgrade_cycle"]),
        step("AC3 upgrade/downgrade on seeded database", [PYTHON, "-m", "pytest", "-q", "tests/test_migration.py::test_seeded_upgrade_downgrade_cycle"]),
        step("AC3 alembic check", [PYTHON, "-m", "pytest", "-q", "tests/test_migration.py::test_alembic_check_has_no_drift"]),
    ]
    full = step("Full regression", [PYTHON, "-m", "pytest", "-q", "tests"])

    combined = "\n".join(logs)
    (ARTIFACTS / "pytest.log").write_text(combined, encoding="utf-8")

    passed = 0
    matches = re.findall(r"(\d+) passed", combined)
    if matches:
        passed = int(matches[-1])
    pg_evidence_present = all((REPO_ROOT / path).is_file() for path in PG_EVIDENCE)
    ok = not any(ac1) and not any(ac2) and not any(ac3) and full == 0 and pg_evidence_present
    summary = {
        "ok": ok,
        "passed": passed,
        "ac1": not any(ac1),
        "ac2": not any(ac2),
        "ac3": not any(ac3),
        "full": full == 0,
        "database": "sqlite-quick",
        "postgresql_evidence": PG_EVIDENCE,
        "postgresql_evidence_present": pg_evidence_present,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "steps": steps,
    }

    lines = [
        "# Acceptance report · #1844",
        "",
        f"- Generated: {summary['generated_at']}",
        "- Database: SQLite quick regression (when TEST_DATABASE_URL is unset)",
        f"- SQLite quick regression tests: {passed} passed",
        f"- AC1 end_at / signup_close constraints: {'PASS' if summary['ac1'] else 'FAIL'}",
        f"- AC2 session_no uniqueness: {'PASS' if summary['ac2'] else 'FAIL'}",
        f"- AC3 SQLite quick upgrade/downgrade (empty, seeded, no drift): {'PASS' if summary['ac3'] else 'FAIL'}",
        f"- SQLite quick full regression: {'PASS' if summary['full'] else 'FAIL'}",
        f"- PostgreSQL 16 evidence present: {'PASS' if pg_evidence_present else 'FAIL'}",
        "",
        "## Commands and results",
        "",
        "| Step | Exit |",
        "| --- | --- |",
    ]
    for item in steps:
        lines.append(f"| {item['name']} | {item['exit']} |")
    lines += [
        "",
        "## PostgreSQL 16 evidence",
        "",
        "The seeded migration test now follows TEST_DATABASE_URL; each PG16 round runs a",
        "dedicated pytest-seeded-pg16 step that asserts seeded cycle database: postgresql",
        "and 1 passed.",
        "",
        "- round1: artifacts/pg16/round1/SUMMARY.md",
        "- round2: artifacts/pg16/round2/SUMMARY.md",
        "",
        "## Evidence",
        "",
        "- artifacts/pytest.log: SQLite quick regression output",
        "- artifacts/ACCEPTANCE.json: structured quick-regression summary",
        "- artifacts/pg16/: PostgreSQL 16 two-round logs, including the dedicated seeded test",
        "- artifacts/schema-postgres.sql: PostgreSQL DDL exported after upgrade",
        "- artifacts/reverse-drill.log: mutation-detection drill",
        "",
    ]
    (ARTIFACTS / "ACCEPTANCE.md").write_text("\n".join(lines), encoding="utf-8")
    (ARTIFACTS / "ACCEPTANCE.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())