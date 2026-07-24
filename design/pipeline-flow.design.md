# 流水线架构设计

> 最后更新: 2026-05-26 | 状态: 生效中

---

## 一、架构概览（三层）

```
┌──────────────────────────────────────────────────────────┐
│                    调度层 (Orchestrator)                  │
│  run_pipeline.py → 编排step0→step1~26→final→sync       │
│  feedback.js    → 赛后反馈循环                          │
│  sync_notion.js → 数据同步层                            │
├──────────────────────────────────────────────────────────┤
│                    分析层 (Analytics)                     │
│  step0 ~ step26 → 顺序执行的数据提取+分析               │
│  final_report_generator.py  → .md报告                  │
│  pattern_matcher.py         → 模式匹配                  │
├──────────────────────────────────────────────────────────┤
│                    学习层 (Learning)                      │
│  feedback_learner.py     → 从反馈学习模式               │
│  pattern_miner.py        → 全量组合扫描+模式挖掘        │
│  weight_engine_v3.py     → 权重精细调整                 │
│  expert_pattern_engine.py → 专家经验匹配                │
└──────────────────────────────────────────────────────────┘
```

---

## 二、两条独立流水线

### 2.1 主流水线（预分析）

**触发时间**: 每日 ~11:00（cron）

**执行脚本**: `run_pipeline.py`

**数据流**:
```
step0_fetch_matches.py (1次/天)
  │
  ├─→ matches_data.json (当日比赛列表)
  │
  ├─→ 针对每场比赛并发执行:
  │     ├─ step146_extractor.py  (合作业: step1/4/6)
  │     ├─ step235_runner.py     (step2/3/5 同赔)
  │     ├─ step7_runner.py       (澳门同赔)
  │     ├─ step8_1923_extractor.py (step8+19-23)
  │     ├─ step918_extractor.py  (step9-18 主客队)
  │     ├─ step24_extractor.py   (盘路匹配)
  │     ├─ step25_zhuangjia.py   (庄家盈亏)
  │     └─ step26_profit_ratio.py (盈亏比例)
  │         ╰→ match/ 目录（含各group子目录）
  │
  ├─→ final_report_generator.py → .md报告
  ├─→ sync_notion.js → 写入Notion主库
  └─→ pattern_matcher.py → 模式匹配 → 写Notion备注
```

**输出**:
- `tasks/{日期}/周日00X_主队vs客队.md`（分析报告）
- Notion主库4字段更新（备注+竞彩预测+步26+让球预测）

### 2.2 反馈流水线（赛后分析）

**触发时间**: 每日 ~13:00（cron）

**执行脚本**: `feedback.js` → `feedback_learner.py`

**数据流**:
```
feedback.js
  1. 获取实际赛果 (zgzcw.com)
  2. 获取终盘赔率 (重跑step146)
  3. 对比竞彩预测vs实际 → 预测是否正确
  4. 对比让球预测vs实际 → 让球预测是否正确
  5. 更新Notion反馈字段
  6. 分组统计准确率
  7. 存档比分到 scores_archive.json
       │
       ▼
feedback_learner.py
  1. 读 feedback.json 提取比赛特征
  2. 生成一维~四维组合标签
  3. Wilson Score + Bayesian 计算置信度
  4. 输出 learned_patterns_v2.json
```

**输出**:
- Notion主库反馈字段更新
- `learnings/learned_patterns_v2.json`（供下次模式匹配使用）
- `learnings/feedback.json`（反馈数据库）

---

## 三、并发策略

### 3.1 并发原则

1. **批量优先**：多场比赛不顺序执行，**并发跑**
2. 不设中间确认点，全流程自动化（pipeline → sync → pattern matching一链到底）
3. 锁机制：使用 `.lock` 文件防并发触发

### 3.2 并发粒度

| 层级 | 并发方式 | 说明 |
|------|---------|------|
| 跨比赛 | 多进程并发 | 每场比赛一个独立进程 |
| 单比赛 | 顺序执行step | 同一比赛的step有数据依赖，不能并发 |
| 同赔查询 | 同步ajax | 同赔接口有速率限制，不宜并发 |

### 3.3 资源限制

- 超时: 3600s（每场比赛1小时）
- 重试: 失败自动重跑3次
- 锁: `.lock` 文件，存在时拒绝新流水线

---

## 四、数据存储结构

### 4.1 目录组织

```
jingcai/
├── tasks/{日期}/           ← 日结数据
│   ├── 周日00X_主队vs客队.md  ← 最终报告
│   ├── data/               ← 中间数据
│   │   └── match001_主队vs客队/
│   │       ├── meta.json
│   │       ├── group01_europe/   (step1-3)
│   │       ├── group02_handicap/ (step4-5)
│   │       ├── group03_asian/    (step6-8)
│   │       ├── group04_teamA/    (step9-13)
│   │       ├── group05_teamB/    (step14-18)
│   │       ├── group06_baijia/   (step19-23)
│   │       ├── step24_*.json
│   │       ├── step25_*.json
│   │       └── step26_*.json
│   └── logs/               ← 日志
│
├── learnings/              ← 跨日持久数据
│   ├── feedback.json
│   ├── learned_patterns_v2.json
│   ├── scores_archive.json
│   ├── expert_patterns.md
│   └── full_combo_scan_results/
│
├── data/jingcai/           ← 其他持久数据
│   ├── league_map.json
│   ├── league_name_map.json
│   └── leagues_all.json
│
├── scripts/                ← 辅助工具
│   ├── memory_integration.py
│   └── win_bridge.py
│
├── specs/                  ← 需求规格
├── design/                 ← 架构设计
└── src/                    ← (待迁移) 核心脚本
```

### 4.2 比赛数据目录结构

```
match001_主队vs客队/
├── meta.json              ← 比赛元数据
├── group01_europe/        ← 步骤1-3: 欧赔基础+同赔
│   ├── step1_europe_base.txt/md
│   ├── step2_jingcai_same.md
│   └── step3_interwetten_same.md
├── group02_handicap/      ← 步骤4-5: 让球
│   ├── step4_handicap_base.txt
│   └── step5_handicap_same.txt
├── group03_asian/         ← 步骤6-8: 亚盘
│   ├── step6_asian_base.txt
│   ├── step7_macau_same.md
│   └── step8_league_asian.txt
├── group04_teamA/         ← 步骤9-13: 主队
├── group05_teamB/         ← 步骤14-18: 客队
├── group06_baijia/        ← 步骤19-23: 百家
│   ├── step19_baijia.txt
│   ├── step20_baijia_stats.txt
│   ├── step21_odds_range.txt
│   ├── step22_baijia_changes.txt
│   └── step23_baijia_kelly.txt
├── step24_panlu_match.json
├── step25_zhuangjia.json
└── step26_profit_ratio.json
```

---

## 五、错误处理设计

### 5.1 三层防御

| 层级 | 机制 | 产出 |
|------|------|------|
| 第一层 | 每一步执行后检查退出码 | 非0退出立即标记 |
| 第二层 | 数据质量验证（报告大小、来源数、场次） | 空洞等同失败 |
| 第三层 | 内置反驳机制（搜索不到不AI编造） | ⚠️标记+来源说明 |

### 5.2 失败处理原则

1. **失败必须出声** — 所有异常必须显式标记，不允许静默通过
2. 根因修复原则 — 发现补丁类修复应追到根因
3. 每步输出验证 — 写入Notion后读回来确认字段是否正确

---

## 六、技术栈

| 组件 | 技术 | 平台 |
|------|------|------|
| 数据获取 | Python + requests + BeautifulSoup | WSL/Windows |
| 同赔查询 | Node.js + axios（部分ajax） | Windows Node |
| 报告生成 | Python | WSL |
| Notion同步 | Node.js（直接https） | Windows Node |
| 日志 | Python `_log_util.py` | 统一格式 |
| 调度 | cron（agent+terminal模式） | Hermes |

**跨平台桥接**:
- WSL Python → Windows Python → Windows Node.js
- 原因：WSL内Node.js通过stdio读写Windows文件系统时报EISDIR错误

---

## 七、变更记录

| 日期 | 变更内容 | 原因 |
|------|---------|------|
| 2026-05-17 | step7从agent-browser重构为ajax | 移除浏览器依赖，正确率提升 |
| 2026-05 | 增加post-sync verify | 发现字段空值无法自动溯源 |
