# 竞彩流水线 - 脚本对照表

> 全部脚本清单 + 每步用哪个 + 调用方式 + 注意事项
> 路径: ~/.openclaw/workspace/jingcai/

---

## 一、核心流水线（入口）

| 脚本 | 用途 | 调用方式 |
|------|------|---------|
| `run_pipeline.py` | **主入口**，调度全部流程 | `python3 run_pipeline.py` (跑今天) |
| | | `python3 run_pipeline.py all` (跑今天完整流水线) |
| | | `python3 run_pipeline.py 2026-05-23` (指定日期) |
| | | `python3 run_pipeline.py 001` (指定场次) |
| | | `python3 run_pipeline.py -p` (并行模式，3 worker) |
| **依赖**: VM Python 3.6 | **动作**: 预缓存→并发跑每场→step25→再生报告→验证→诊断→学习→Notion同步→反馈 |
| **⚠️ 尾部 3 步有兼容问题**（见下文第五节） |

---

## 二、每场比赛的步骤 → 对应脚本

### 0. 比赛列表获取

| 步骤 | 脚本 | 输出 |
|------|------|------|
| step0 获取比赛列表 | `step0_fetch_matches.py` | `tasks/{date}/matches_data.json` |

### 1-6. 赔率基础数据

| 步骤 | 脚本 | 说明 |
|------|------|------|
| step1 欧盘基础 | `step146_extractor.py` | 步骤1+4+6合并执行 |
| step2 竞彩同赔 | `step235_runner.py` | 步骤2+3+5合并执行 |
| step3 Interwetten同赔 | `step235_runner.py` | 同上 |
| step4 让球基础 | `step146_extractor.py` | 步骤1+4+6合并 |
| step5 让球同赔 | `step235_runner.py` | 同上 |
| step6 亚盘基础 | `step146_extractor.py` | 步骤1+4+6合并 |
| step7 澳门亚盘同赔 | `step7_runner.py` | 单独脚本 |

### 8-24. 深度分析

| 步骤 | 脚本 | 说明 |
|------|------|------|
| step8 同联赛亚盘统计 | `step8_1923_extractor.py` | 步骤8+19-23合并 |
| step9-13 主队历史 | `step918_extractor.py` | 步骤9-18合并 |
| step14-18 客队历史 | `step918_extractor.py` | 同上 |
| step19-23 百家对比 | `step8_1923_extractor.py` | 同上 |
| step24 盘路匹配汇总 | `step24_extractor.py` | 单独脚本 |

### 25-26. 庄家盈亏

| 步骤 | 脚本 | 说明 |
|------|------|------|
| step25 庄家盈亏 | `step25_zhuangjia.py` | 先单场 `--match-dir`，再全量 `--all` |
| step26 盈亏占比 | `step25_zhuangjia.py` | 加 `--all` 参数时一起生成 |

### 报告生成

| 步骤 | 脚本 | 说明 |
|------|------|------|
| 最终报告 | `final_report_generator.py` | **唯一活跃的报告脚本**，写 .md |
| (旧) 结论JSON | `final_conclusion_generator.py` | ⚠️ 已合并到报告生成器，不再单独调用 |
| 报告格式 | `conclusion_signals.py` | 信号提取函数（被报告生成器import） |
| 报告格式 | `weight_engine_v3.py` | Wilson Score + Bayesian 权重引擎（被import） |
| 报告格式 | `expert_pattern_engine.py` | 专家盘路模式引擎 V4（被import） |

---

## 三、预缓存/辅助脚本

| 脚本 | 用途 | 调用方式 | 说明 |
|------|------|---------|------|
| `precache_leagues.py` | 联赛历史数据预缓存 | `python3 precache_leagues.py 2026-05-23` | pipeline自动调用 |
| | 补充缓存 | `python3 precache_leagues.py --enrich 19200` | 手动的单个联赛补充 |
| `_league_util.py` | 联赛ID映射（49个联赛） | 被 precache_leagues.py 引用 | 从静态文件读取 |
| `_verify_util.py` | 逐步骤数据质量核查 | 被 run_pipeline.py import | 检查10个步骤的输出内容 |
| `_notion_verify.js` | Notion上传前后字段核查 | 被 sync_notion.js import | 区分空字符串/null/0占位符 |
| `diagnose.py` | 数据完整性诊断 | pipeline自动调用 | ⚠️ 需要 Windows Python |
| `feedback_learner.py` | 反馈学习引擎 V2 | pipeline自动调用 | 分析历史准确率+组合模式 |
| `protect.py` | 工作区保护（锁定/解锁） | `python3 protect.py lock/unlock` | 防止多session冲突 |
| `_util.py` | 共享工具函数 | 被各脚本 import | utf-8编码保证 |
| `_log_util.py` | 日志工具（Python版） | 被 Python 脚本import | |
| `_log_util.js` | 日志工具（JS版） | 被 JS 脚本 require | 需要 Node.js |

---

## 四、Notion 同步/反馈

| 脚本 | 用途 | 调用方式 | 运行环境 |
|------|------|---------|---------|
| `sync_notion_wrapper.py` | **同步入口** | `python3 sync_notion_wrapper.py add 2026-05-23` | ✅ VM Python 3.6 |
| | 内部机制 | → 写临时.py → Windows Python 3.14 → Windows Node.js |
| `sync_notion.js` | Notion 核心同步 | 内部被 wrapper 调用 | Node.js (Windows) |
| `sync_summary.js` | 汇总表同步 | `node sync_summary.js 2026-05-23` | Node.js (Windows) |
| `_notion_verify.js` | 上传前/后核查 | 被 sync_notion.js import | Node.js (Windows) |
| `notion_schema.js` | Notion 库结构定义 | 被其他JS引用 | Node.js (Windows) |
| `feedback.js` | 获取赛果+更新反馈 | `node feedback.js 2026-05-23` | Node.js (Windows) ✅ 已修复 |

### 同步流程图示
```
run_pipeline.py
  └─ sync_notion_wrapper.py (VM Python 3.6)  ← pipeline入口
       └─ 写临时脚本 ___tmp_sync.py
            └─ Windows Python 3.14
                 └─ Windows Node.js (sync_notion.js)
                      ├─ _log_util.js
                      ├─ _notion_verify.js
                      └─ notion_schema.js
```

---

## 五、⚠️ 已知兼容性问题

### A. VM Python 3.6 兼容（WSL Ubuntu 18.04）

`python3` = /usr/bin/python3 3.6.5。以下语法/库不支持：

| 问题 | 替代方案 |
|------|---------|
| `capture_output=True` (3.7+) | 用 `stdout=PIPE, stderr=PIPE` |
| `text=True` (3.7+) | 用 `universal_newlines=True` |
| `encoding='utf-8'` in subprocess (3.6无效) | 加 `universal_newlines=True` |
| `bs4` / `pandas` 等库 | 不存在，需要 `C:\Python314\python.exe` 调用 |

### B. Windows Node.js EISDIR

Windows Node (`/mnt/c/Program Files/nodejs/node.exe`) 在 WSL 里直接调有 stdio 兼容问题。
**不能**直接在 pipeline 里调 `node xxx.js`。
**必须**通过 Windows Python (C:\Python314) 间接调。

当前已修复的路径：
- `sync_notion_wrapper.py` → 写临时.py → Windows Python → Windows Node ✅
- `feedback.js` → 未修复（pipeline尾部会报错）

### C. 被归档到 archive/ 的关键依赖

上次整理时归档了514个脚本。以下**已经在根目录恢复**的：

| 文件 | 状态 | 被哪些脚本引用 |
|------|------|-------------|
| `sync_notion_wrapper.py` | ✅ 已恢复+重写 | run_pipeline.py |
| `_log_util.js` | ✅ 已恢复 | sync_notion.js, feedback.js |
| `_notion_verify.js` | ✅ 保留（未归档） | sync_notion.js, feedback.js, sync_summary.js |

**⚠️ 如果哪天某个JS报 `Cannot find module`，先去 `archive/` 找。**

---

## 六、快速参考

### 最常用命令

```bash
# 跑今天全部比赛（完整流水线）
cd ~/.openclaw/workspace/jingcai
python3 run_pipeline.py all

# 仅同步到 Notion（不用重跑流水线）
python3 sync_notion_wrapper.py add 2026-05-23

# 手动跑反馈
# （需要用 Windows Python 调 Windows Node）
C:\Python314\python.exe -c "
import subprocess
r = subprocess.run(['C:/Program Files/nodejs/node.exe', 'feedback.js', '2026-05-23'],
                   capture_output=True, text=True, timeout=3600)
print(r.stdout)
"

# 补充联赛缓存
python3 precache_leagues.py --enrich 19200

# 手动跑单场验证
python3 -c "from _verify_util import *; print(verify_all_steps('tasks/2026-05-23/data/match001_xxx'))"
```

### 文件结构关系图

```
jingcai/
├── run_pipeline.py          ← 🚀 入口
│
├── step0_fetch_matches.py   ← 比赛列表
├── step146_extractor.py     ← step1,4,6
├── step235_runner.py        ← step2,3,5
├── step7_runner.py          ← step7
├── step8_1923_extractor.py  ← step8,19-23
├── step918_extractor.py     ← step9-18
├── step24_extractor.py      ← step24
├── step25_zhuangjia.py      ← step25,26
│
├── final_report_generator.py  ← 📄 报告（被import: conclusion_signals, weight_engine）
├── sync_notion_wrapper.py     ← ☁️ Notion（→ Windows Python → Windows Node）
│
├── _league_util.py           ← 🔧 被 precache 引用
├── _verify_util.py           ← 🔧 被 run_pipeline import
├── _notion_verify.js         ← 🔧 被 sync_notion.js require
├── _log_util.py / .js        ← 🔧 被各脚本引用
├── _util.py                  ← 🔧 共享工具
│
├── precache_leagues.py       ← 预缓存
├── diagnose.py               ← 诊断
├── feedback_learner.py       ← 学习
├── feedback.js               ← 赛果
├── protect.py                ← 锁
│
├── conclusion_signals.py     ← 📦 信号引擎 (被 report import)
├── weight_engine_v3.py       ← 📦 权重引擎 (被 report import)
├── expert_pattern_engine.py  ← 📦 专家模式引擎 (被 report import)
│
├── sync_summary.js           ← Notion 汇总同步
├── notion_schema.js          ← Notion 结构定义
│
├── tasks/                    ← 比赛数据
│   └── {date}/
│       ├── 周六001_xxx.md    ← 报告（根目录）
│       ├── data/              ← 中间数据
│       │   ├── match001_xxx/  ← 每场数据目录
│       │   └── league_cache/  ← 联赛缓存
│       └── logs/              ← 日志
│
├── learnings/                 ← 学习结果
├── archive/                   ← 归档（514个旧脚本）
└── versions/                  ← 版本备份
```

---

## 七、各脚本运行环境速查

| 脚本 | 运行环境 | 能否从 pipeline 自动调 |
|------|---------|---------------------|
| `run_pipeline.py` | VM Python 3.6 | ✅ 入口 |
| `step*.py` (核心步骤) | VM Python 3.6 | ✅ |
| `final_report_generator.py` | VM Python 3.6 | ✅ |
| `precache_leagues.py` | VM Python 3.6 | ✅ |
| `_verify_util.py` | VM Python 3.6 | ✅ (被import) |
| `feedback_learner.py` | VM Python 3.6 | ⚠️ 有路径问题（见第五节A） |
| `diagnose.py` | VM Python 3.6 | ⚠️ 同上 |
| `sync_notion_wrapper.py` | VM Python 3.6 | ✅ (内部转发) |
| `sync_notion.js` | Windows Node.js | ✅ (通过wrapper) |
| `feedback.js` | Windows Node.js | ❌ 无法自动调 |
| `sync_summary.js` | Windows Node.js | ❌ 无法自动调 |

---

## 八、如果脚本丢失（被误归档）

**已经在 pipeline 尾部修复的**（恢复了关键脚本到根目录）：
- `sync_notion_wrapper.py` → ✅
- `_log_util.js` → ✅
- `_log_util.py` → ✅（保留）

**如果以后又出现 `Cannot find module` / `No such file`：**
1. `ls archive/*xxx*` 在 archive 找
2. `cp archive/xxx.js .` 恢复
3. 然后更新本文件
