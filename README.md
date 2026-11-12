# SCD Chain · 缓慢变化维 SCD2 拉链与一致性维度台

嘉禾保险数据仓库建模组的**客户维度年鉴**：把核心保单、会员中心、客服工单三个系统每天的全量客户快照，按业务键拉成 SCD2 链，并提供「任意一天当时等级」的时点回溯、跨源冲突归一化裁决与人工留痕。

> 一句话：监管要「当时等级」，BI 要「当前链」，这本年鉴让两边看到同一页。

## 1. 真实场景

- **客户**：嘉禾保险 · 数据仓库建模组（7 人）。客户维度来自 3 个系统，每日变更约 2000 条（演示 180 业务键 × 5 天）。
- **现有工作流**：每天取最新快照覆盖 → 历史状态查不到；三系统冲突靠打电话确认；拉链 SQL 手写，漏关链导致一人多条当前记录。
- **三个痛点**：① 监管审计要「当时等级 / 当时归属机构」查不到；② 跨源属性冲突无裁决留痕；③ 拉链不变量无校验。
- **上下游**：上游 = 3 源系统每日全量快照；本系统替代「手工 SQL 拉链 + 人工判断冲突」；下游 = 监管报送、BI 客户分析。

## 2. 角色与权限

| 角色 | 账号 | 页面 | 权限 | 典型动作 |
|---|---|---|---|---|
| `admin` 建模负责人 | `admin@scdchain.io` | 全部 | 维度定义 / 合并规则 / 发起构建 / 裁决 / 导出 / 审计日志 | 调整属性优先级，发起重建 |
| `modeler` 建模工程师 | `modeler@scdchain.io` | 除审计日志外全部 | 发起构建 / 处理冲突 / 查看校验；**改规则返回 403** | 跑 v2、裁决冲突 |
| `auditor` 审计只读 | `auditor@scdchain.io` | 只读浏览 | 任意时点回溯 + 导出；**发起构建 / 裁决 / 改规则均返回 403** | 回溯 2026-11-05 并导出 CSV |

密码统一 `Demo@2026`。权限在后端中间件 + 路由依赖双重生效（直接 curl 低权接口同样 403）。

## 3. 六条核心实体

| 实体 | 表 | 说明 |
|---|---|---|
| `SourceSystem` | `source_systems` | 三个上游系统：核心保单 / 会员中心 / 客服工单（含可信度、快照时间、接口人） |
| `CustomerSnapshot` | `customer_snapshots` | 每日全量快照原始行，自然键 `source + business_key + snapshot_date`，含迟到标记 |
| `DimCustomer` | `dim_customers` | SCD2 拉链版本：`valid_from / valid_to / is_current / version / version_source`，按 `build_run` 隔离 |
| `MergeRule` | `merge_rules` | 属性级合并策略：源优先级、归一化方式、忽略列标记 |
| `BuildRun` | `build_runs` | 构建批次：统计、四项不变量报告、输入指纹、对比基线 |
| `ConflictItem` | `conflict_items` | 跨源冲突候选、归一化裁决、人工覆盖留痕（自然键 `business_key + attribute_key`） |

每个实体都贯穿：表 → model → schema → service → controller → route → 前端 api → store → 页面/组件。

## 4. 两个真算算法（Python，前端只展示）

### 4.1 SCD2 拉链构建 `backend/src/algorithms/scd2.py`

1. 按业务键分组，逐日比较 golden 属性（多源同日按 `MergeRule` 优先级 + 归一化折叠为一条）。
2. 变更字段集合非空 → 关旧链（`valid_to = 观察日`）+ 开新链（`valid_from = 观察日 + 1`，夜间批次次日生效）。
3. 迟到快照：按**入库顺序**重放，发现 `snapshot_date` 早于已见最大日期即计入迟到，并按日期重排回插。
4. 人工覆盖：`effective_date = 冲突日 + 1` 追加 `version_source = manual` 的新版本。
5. 不变量校验：每键 `Σ is_current = 1`、区间不重叠、无空洞、`valid_from ≤ valid_to`。

基线数据（seed 可复现）：`180` 业务键 × `5` 天 = `900` 快照 → `210` 条链（180 首链 + 30 变更链），唯一 current `180/180` 通过；迟到回插 6 条；同日折叠 24 条；忽略列 `channel`。裁决 3 条冲突后重建 → `213` 条链（+3 人工/候选覆盖链）。

### 4.2 跨源冲突合并 `backend/src/algorithms/conflict_merge.py`

1. 按 `(business_key, snapshot_date)` 收集同键同日的多源候选。
2. 逐属性收集原始值；原始值相同不构成候选。
3. 归一化：手机号去分隔符/去 `+86`；机构编码映射（`ORG-BJ01`/`BJ01`/`华北一区` → `BJ01`）；姓名按声调无关拼音比对。
4. 归一后全等 → `normalized_equal` 自动收敛；否则相似度 ≥ `0.85` → `similar`（同音）自动收敛到高优先源；否则 → `conflict` 进入人工队列。
5. 人工裁决两种：候选中裁定（`candidate`）或人工覆盖（`manual`，可填候选外值），均记录来源、依据、裁决人、时间与生效日。

seed 产出 `24` 条冲突候选：14 条归一后一致（手机号 9 / 机构编码 5）、4 条姓名同音、6 条真实冲突（3 条等级 / 3 条机构）。

## 5. 六个页面

1. **登录**（编年史封面 + 三账号快捷填充）
2. **维度设计** `/dimensions`：合并规则台账（优先级上移/下移、归一化、忽略列），源系统登记、上游快照接入
3. **构建运行** `/builds`：批次编年、统计、快照时间轴、不变量校验报告、批次对比（新增链）
4. **当前维度** `/dims/current`：当前链台账、等级分布、编年提示、客户编年抽屉
5. **时点回溯** `/dims/as-of`：横向时间轴选日期、当时有效链、旧值验证、导出 CSV
6. **冲突裁决** `/conflicts`：待裁决/全部切换、候选来源对比、归一化裁决、人工覆盖留痕、校验报告

## 6. 快速启动

```bash
cp .env.example .env
docker compose up -d --build
# 前端 http://localhost:18245  后端 http://localhost:19245/docs  数据库 17745
```

启动时后端自动建表并执行幂等 seed（`SEED_DEMO=true`），容器内日志会打印：

```text
SEED_SUMMARY brand=scdchain sources=3 customers=180 snapshots=900 conflicts=24 runs=2 users=3
```

手动重跑 seed（幂等，两次输出逐字一致）：

```bash
docker compose exec backend python scripts/seed_demo.py
```

## 7. 本地开发

```bash
# backend
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
DB_HOST=127.0.0.1 DB_PORT=17745 uvicorn src.main:app --reload --port 19245

# frontend
cd frontend && npm install && npm run dev   # 开发时请把 /api 代理到 19245
```

## 8. 技术栈

| 层 | 选型 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite 5 + Pinia + vue-router 4 |
| 后端 | Python 3.11 + FastAPI 0.115 + SQLAlchemy 2.0 + Pydantic 2 |
| 异步 | Celery 5.4 + Redis 7（构建批次异步执行，worker 心跳健康检查） |
| 数据库 | PostgreSQL 16（JSONB 属性、`is_current` 部分唯一索引） |
| 部署 | Docker Compose，恰好 5 服务：frontend / backend / worker / db / redis |

## 9. 目录

```text
gb-572/
├── backend/
│   ├── src/{routes,controllers,services,models,schemas,middlewares,utils,constants,config}
│   ├── src/algorithms/{scd2.py,conflict_merge.py,normalization.py}   # 纯函数、可离线验证
│   ├── src/services/fixture.py                                      # 确定性演示数据
│   ├── scripts/seed_demo.py                                         # 幂等 seed
│   └── migrations/                                                  # DDL 快照 + 说明
├── worker/{Dockerfile,entrypoint.sh,healthy.py}
├── frontend/src/{api,stores,types,components/common,hooks,pages,router,utils,constants,styles}
├── docker-compose.yml
└── .env.example
```

## 10. 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `FRONTEND_PORT` / `BACKEND_PORT` / `DB_PORT` | 18245 / 19245 / 17745 | 端口映射 |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | scdchain_* | PostgreSQL 连接 |
| `JWT_SECRET` / `JWT_EXPIRE_HOURS` | dev 值 / 8 | JWT 签名与过期 |
| `SEED_DEMO` | true | 启动时执行 seed |
| `OVERRIDE_EFFECTIVE_DATE` | 2026-11-06 | 人工覆盖默认生效日 |
| `RATE_WINDOW_SECONDS` / `RATE_WINDOW_MAX` | 60 / 120 | 限流窗口 |

## 11. 共享枚举（前后端各一份）

| 枚举 | 后端位置 | 前端位置 |
|---|---|---|
| 角色 `admin/modeler/auditor` | `backend/src/constants/roles.py` | `frontend/src/constants/roles.ts` |
| 客户等级 `银卡/金卡/白金卡/钻石卡` | `backend/src/constants/customer_level.py` | `frontend/src/constants/customerLevel.ts` |
| 构建状态 `pending/running/succeeded/failed` | `backend/src/constants/build_status.py` | `frontend/src/constants/buildStatus.ts` |
| 冲突状态/裁决策略 | `backend/src/constants/conflict_status.py` | `frontend/src/constants/conflictStatus.ts` |
| 归一化策略 `direct/phone_digits/org_code_map/name_homophone` | `backend/src/constants/normalization.py` | `frontend/src/constants/conflictStatus.ts`（`NORMALIZATION_LABELS`） |

## 12. 视觉

年鉴 / 编年史时间轴风：暖灰纸底 + 深藏青目录侧栏 + 青铜色刻度与印章；双字体 **Libre Baskerville**（衬线标题/数字）+ **Public Sans**（正文）；`oklch()` 色板，无纯黑纯白；响应式 1280 / 860 / 768 三档。

## 13. 已知边界

- 演示数据固定为 180 业务键 × 5 天；真实客户维度规模需调整 `fixture.py` 与分页。
- 姓名同音使用内置轻量拼音表（覆盖演示用字），非常用字回退为原字符。
- 构建为全量重建模式（`mode=full`），增量会话级 merge 未实现。
- 更多细节见 `test-artifacts/gb-572/TESTING.md`。

## License

MIT (demo)。
