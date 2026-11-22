# Acceptance report · #1844

- Generated: 2026-11-22T04:10:58Z
- Database: SQLite quick regression (when TEST_DATABASE_URL is unset)
- SQLite quick regression tests: 20 passed
- AC1 end_at / signup_close constraints: PASS
- AC2 session_no uniqueness: PASS
- AC3 SQLite quick upgrade/downgrade (empty, seeded, no drift): PASS
- SQLite quick full regression: PASS

## Commands and results

| Step | Exit |
| --- | --- |
| AC1 end_at and signup_close constraints | 0 |
| AC2 session_no uniqueness | 0 |
| AC3 upgrade/downgrade on empty database | 0 |
| AC3 upgrade/downgrade on seeded database | 0 |
| AC3 alembic check | 0 |
| Full regression | 0 |

## PostgreSQL 16 evidence

The seeded migration test now follows TEST_DATABASE_URL; each PG16 round runs a
dedicated pytest-seeded-pg16 step that asserts seeded cycle database: postgresql
and 1 passed.

- round1: artifacts/pg16/round1/SUMMARY.md
- round2: artifacts/pg16/round2/SUMMARY.md

## Evidence

- artifacts/pytest.log: SQLite quick regression output
- artifacts/ACCEPTANCE.json: structured quick-regression summary
- artifacts/pg16/: PostgreSQL 16 two-round logs, including the dedicated seeded test
- artifacts/schema-postgres.sql: PostgreSQL DDL exported after upgrade
- artifacts/reverse-drill.log: mutation-detection drill
