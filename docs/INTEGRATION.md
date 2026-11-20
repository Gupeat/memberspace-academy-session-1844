# 与兄弟任务 #1839 的集成说明

本仓库是 **#1844 的独立交付**，只拥有 `acad_course_session`；`acad_course` 业务表由 #1839 拥有。本文件记录两者合并时必须处理的边界，避免把“单仓可验收”误读为“可直接合入”。

## 1. 单仓行为（本仓库已验证）

- `alembic/versions/0001_acad_course_session.py` 是独立根 revision（`down_revision = None`）。
- 为满足 `course_id -> acad_course.id` 外键并让空库可执行，upgrade 先执行：
  `CREATE TABLE IF NOT EXISTS acad_course (id UUID PRIMARY KEY)`
  这是 **FK 解析/空库验收用的最小桩**，不是 #1839 的完整课程表。
- 若 `acad_course` 已存在（例如先跑了 #1839），该语句是 no-op，不会覆盖真实列。
- downgrade 只删除 `acad_course_session`，保留 `acad_course` 桩/真表，避免破坏兄弟任务数据。

## 2. 合并时的已知阻塞

在本仓库与 #1839 仓库各自保持独立 revision 的前提下，合并会失败：

1. **ORM 冲突**：本仓库 `app/academy/models.py` 用 `Table("acad_course", ...)` 只声明 `id` 桩；#1839 用 `mapped class` 声明完整模型。两者注册到同一 `Base.metadata` 时会抛
   `InvalidRequestError: Table 'acad_course' is already defined`（取决于 import 顺序）。
2. **迁移链冲突**：两个仓库的 `0001_*` 都是 `down_revision = None`。合并进一个 `alembic/versions` 后会得到 **multiple heads**；若强行 `upgrade heads` 且本仓库先执行，本仓库的最小桩会让 #1839 的
   `op.create_table("acad_course", ...)` 抛 `DuplicateTable: relation "acad_course" already exists`。
3. **唯一可工作的顺序**：先执行 #1839 的 `0001_acad_course` 建真实表。本仓库的 `CREATE TABLE IF NOT EXISTS` 变成 no-op；但两个独立 revision 仍必须在合并仓库中重写为单链（见下）。

## 3. 合并方必须做的修改

- 把本仓库 revision 的 `down_revision` 指向 #1839 的 revision id（形成单链），不要在合并仓库保留两个根。
- 删除本仓库 migration 中的 `CREATE TABLE IF NOT EXISTS acad_course ...`；真实表由 #1839 提供。
- 删除本仓库 `app/academy/models.py` 中的 `acad_course = Table(...)` 桩，改为引用 #1839 的 `AcadCourse` 映射类（或共享模型模块）。
- 合并后跑：
  ```powershell
  python -m alembic upgrade head
  python -m alembic downgrade base
  python -m alembic upgrade head
  python -m pytest -q tests
  ```
  并确认 `alembic check` 无漂移、`acad_course` 数据在 downgrade 中保留。

## 4. 本仓库的边界

- 不修改 #1839 的代码；不声称两个独立仓库可以直接合并。
- 单仓的空库/种子库 upgrade/downgrade、20 tests、13 CHECK、2 UNIQUE、2 索引均已验证，见 `artifacts/`。
- 合并补丁属于集成方职责；若平台要求本仓库直接合入，需先完成第 3 节的三处修改并重跑迁移与测试。
