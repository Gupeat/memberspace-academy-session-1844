# #1844 · 学院课期表 acad_course_session 模型与迁移

本仓库交付会员空间平台学院课期表 **acad_course_session** 的 SQLAlchemy 2.x 模型与 Alembic 迁移。范围严格限定为模型、迁移、约束和验证；不包含状态自动推进、接口或业务服务。

## 交付内容

| 路径 | 说明 |
| --- | --- |
| `app/db.py` | SQLAlchemy `Base`、命名约定、统一系统字段 mixin、引擎工厂（SQLite 打开外键） |
| `app/academy/models.py` | `AcadCourseSession` 模型、13 个 CHECK、2 个唯一约束、2 个索引、ORM 校验器 |
| `app/academy/constants.py` | 六种状态、字段长度与容量边界 |
| `alembic/versions/0001_acad_course_session.py` | 建表/索引/约束与 downgrade |
| `alembic.ini`、`alembic/env.py` | 从 `ACADEMY_DB_URL` 读取连接，排除外部依赖表 `acad_course` 的 autogenerate 漂移 |
| `tests/` | 20 个测试：约束、默认值、唯一性、迁移、alembic check |
| `scripts/run_acceptance.py` | 生成 `artifacts/ACCEPTANCE.md` 与 `ACCEPTANCE.json` |
| `scripts/run_pg16_round.py` | 在 PostgreSQL 16 上执行完整空库/种子库升级降级轮次 |
| `scripts/export_pg_ddl.py` | 导出最终 PostgreSQL DDL 到 `artifacts/schema-postgres.sql` |
| `scripts/reverse_drill.py` | 反向变异验证测试确实能捕获约束缺失 |

## 字段

### 统一系统字段

| 字段 | 类型 | 约束/默认 |
| --- | --- | --- |
| id | UUID | 主键，应用侧默认 uuid4 |
| org_id | UUID | 非空 |
| site_id | UUID | 可空 |
| created_at | timestamptz | 非空，server default now() |
| created_by | UUID | 可空 |
| updated_at | timestamptz | 非空，server default now()，ORM onupdate |
| deleted_at | timestamptz | 可空；软删除标记 |

### 业务字段

| 字段 | 类型 | 约束/默认 |
| --- | --- | --- |
| course_id | UUID | 非空，外键 `acad_course.id` |
| session_no | integer | 非空，>= 1；与 course_id 联合唯一 |
| label | varchar(20) | 非空，去空格后非空 |
| start_at | timestamptz | 非空 |
| end_at | timestamptz | 非空，必须晚于 start_at |
| room_name | varchar(30) | 非空，去空格后非空 |
| capacity | integer | 非空，1–500 |
| waitlist_capacity | integer | 非空，默认 0，0–100 |
| signup_open_at | timestamptz | 非空，必须早于 signup_close_at |
| signup_close_at | timestamptz | 非空，必须不晚于 start_at |
| require_review | boolean | 非空，默认 false |
| cancel_deadline_hours | integer | 非空，默认 24，>= 0 |
| event_id | UUID | 可空，唯一 |
| application_template_id | UUID | 可空 |
| status | varchar(16) | 非空，默认 scheduled；六值闭集 |
| cancel_reason | varchar(200) | 可空，长度 <= 200 |

状态闭集：`scheduled`、`signup_open`、`signup_closed`、`in_progress`、`finished`、`cancelled`。

## 约束清单（数据库层）

1. `ck_acad_course_session_time_order`: `end_at > start_at`
2. `ck_acad_course_session_signup_window`: `signup_open_at < signup_close_at`
3. `ck_acad_course_session_signup_before_start`: `signup_close_at <= start_at`
4. `ck_acad_course_session_capacity_range`: `capacity BETWEEN 1 AND 500`
5. `ck_acad_course_session_waitlist_range`: `waitlist_capacity BETWEEN 0 AND 100`
6. `ck_acad_course_session_session_no_positive`: `session_no >= 1`
7. `ck_acad_course_session_cancel_deadline_nonnegative`: `cancel_deadline_hours >= 0`
8. `ck_acad_course_session_status_enum`: 六状态闭集
9. `ck_acad_course_session_label_length`: `length(label) <= 20`
10. `ck_acad_course_session_label_not_blank`: `length(trim(label)) > 0`
11. `ck_acad_course_session_room_name_length`: `length(room_name) <= 30`
12. `ck_acad_course_session_room_name_not_blank`: `length(trim(room_name)) > 0`
13. `ck_acad_course_session_cancel_reason_length`: `cancel_reason IS NULL OR length(cancel_reason) <= 200`

唯一约束：

- `uq_acad_course_session_course_session_no` (`course_id`, `session_no`)
- `uq_acad_course_session_event_id` (`event_id`)；多行 NULL 允许

索引：

- `ix_acad_course_session_org_start` (`org_id`, `start_at`)
- `ix_acad_course_session_course_start` (`course_id`, `start_at`)

## 外部依赖说明

`acad_course` 由兄弟任务 #1839 拥有，真实表包含多列。本任务不创建、不修改该业务表；`app/academy/models.py` 中的 `acad_course = Table(...)` 只是 SQLAlchemy metadata 的 FK 解析桩，`alembic/env.py` 的 `include_object` 将其排除在 autogenerate 之外。迁移为了能在空库独立执行，会先 `CREATE TABLE IF NOT EXISTS acad_course (id UUID PRIMARY KEY)`；若真实表已存在则不会覆盖。downgrade 只删除 `acad_course_session`，保留 `acad_course`，避免毁掉兄弟任务的数据。

## 运行

环境：Python 3.12、SQLAlchemy 2.x、Alembic 1.x、pytest；PostgreSQL 16 用于完整迁移验证。

```powershell
python -m pip install -r requirements.txt

# SQLite 快速验证
$env:ACADEMY_DB_URL = "sqlite:///./acad_sessions.db"
python -m alembic upgrade head
python -m pytest -q tests

# PostgreSQL 16 两轮（127.0.0.1:55432，自动建库 clawhunt_1844）
python scripts/run_pg16_round.py --label round1
python scripts/run_pg16_round.py --label round2

# 验收与证据
python scripts/run_acceptance.py
python scripts/export_pg_ddl.py
python scripts/reverse_drill.py
```

## 验收结果

- SQLite / PostgreSQL 测试：**20 passed**。
- PostgreSQL 16.15 两轮：round1 2026-11-20T15:38:03Z、round2 2026-11-20T15:38:41Z，均 Overall PASS。
  - 空库 upgrade → 1 张 session 表、23 列、13 CHECK → downgrade 后 session 0 行、acad_course 保留 → 再次 upgrade PASS。
  - 种子库（2 个 course、1 个 session）upgrade → downgrade 后 session 表消失、course 仍 2 行 → 再次 upgrade 后 session 表恢复、course 仍 2 行。
  - 两轮均执行 `alembic check`，无模型/迁移漂移。
- AC1：`end_at <= start_at` 与 `signup_close_at > start_at` 插入均被数据库拒绝。
- AC2：同课程重复 `session_no` 被联合唯一约束拒绝；不同课程可重复。
- AC3：空库与种子库 upgrade/downgrade 均成功，downgrade 保留 `acad_course`。
- 反向变异：A 将 `end_at > start_at` 放宽为 `>=`、B 删除 `(course_id, session_no)` 唯一约束，测试均失败（DETECTED）。
- DDL：`artifacts/schema-postgres.sql`，含 13 CHECK、2 UNIQUE、2 索引、FK。

## 限制

- 不实现状态自动推进、报名、审核、取消流程或 HTTP API。
- 软删除不释放 `(course_id, session_no)` 唯一名额；任务未要求重建同一期次，按全量唯一处理。
- `updated_at` 的自动更新由 ORM `onupdate` 提供，不是数据库触发器。
- `acad_course` 是外部依赖；本仓库的 stub 只用于 FK 解析和空库迁移，不声明其真实列。
- 测试覆盖约束与迁移，不覆盖并发下的竞态；唯一性最终由数据库约束保证。
