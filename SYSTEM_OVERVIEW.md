# 竞彩分析系统 — 完整工作流总览

> 最后更新: 2026-05-17 | 共 22 个核心文件，约 13,000+ 行代码

---

## 一、整体架构（三层）

```
┌────────────────────────────────────────────────┐
│  第三层：调度层                                  │
│  run_pipeline.py  →  orchestrates all steps     │
│  feedback.js      → 赛后反馈 + Notion更新       │
│  sync_notion.js   → Notion数据库同步            │
├────────────────────────────────────────────────┤
│  第二层：分析层（24步分析引擎）                    │
│  step0 ~ step26  → 顺序执行的数据提取+分析       │
│  final_*.py      → 结论生成 + 报告生成          │
├────────────────────────────────────────────────┤
│  第一层：学习层                                  │
│  feedback_learner.py      → 从反馈学到模式       │
│  full_combo_scanner.py   → 全量组合扫描          │
│  weight_engine_v3.py     → 权重精细调整          │
│  expert_pattern_engine.py → 专家经验匹配引擎     │
└────────────────────────────────────────────────┘
```

---

## 二、核心文件功能详解

### 🔹 0. 调度层

#### `run_pipeline.py` (594 行, 12 函数) — 🔑 最关键
**入口和作用**：
- 每天 11:00 cron 触发或手动运行
- 编排整个流：step0 → step1~26（按比赛逐一执行）→ final_report → feedback_learner → diagnose
- 使用 `.lock` 文件防并发
- 带重试机制（失败自动重跑3次）
- 调用子进程：7 处（subprocess.run 执行各 step 脚本）
- 超时：3600s（1 小时）
- **调用方式**：`python run_pipeline.py` 或 `python run_pipeline.py 2026-05-17`

**数据流**：
```
run_pipeline.py
  │
  ├─→ step0_fetch_matches.py (1次/天)           ─→ matches_data.json
  │
  ├─→ 对每场比赛逐一执行:
  │     ├─→ step146_extractor.py (合作业)      ─→ group01_europe/step1
  │     │                                        group02_handicap/step4
  │     │                                        group03_asian/step6
  │     ├─→ step235_runner.py                   ─→ step2/3/5 同赔分析
  │     ├─→ step7_runner.py                     ─→ step7 澳门同赔
  │     ├─→ step8_1923_extractor.py            ─→ step8+19-23
  │     ├─→ step918_extractor.py              ─→ step9-18 (主客队)
  │     ├─→ step24_extractor.py               ─→ 盘路匹配汇总
  │     ├─→ step25_zhuangjia.py               ─→ 庄家盈亏
  │     └─→ step26_profit_ratio.py            ─→ 盈亏比例
  │                                           ╰→ match 目录完成
  │
  ├─→ final_stats.py                           ─→ 统计摘要
  ├─→ final_report_generator.py (调conclusion)  ─→ .md 报告
  ├─→ sync_notion.js (调子进程)                ─→ → Notion DB
  └─→ feedback_learner.py                     ─→ trained_patterns_v2
```

---

### 🔹 1. 数据获取层

#### `step0_fetch_matches.py` (301 行, 5 函数)
**作用**：获取当日竞彩比赛列表
- 主数据源：trade.500.com（HTML 解析）
- 备选：live.500.com
- 输出：`matches_data.json` + `meta.json`（每场比赛一个）
- 含多数据源 fallback

#### `step146_extractor.py` (359 行, 1 函数)
**作用**：一次运行完成 step1/step4/step6 三个基础数据步骤
- **step1（欧赔基础）**：提取竞彩/Interwetten/百家 3家初盘+即时赔率
- **step4（让球基础）**：提取让球指数初盘+即时
- **step6（亚盘基础）**：提取澳门/易胜博/韦德 3家亚盘
- 数据源：trade.500.com 欧赔/亚盘页面
- 为什么合并：3步共享同一次页面请求，减少网络开销

---

### 🔹 2. 同赔分析层

#### `step235_runner.py` (354 行, 10 函数)
**作用**：step2/step3/step5 三个同赔历史分析
- **step2（竞彩同赔）**：调竞彩官网 ajax 接口，查相同赔率的往期比赛
- **step3（IW同赔）**：调 500.com `ouzhi_sameajax.php`，查相同 Interwetten 赔率的历史
- **step5（让球同赔）**：调让球同赔 ajax，查相同让球指数的历史
- **V2 升级**：统计分"相同联赛"和"所有赛事"两个维度
- 输出：`step2_jingcai_same.md` / `step3_interwetten_same.md` / `step5_handicap_same.txt`

#### `step7_runner.py` (301 行, 5 函数)
**作用**：澳门亚盘同赔历史统计
- 2026-05-17 **从 agent-browser 重构为 ajax**（`yazhi_sameajax.php`）后，彻底移除浏览器依赖
- 输出：`step7_macau_same.md`
- 关键改进：ajax 直接获取盘口值，正确率从 5 场提升到 12 场

#### `step8_1923_extractor.py` (952 行, 12 函数) 🏋️ 最复杂的 extractor
**作用**：step8 + step19~23 的批量提取
- **step8**：同联赛亚盘统计（本场 + 同联赛的历史比赛）
- **step19**：百家欧赔对比表（提取 20+ 家公司的初盘/即时赔率）
- **step20**：百家胜平负区间统计
- **step21**：赔率组合区间
- **step22**：百家时间段变化
- **step23**：百家凯利指数
- 数据源：500.com 亚盘页面 + 欧赔页面

#### `step918_extractor.py` (612 行, 15 函数) 
**作用**：step9~18 的主客队分析
- 调 500.com 的 `teams_oddschange.php` 接口获取球队历史比赛
- 按联赛/主客场筛选，按亚盘盘口匹配过滤
- **15 个函数** = `fetch_team()` + `filter1/2/3/4()` + 联赛名映射 + 日志等
- 输出：`step9_home_history.txt` ~ `step18_away_all.txt`

---

### 🔹 3. 汇总结论层

#### `step24_extractor.py` (717 行, 9 函数)
**作用**：盘路完全匹配汇总
- 读前面各 step 的输出，进行盘路方向匹配
- 统计各维度方向一致情况（均势/单向/一致）
- 生成盘路匹配度评分
- 输出：`step24_panlu_match.json`

#### `step25_zhuangjia.py` (232 行, 4 函数)
**作用**：庄家盈亏分析
- 从 500.com 投注页面提取投注占比 + 庄家盈亏
- 计算各方向（主胜/平局/客胜）的庄家赢/亏
- 判断大热方
- 输出：`step25_zhuangjia.json`

#### `step26_profit_ratio.py` (290 行, 5 函数)
**作用**：盈亏比例计算
- 从投注数据计算各方向盈利率（profit ratio）
- 判断庄家最看好方向
- 输出：`step26_profit_ratio.json`

#### `final_conclusion_generator.py` (1517 行, 15 函数) 🔑 最核心
**作用**：生成每场比赛的预测结论
- 读所有 step 的输出文件
- 10 维度加权评分（欧赔/竞彩同赔/IW同赔/澳门亚盘/让球/主队/客队/百家/庄家/盘路）
- **3 层学习修正**：组合模式(Wilson+Baysian) → 联赛准确率 → 专家模式
- 输出：竞彩预测 + 让球预测 + 信心度 + 各维度详解
- 被 `final_report_generator.py` 通过 subprocess 调用

#### `final_report_generator.py` (463 行, 3 函数)
**作用**：生成 `.md` 格式的完整分析报告
- 调用 `final_conclusion_generator.py`（subprocess）
- 按 RULES.md 格式输出：比赛信息 → 各 step 数据 → 最终结论表格
- 输出：`tasks/{日期}/周X00X_主队vs客队.md`

#### `final_stats.py` (133 行, 1 函数)
**作用**：生成当天比赛的统计摘要
- 统计各预测分布（主胜/平局/客胜）
- 生成简要汇总

---

### 🔹 4. 反馈与同步层

#### `feedback.js` (1144 行, 13 函数) 🔑 赛后核心
**作用**：比赛结束后获取实际赛果，对比预测
- 获取源站赛果（zgzcw.com / trade.500.com）
- 获取终盘赔率（重新运行 step146 获取关闭后的即时值）
- 对比竞彩预测 vs 实际 → `预测正确`
- 对比让球预测 vs 让球后结果 → `让球预测正确`
- 更新 Notion：实际比分/结果/是否正确/反馈总结/终盘赔率
- 生成分组统计（竞彩+庄家+让球组合的准确率）
- **比分存档**：写入 `data/jingcai/scores_archive.json`
- 调用子进程 4 处（step146 重新提取）

#### `sync_notion.js` (1216 行, 28 函数) 🔑 Notion 适配器
**作用**：将流水线生成的比赛数据同步到 Notion 数据库
- 28 个函数的庞大适配器（处理各种字段类型的读写）
- 支持参数：日期/比赛编号/联赛筛选
- 支持增量更新、重跑检测
- 数据库：`35491ad7-17ba-81cc-aa04-ce53f7234e17`（24字段）

#### `sync_summary.js` (286 行, 12 函数)
**作用**：更新 Notion 中的汇总统计
- 读 `learned_patterns_v2.json` 生成准确率汇总
- 按联赛/信心等级分组统计

---

### 🔹 5. 学习层

#### `feedback_learner.py` (1162 行, 6 函数) 🔑 学习核心
**作用**：从历史反馈中学习预测模式
- 从反馈数据提取比赛特征（10个维度+精细数据）
- 自动生成一维→四维组合标签
- 统计每个组合的准确率（Wilson + Bayesian）
- 输出：`learned_patterns_v2.json`

#### `full_combo_scanner.py` (306 行, 2 函数)
**作用**：全量组合扫描器 V3
- 扫描所有可用维度（联赛/亚盘/盘路/庄家/投注占比等）
- 枚举所有维度组合，计算准确率
- 输入：`feedback.json` 中的 combos 数据

#### `weight_engine_v3.py` (541 行, 10 函数)
**作用**：权重调整引擎
- 使用 Wilson Score + Bayesian Average 计算组合置信度
- 精细调整各维度权重
- 替代简单平均数

#### `expert_pattern_engine.py` (471 行, 11 函数)
**作用**：专家盘路模式引擎 V4
- 从 `expert_patterns.md` 加载人工编写经验规则
- 按联赛/赔率/盘口/变化方向四维匹配
- 返回匹配因子（0.0~1.0）供权重调整

---

### 🔹 6. 诊断与工具层

#### `diagnose.py` (531 行, 4 函数)
**作用**：竞彩数据核对+自动修复
- 快速模式：只读报告文本，不访问源站
- 完整模式：访问源站验证，区分"脚本bug"vs"确实没数据"
- `--fix` 参数自动重跑问题比赛

#### `_log_util.py` (41 行, 1 函数)
**作用**：统一日志模块
- 输出格式：`[时间] [步骤名] 级别 信息`
- 日志位置：`tasks/{日期}/logs/{脚本名}.log`

---

## 三、数据流全景图

```
                         ┌───────────────────┐
                         │   trade.500.com   │
                         │   zgzcw.com       │
                         │   sporttery.cn    │
                         └────────┬──────────┘
                                  │ HTTP
                                  ▼
 ┌─────────────────────────────────────────────────────────┐
 │                       run_pipeline.py                    │
 │  day 11:00 (cron)                                        │
 │                                                          │
 │  step0 ─→ matches_data.json                              │
 │                                                          │
 │  ┌─────── 每场比赛 ───────┐                              │
 │  │ step146 ─→ 欧赔/让球/亚盘  │                           │
 │  │ step235 ─→ 竞彩/IW/让球同赔 │                          │
 │  │ step7   ─→ 澳门同赔       │                           │
 │  │ step8   ─→ 同联赛亚盘统计  │                           │
 │  │ step918 ─→ 主客队历史     │                           │
 │  │ step19~23→ 百家对比       │                           │
 │  │ step24  ─→ 盘路匹配汇总    │                           │
 │  │ step25  ─→ 庄家盈亏       │                           │
 │  │ step26  ─→ 盈亏比例       │                           │
 │  └───────────────────────────┘                           │
 │                                                          │
 │  final_report_generator                                   │
 │    └→ final_conclusion_generator (15函数)                │
 │        ├ 10维度加权评分                                    │
 │        ├ 3层学习修正                                      │
 │        ├ 信心度计算                                        │
 │        └ .md 报告                                          │
 │                                                          │
 │  sync_notion.js ─→ Notion DB                             │
 │  feedback_learner ─→ learned_patterns_v2.json            │
 └─────────────────────────────────────────────────────────┘
                                  │
                                  ▼
 ┌─────────────────────────────────────────────────────────┐
 │                     feedback.js                          │
 │  day ~12:01 (cron)                                       │
 │                                                          │
 │  1. 获取实际赛果 (zgzcw.com)                              │
 │  2. 获取终盘赔率 (重跑step146)                            │
 │  3. 对比竞彩预测 vs 实际 → 预测正确                        │
 │  4. 对比让球预测 vs 让球后 → 让球预测正确                   │
 │  5. 更新 Notion (比分/结果/终盘/反馈总结)                  │
 │  6. 分组统计 (竞彩+庄家+让球分组准确率)                    │
 │  7. 存档比分到 scores_archive.json                        │
 └─────────────────────────────────────────────────────────┘
                                  │
                                  ▼
 ┌─────────────────────────────────────────────────────────┐
 │                   feedback_learner.py                    │
 │  手动或流水线末尾自动触发                                  │
 │                                                          │
 │  1. 读 feedback.json 提取所有比赛特征                      │
 │  2. 生成一维~四维组合标签                                  │
 │  3. 统计各组合准确率                                       │
 │  4. Wilson Score + Bayesian 计算置信度                    │
 │  5. 输出 learned_patterns_v2.json                        │
 └─────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    下次 run_pipeline 时读取
                    learned_patterns_v2.json → 3层修正
                    ← 学习闭环完成 ←
```

---

## 四、数据存储结构

```
jingcai/
├── tasks/{日期}/                     ← 日结
│   ├── 周日001_主队vs客队.md         ← 最终报告
│   ├── matches_data.json             ← 当日比赛列表
│   │
│   ├── data/
│   │   ├── match1_主队__客队/
│   │   │   ├── meta.json              ← 比赛元数据 (league/home/away/fid/macau_line)
│   │   │   ├── group01_europe/        ← 欧赔(step1-3)
│   │   │   ├── group02_handicap/      ← 让球(step4-5)
│   │   │   ├── group03_asian/         ← 亚盘(step6-8)
│   │   │   ├── group04_teamA/         ← 主队(step9-13)
│   │   │   ├── group05_teamB/         ← 客队(step14-18)
│   │   │   ├── group06_baijia/        ← 百家(step19-23)
│   │   │   ├── step24_panlu_match.json
│   │   │   ├── step25_zhuangjia.json
│   │   │   └── step26_profit_ratio.json
│   │   └── match2_.../
│   │
│   └── logs/                          ← 日志（统一格式）
│       ├── step0.log
│       ├── step146.log
│       └── ...
│
├── learnings/                         ← 跨日持久数据
│   ├── feedback.json                   ← 反馈数据库
│   ├── learned_patterns_v2.json        ← 学习产出
│   ├── scores_archive.json             ← 比分存档
│   ├── scores_history.json
│   ├── expert_patterns.md              ← 专家模式库
│   ├── full_combo_scan_results/        ← 组合扫描结果
│   └── ...
│
├── data/jingcai/                       ← 其他持久数据
│   ├── scores_archive.json             ← 比分快照（新加）
│   ├── league_map.json
│   └── ...
│
└── *.py / *.js                         ← 核心脚本（22个在根目录）
```

---

## 五、优化空间评估

### 5.1 当前存在的问题

| 问题 | 严重程度 | 说明 |
|------|---------|------|
| `final_conclusion_generator.py` 1517 行 | ⚠️ 高 | 一个文件承担了结论生成 + 学习修正，耦合太紧 |
| 调试脚本堆积 (`check_*.py`) | ⚠️ 中 | 大量一次性调试脚本没清理（当前 40+ 个） |
| JS 无统一日志 | ⚠️ 中 | `feedback.js` `sync_notion.js` 还没接入日志模块 |
| 没有单元测试 | ⚠️ 中 | 各 step 改了依赖没法验证完整性 |
| 联赛映射分散 | ⚠️ 低 | `_league_match()` 在 3 个脚本里各有一份 |
| `step8_1923_extractor.py` 952 行 | ⚠️ 低 | 大文件，但 step8 和 step19-23 确实共享逻辑 |
| 没有自动重跑昨日的机制 | ✅ 已解决 | 刚加了 `scores_archive.json` 存档 |

### 5.2 建议优化方向

**🔴 高优先级：**
1. **拆分 `final_conclusion_generator.py`** — 把学习修正逻辑分离出来
2. **清理调试脚本** — `check_*.py` 40+ 个文件没清理

**🟡 中优先级：**
3. **JS 日志统一** — `feedback.js` / `sync_notion.js` 接入 `_log_util.py` 风格
4. **单元测试** — 每个 step 的输入输出验证
5. **重复代码抽象** — `rd()` / 编码修复 / 文件查找路径 散落各处

**🟢 低优先级：**
6. **联赛映射表统一** — 抽成独立模块
7. **定时 cleanup** — 自动清理 15 天前的中间数据（只保留报告+比分存档）
8. **错误处理升级** — 目前很多 step 用 `try/except: pass`，失败静默吞掉
