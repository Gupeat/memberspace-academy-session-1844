# 验证产物说明

本目录是仓库的一部分，由仓库内脚本生成，用于让评审者不必先运行环境就能核对结果。

## 文件

- `ACCEPTANCE.md` / `ACCEPTANCE.json`：验收汇总。默认是 **SQLite 快速回归**口径（未设置 `TEST_DATABASE_URL`）；PostgreSQL 16 两轮证据单独列在第 22–29 行。
- `pytest.log`：验收脚本执行时的完整 pytest 输出。
- `pg16/round1/`、`pg16/round2/`：PostgreSQL 16.15 两轮，每轮 28 个步骤日志（`00-*` 到 `27-*`）和 `SUMMARY.md`。
  - `22-pytest-seeded-pg16.log` 是专用 seeded 用例输出，含 `seeded cycle database: postgresql` 和 `1 passed`。
  - `SUMMARY.md` 的 Overall PASS 需要所有步骤 exit 0、约束/表/行数断言通过、`alembic check` 通过。
- `schema-postgres.sql`：从实际 PostgreSQL 16 数据库导出的 DDL，含 13 CHECK、2 UNIQUE、2 索引、1 FK。
- `reverse-drill.log`：两个反向变异的演练记录；两个变异都必须被测试检出（DETECTED）。

## 复现

在仓库根目录执行：

```powershell
python -m pip install -r requirements.txt
python -m pytest -q tests
python scripts/run_acceptance.py
python scripts/run_pg16_round.py --label round1
python scripts/run_pg16_round.py --label round2
python scripts/export_pg_ddl.py
python scripts/reverse_drill.py
```

PostgreSQL 两轮需要本机有一个可连接的 PostgreSQL 16 实例（默认 `127.0.0.1:55432`，用户 `postgres`），并能创建 `clawhunt_1844`。SQLite 快速回归不需要 PostgreSQL。

## 边界

- 产物是某一时点的运行记录，不是实时服务；数字以 `ACCEPTANCE.json` 和两轮 `SUMMARY.md` 为准。
- 不包含真实用户数据、密钥或本机绝对路径。
