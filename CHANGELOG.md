# 竞彩预测引擎 CHANGELOG

> 记录预测算法、分析流程的每次迭代和关键变更。
> 每次修改预测逻辑、新增/删除步骤、变更数据来源、优化准确率时，在此记录。

---

## V2.2 — 2026-05-18 架构优化与清理

### 新增
- **`_util.py` 工具模块**：统一 rd()、re_find()、ensure_utf8_stdout()、safe_json_load()，3个核心文件切换
- **`_league_util.py` 联赛工具模块**：统一 `_league_match()` + `LEAGUE_ID_MAP`，3个文件统一调用，10个测试用例通过
- **`_log_util.js` JS 日志模块**：feedback.js / sync_notion.js 接入，日志写入 `tasks/{日期}/logs/`
- **`conclusion_signals.py` 信号分离**：从 `final_conclusion_generator.py` (1511行) 拆分出信号提取函数（499行），主文件压缩到1038行
- **`_cleanup.py` 定时清理**：清理30天前的中间数据（只保留最终报告 .md + 比分存档），支持 --dry-run / --days 参数

### 改进
- **`except: pass` 加日志**：43处静默异常改为 `log.warn()`，覆盖全部核心 step 脚本
- **联赛映射统一**：`step235_runner.py` / `step8_1923_extractor.py` / `step918_extractor.py` 共享 `_league_util._league_match()`
- **编码修复统一**：`ensure_utf8_stdout()` 从各文件头部抽取到 `_util.py`
- **变量名修复**：`final_conclusion_generator.py` 中修复 `for log in adjust_log` 覆盖全局 logger 的 bug

### 清理
- **删除 220 个 `check_*.py` 调试脚本**：所有一次性脚本已清空
- 删除临时调试文件：`_analyze_funcs.py`、`_fix_split.py`、`_test_split.py`、`_fix_except_pass.py`、`_find_league_match.js`

### 涉及的脚本
`_util.py`, `_league_util.py`, `_log_util.js`, `conclusion_signals.py`, `final_conclusion_generator.py`, `final_report_generator.py`, `feedback_learner.py`, `step235_runner.py`, `step8_1923_extractor.py`, `step918_extractor.py`, `feedback.js`, `sync_notion.js`, `step146_extractor.py`, `step7_runner.py`, `_cleanup.py`

---

## V2.1 — 2026-05-17 流水线重构

### 变更
- **step7 数据源替换**：agent-browser（无障碍树JS渲染）→ ajax接口 `yazhi_sameajax.php`
  - 原因：agent-browser 解析盘口值有bug，历史数据初盘显示错误（`一球 0.950/0.890` vs 本场 `半球/一球 0.770/1.010`）
  - 结果：12场（全盘口匹配高）vs 原来的5场（盘口错配低），速度 3-5s vs 10+秒
- **澳门初盘提取**：BeautifulSoup → 正则表达式 `extract_macau_odds()`
  - 原因：BS 解析 170KB yazhi 页面耗时太长
- **移除所有 agent-browser 依赖**：确认其他 step 已用 ajax/requests，agent-browser 仅 step7 使用
- **统一日志系统**：所有核心脚本（14个）接入 `_log_util.py`
  - 日志位置：`tasks/{日期}/logs/{步骤名}.log`
  - 格式：`[时间] [步骤] 级别 信息`

### 清理
- 删除废弃脚本：`final_conclusion_generator_v2.py`、`final_two.py`、`step2357_runner.py`
- 删除临时诊断脚本：`final_audit.js`、`final_full_audit.js`、`step1_explore.py`、`step0_fetch_matches_enhanced.py`
- 删除调试中间文件：`step8_analysis.txt`、`step8_debug.txt`、`step19_sample.txt`、`step7_snapshot.json`

### 涉及的脚本
`step7_runner.py`, `_log_util.py`, 所有 `step*.py`, `final_*.py`, `run_pipeline.py`

---

## V2.0 — 2026-05-09 组合模式学习 + Step25/26 集成

### 新增
- **反馈学习引擎 V2**（`feedback_learner.py`）：从 `feedback.json` 提取组合特征（欧赔趋势×让球趋势×亚盘趋势×百家趋势×盘路匹配）
- **Step25 庄家盈亏**（`step25_zhuangjia.py`）：从 500.com 投注页面抓取投注占比和庄家盈亏数据
- **Step26 盈亏比例**（`step26_profit_ratio.py`）：计算各方向的盈利占比
- **全量组合扫描器 V3**（`full_combo_scanner.py`）：扫描精细维度组合，生成 `learned_patterns_v2.json`
- **权重调整引擎 V3**（`weight_engine_v3.py`）：Wilson Score + Bayesian Average 精确调整组合权重
- **专家模式库**（`learnings/expert_patterns.md`）：基于实战经验总结的盘口变化规律

### 预测逻辑增强
- `final_conclusion_generator.py` 新增：
  - 投注占比方向分析（step25 数据）
  - 胜平负几率计算
  - 欧赔盘路组合匹配（≥2个欧赔盘路一致时加权）
  - 历史模式学习修正（从 `learned_patterns_v2.json` 和 `feedback.json` 加载）
  - 联赛准确率、盘路匹配度、高准确率组合标签 → 动态修正信心度

### 数据基础
- `learned_patterns_v2.json`：235场比赛、28个日期、1185个组合标签
- 支持维度：联赛(19)、投注占比(18)、澳门亚盘(12)、竞彩盘路(12)、百家盘路(12)、IW盘路(11)、庄家盈亏(7)、澳门同赔(6)、欧赔(3)、让球(3)、亚盘(3)

### 涉及的脚本
`feedback_learner.py`, `step25_zhuangjia.py`, `step26_profit_ratio.py`, `full_combo_scanner.py`, `weight_engine_v3.py`, `final_conclusion_generator.py`, `final_report_generator.py`

---

## V1.6 — 2026-05-05 联赛名模糊匹配修复

### 变更
- 修复联赛名精确匹配问题：竞彩"韩职"在500.com叫"K1联赛"
- `_league_match()` 模糊匹配函数统一集成到：`step235_runner.py`、`step8_1923_extractor.py`、`step918_extractor.py`
- 映射表覆盖30+联赛（韩职↔K1联赛、日职↔J1联赛等）

### 诊断工具
- 新增 `diagnose.py`：快速模式（只读报告文本）和详细模式（访问源站验证），区分"脚本bug"vs"确实没数据"
- 已集成到流水线末尾，每次跑完自动诊断

### 涉及的脚本
`step235_runner.py`, `step8_1923_extractor.py`, `step918_extractor.py`, `diagnose.py`, `run_pipeline.py`

---

## V1.5 — 2026-05-03 流水线打通 + Notion 同步

### 新增
- **`sync_notion.js`**：24字段完整同步到 Notion 数据库（Database ID: `35491ad7-17ba-81cc-aa04-ce53f7234e17`）
- **`feedback.js`**：反馈闭环，获取实际比分对比预测，更新 Notion（`预测正确` / `让球预测正确` 字段）
- **`version.py`**：版本管理工具（init/list/diff/restore/status）

### 修复
- `run_pipeline.py` 的 `run_script` 函数重复代码导致启动报错
- 删除残留 .lock 文件
- 完整跑通：30场比赛全部完成24步 + 第25步庄家盈亏

### 涉及的脚本
`run_pipeline.py`, `sync_notion.js`, `feedback.js`, `version.py`

---

## V1.0 — 2026-04-29 24步分析框架建立

### 初始版本
- **24步完整分析流程**：
  - 第一组：欧盘（1-3步）— 欧赔基础 → 竞彩同赔 → Interwetten同赔
  - 第二组：让球（4-5步）— 让球基础 → 让球同赔
  - 第三组：亚盘+历史（6-8步）— 亚盘基础 → 澳门同赔 → 历史亚盘统计
  - 第四组：主队分析（9-13步）
  - 第五组：客队分析（14-18步）
  - 第六组：百家对比（19-23步）
  - 第24步：盘路完全匹配汇总
- **数据源**：trade.500.com（主站）+ live.500.com（备选）
- **竞彩同赔**：调竞彩官网ajax接口获取相同赔率历史
- **澳门同赔**：agent-browser 渲染JS（yazhi_same.php）
- **Interwetten / 让球同赔**：欧赔ajax接口 `ouzhi_sameajax.php`
- **最终报告**：`final_report_generator.py` 生成 `.md` 报告

### 预测结论规则
- 基于6组欧赔盘路一致数量决定方向
- 5家欧赔和百家对比综合判断
- 信心等级划分（高/中/低）

### 涉及的脚本
`step0_fetch_matches.py`, `step146_extractor.py`, `step235_runner.py`, `step7_runner.py` (agent-browser版), `step8_1923_extractor.py`, `step918_extractor.py`, `step24_extractor.py`, `final_report_generator.py`, `final_conclusion_generator.py`, `run_pipeline.py`

---

## V0.1 — 2026-04-22 原型

### 初始探索
- 概念验证：手动获取少数比赛数据
- 确认500.com数据可用性
- 建立竞彩赔率概念框架（即时盘 vs 终盘）
- 确立目录结构规范（`tasks/{日期}/data/{比赛}`）
