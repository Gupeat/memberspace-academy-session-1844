# PostgreSQL 16 acceptance · round1

- PostgreSQL: 16.15 at 127.0.0.1:55432 / database clawhunt_1844
- Generated: 2026-11-22T05:12:01Z
- Tests: 20 passed
- Empty-DB upgrade/downgrade: PASS
- Seeded-DB upgrade/downgrade: PASS
- Alembic check: PASS
- Seeded test on PostgreSQL: PASS
- Overall: PASS

## Steps

| # | Step | Exit |
| --- | --- | --- |
| 0 | reset-empty | 0 |
| 1 | upgrade-empty | 0 |
| 2 | empty-session-table | 0 |
| 3 | empty-column-count | 0 |
| 4 | empty-check-count | 0 |
| 5 | check-empty | 0 |
| 6 | downgrade-empty | 0 |
| 7 | after-downgrade-session-table | 0 |
| 8 | after-downgrade-course-table | 0 |
| 9 | upgrade-empty-again | 0 |
| 10 | reset-seeded | 0 |
| 11 | create-seed-course | 0 |
| 12 | insert-seed-courses | 0 |
| 13 | upgrade-seeded | 0 |
| 14 | insert-seed-session | 0 |
| 15 | downgrade-seeded | 0 |
| 16 | seeded-after-downgrade-session-table | 0 |
| 17 | seeded-after-downgrade-course-rows | 0 |
| 18 | upgrade-seeded-again | 0 |
| 19 | seeded-after-regrade-session-table | 0 |
| 20 | seeded-after-regrade-course-rows | 0 |
| 21 | pytest | 0 |
| 22 | pytest-seeded-pg16 | 0 |
| 23 | upgrade-after-tests | 0 |
| 24 | check-after-tests | 0 |
| 25 | final-constraint-count | 0 |
| 26 | final-unique-count | 0 |
| 27 | final-index-count | 0 |

## Evidence

Logs 00-27 in this directory; pytest.log in artifacts/ is the combined acceptance log.
