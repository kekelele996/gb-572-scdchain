# migrations

The runtime schema is created idempotently by `src.config.database.init_db()`
(SQLAlchemy `Base.metadata.create_all`) when the backend container starts, so a
fresh `docker compose up` needs no manual migration step.

`20261112_0001_initial.sql` is the authoritative DDL snapshot of that schema
(PostgreSQL 16) for review / offline provisioning. It is written to be re-runnable
and matches the models under `src/models/`.

| table | 说明 |
|---|---|
| `users` | 三角色演示账号（admin / modeler / auditor） |
| `source_systems` | 上游三个源系统（核心保单 / 会员中心 / 客服工单） |
| `customer_snapshots` | 每日全量快照原始行（自然键：source + business_key + snapshot_date） |
| `merge_rules` | 属性级合并策略：源优先级、归一化方式、忽略列标记 |
| `dim_customers` | SCD2 拉链版本（按 build_run 隔离，唯一 current 部分索引） |
| `build_runs` | 每次构建批次的统计与不变量报告 |
| `conflict_items` | 跨源冲突候选、归一化裁决与人工留痕 |
| `audit_logs` | 横切审计日志 |
