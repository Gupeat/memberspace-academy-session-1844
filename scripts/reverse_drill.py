"""Reverse drill for #1844: prove tests fail when key DB guarantees are removed."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = REPO_ROOT / "artifacts"
MIGRATION = Path("alembic/versions/0001_acad_course_session.py")

MUTATIONS = [
    (
        "A_end_at_allows_equal",
        'sa.CheckConstraint("end_at > start_at", name=op.f("ck_acad_course_session_time_order"))',
        'sa.CheckConstraint("end_at >= start_at", name=op.f("ck_acad_course_session_time_order"))',
        "tests/test_constraints.py",
        "end_at",
    ),
    (
        "B_drop_course_session_unique",
        '''        sa.UniqueConstraint(
            "course_id", "session_no", name=op.f("uq_acad_course_session_course_session_no")
        ),
''',
        "",
        "tests/test_constraints.py",
        "duplicate_session_no",
    ),
]


def run(cmd: list[str], cwd: Path, env: dict[str, str]) -> tuple[int, str]:
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    return completed.returncode, (completed.stdout or "") + (completed.stderr or "")


def main() -> int:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    lines: list[str] = ["# Reverse drill · #1844", ""]
    ok = True
    for name, old, new, test_file, keyword in MUTATIONS:
        temp = Path(tempfile.mkdtemp(prefix=f"reverse-{name}-"))
        target = temp / "repo"
        shutil.copytree(
            REPO_ROOT,
            target,
            ignore=shutil.ignore_patterns(".pytest_cache", "__pycache__", "artifacts", "*.pyc"),
        )
        migration = target / MIGRATION
        text = migration.read_text(encoding="utf-8")
        if old not in text:
            lines.append(f"- {name}: ERROR target text not found")
            ok = False
            shutil.rmtree(temp, ignore_errors=True)
            continue
        migration.write_text(text.replace(old, new, 1), encoding="utf-8")
        db = temp / "drill.db"
        env = os.environ.copy()
        env["ACADEMY_DB_URL"] = "sqlite:///" + str(db)
        env.pop("TEST_DATABASE_URL", None)
        env["PYTHONIOENCODING"] = "utf-8"
        code, output = run(
            [sys.executable, "-m", "pytest", "-q", test_file, "-k", keyword],
            target,
            env,
        )
        detected = code != 0
        ok = ok and detected
        lines.append(f"- {name}: {'DETECTED' if detected else 'NOT DETECTED'} (exit {code})")
        tail = [line for line in output.splitlines() if line.strip()][-3:]
        lines.extend(f"  {line}" for line in tail)
        shutil.rmtree(temp, ignore_errors=True)
    lines += ["", f"Overall: {'PASS' if ok else 'FAIL'}", ""]
    out = ARTIFACTS / "reverse-drill.log"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
