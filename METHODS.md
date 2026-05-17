# 竞彩24步 - 方法库 (METHODS.md)

## 脚本清单与步骤映射

### 核心流程脚本（通用型，带runner后缀）

| 脚本 | 位置 | 步骤 | 用途 |
|------|------|------|------|
| `step0_fetch_matches.py` | `jingcai/` | 第0步 | 获取竞彩比赛列表 |
| `step146_extractor.py` | `jingcai/` | ✅ 1,4,6 | 欧赔/让球/亚盘基础数据（固定3家/1家/3家） |
| `step235_runner.py` | `jingcai/` | ✅ 2,3,5 | 欧赔同赔+让球同赔（从AJAX获取） |
| `step7_runner.py` | `jingcai/` | ✅ 7 | 澳门亚盘同赔（从HTML解析） |
| `step8_1923_extractor.py` | `jingcai/` | ✅ 8+19-23 | 同联赛亚盘统计+百家欧赔对比（合并脚本） |
| `step918_extractor.py` | `jingcai/` | ✅ 9-18 | 主队/客队历史+盘路匹配（3层过滤） |
| `step24_extractor.py` | `jingcai/` | ✅ 24 | 步骤24盘路匹配汇总 |
| `final_report_generator.py` | `jingcai/` | - | 自动生成完整分析报告（24步完成后触发） |

**最终报告命名**：`jingcai/tasks/{日期}/周几00几_主队vs客队.md`
**脚本用法**：`python jingcai/final_report_generator.py <match目录路径> [输出路径]`

### 每步提取规则（关键公司）

#### 第1步：欧赔基础
- **数据源**：`https://odds.500.com/fenxi/ouzhi-{fid}.shtml`
- **脚本**：`step146_extractor.py` ✅ 已创建
- **用法**：`python step146_extractor.py <fid> <league> [output_path]`
- **提取公司**（固定3家）：
  1. **竞彩官方**（row#1）- td[3-8]
  2. **Interwetten**（row#6）- td[3-8]
  3. **百家平均**（平均值行）- td[3-8]
- **提取字段**：初胜/初平/初负/即时胜/即时平/即时负
- **输出格式**：Markdown表格，含盘路变化符号

#### 第2步：竞彩同赔
- **数据源**：AJAX `https://odds.500.com/fenxi1/inc/ouzhi_sameajax.php`
- **脚本**：`step235_runner.py` ✅ 已创建
- **参数**：cid=1, 竞彩初盘赔率, fid
- **输出**：同赔历史数据表格

#### 第3步：Interwetten同赔
- **数据源**：AJAX `https://odds.500.com/fenxi1/inc/ouzhi_sameajax.php`
- **脚本**：`step235_runner.py` ✅ 已创建
- **参数**：cid=4, Interwetten初盘赔率, fid
- **输出**：同赔历史数据表格

#### 第4步：让球基础
- **数据源**：`https://odds.500.com/fenxi/rangqiu-{fid}.shtml`
- **脚本**：`step146_extractor.py` ✅ 已创建
- **提取公司**（固定1家）：
  1. **竞彩官方**（row#1）- td[4-9]（偏移1列，td[2]是让球数）
- **提取字段**：让球数/初胜/初平/初负/即时胜/即时平/即时负

#### 第5步：让球同赔
- **数据源**：AJAX `https://odds.500.com/fenxi1/inc/rangqiu_sameajax.php`
- **脚本**：`step235_runner.py` ✅ 已创建
- **参数**：cid=1, 让球初盘赔率, fid, handicapline
- **输出**：同赔历史数据表格

#### 第6步：亚盘基础
- **数据源**：`https://odds.500.com/fenxi/yazhi-{fid}.shtml`
- **脚本**：`step146_extractor.py` ✅ 已创建
- **提取公司**（固定3家，必选澳门）：
  1. **威廉希尔**（row#1）
  2. **澳门**（row#2）- 必选
  3. **立博**（row#3）
- **提取字段**：初盘盘口/初盘主队水位/初盘客队水位/即时盘盘口/即时盘主队水位/即时盘客队水位

#### 第7步：澳门亚盘同赔
- **数据源**：`https://odds.500.com/fenxi1/yazhi_same.php?cid=5&cp={GBK盘口}&id={fid}&s1={主队水位}&s2={客队水位}`
- **脚本**：`step7_runner.py` ✅ 已创建
- **用法**：`python step7_runner.py <fid> <league> [output_path]`
- **提取**：从HTML表格解析同赔数据（每行2列：序号+比赛信息）
- **输出**：同赔历史数据表格

#### 第8步+第19-23步：联赛相同亚盘统计+百家对比
- **数据源**:
  - 联赛赛程: `https://liansai.500.com/team/{TEAM_ID}/teamfixture/` (16支球队各30场)
  - 亚盘: `https://odds.500.com/fenxi/yazhi-{fid}.shtml`
  - 百家欧赔: `https://odds.500.com/fenxi/ouzhi-{fid}.shtml`
  - 竞彩欧赔: `https://odds.500.com/fenxi/ouzhi-{fid}.shtml`
  - 竞彩让球: `https://odds.500.com/fenxi/rangqiu-{fid}.shtml`
- **脚本**: `step8_1923_extractor.py` ✅ 已验证
- **用法**: `python step8_1923_extractor.py <home_id> <away_id> <league> <fid> <macau_line> [output_path]`
- **示例**: `python step8_1923_extractor.py 2465 848 瑞典超 1362643 "一球/球半" output.txt`
- **Step 8 流程**:
  1. 获取整个联赛所有球队赛程（16支×30场=480条，去重后135场）
  2. 筛选相同联赛（`SIMPLEGBNAME == 本场比赛联赛名称`）
  3. **精确匹配盘口**：去掉"升""降"后缀后完全一致（如`一球/球半` == `一球/球半`，不匹配`一球`）
  4. 去重（主队和客队赛程可能包含同一场比赛）
  5. 逐场获取澳门亚盘+竞彩欧赔+竞彩让球
- **Step 19-23 流程**:
  1. 获取全部联赛比赛的百家欧赔数据
  2. **百家匹配规则**：只对比**主胜+客胜**（平局不参与），整数+小数点第一位一致即匹配
  3. 第22步已删除（与第19步重复）
- **输出A**: 亚盘统计明细（含主场水位差、客场水位差两列）
- **输出B**: 欧赔明细（竞彩官方）
- **输出C**: 让球指数（竞彩）
- **Step 19-23 输出**: 百家欧赔对比表格（初盘/终盘/盘路变化/盘路匹配度）

#### 第9步：主队主场·相同联赛·澳门亚盘同赔
- **数据源**：`https://liansai.500.com/team/{主队ID}/teamfixture/`
- **脚本**：`step918_extractor.py` ✅ 已创建
- **用法**：`python step918_extractor.py <home_id> <away_id> <league> <fid> <macau_line> [output_dir]`
- **筛选条件（3层过滤）**：
  1. **主客场**：`HOMETEAMID == 主队ID`
  2. **联赛**：`SIMPLEGBNAME == 本场比赛联赛名称`
  3. **盘口**：`HANDICAPLINENAME` 包含第6步澳门即时盘口中文名称
- **提取字段**：日期/对阵/比分/半场/赛果/盘口/盘路/大小
- **输出格式**：Markdown表格 + 统计（胜率/赢盘率/场均进球/场均失球）
- **注意**：liansai页面固定返回最近30场，无法扩展到50场

#### 第10步：主队比赛·竞彩官方欧赔
- **数据源**：每场比赛的 `https://odds.500.com/fenxi/ouzhi-{fid}.shtml`
- **脚本**：`step918_extractor.py` ✅ 已创建（内置）
- **提取公司**：竞彩官方（row#1）
- **输出**：每场比赛的初盘/终盘赔率 + 盘路变化 + 盘路匹配度（高/中/低）

#### 第11步：主队比赛·Interwetten欧赔
- **数据源**：每场比赛的 `https://odds.500.com/fenxi/ouzhi-{fid}.shtml`
- **脚本**：`step918_extractor.py` ✅ 已创建（内置）
- **提取公司**：Interwetten（row#6）
- **输出**：每场比赛的初盘/终盘赔率 + 盘路变化 + 盘路匹配度

#### 第12步：主队比赛·百家平均欧赔
- **数据源**：每场比赛的 `https://odds.500.com/fenxi/ouzhi-{fid}.shtml`
- **脚本**：`step918_extractor.py` ✅ 已创建（内置）
- **提取公司**：百家平均（平均值行）
- **输出**：每场比赛的初盘/终盘赔率 + 盘路变化 + 盘路匹配度

#### 第13步：主队比赛·竞彩让球指数
- **数据源**：每场比赛的 `https://odds.500.com/fenxi/rangqiu-{fid}.shtml`
- **脚本**：`step918_extractor.py` ✅ 已创建（内置）
- **提取公司**：竞彩官方（row#1）
- **输出**：每场比赛的初盘/终盘让球赔率 + 盘路变化 + 盘路匹配度
- **统计**：盘路完全一致/部分相同/完全不同的胜平负分布

#### 第14步：客队客场·相同联赛·澳门亚盘同赔
- **数据源**：`https://liansai.500.com/team/{客队ID}/teamfixture/`
- **脚本**：`step918_extractor.py` ✅ 已创建
- **筛选条件（3层过滤）**：
  1. **主客场**：`AWAYTEAMID == 客队ID`
  2. **联赛**：`SIMPLEGBNAME == 本场比赛联赛名称`
  3. **盘口**：`HANDICAPLINENAME` 包含第6步澳门即时盘口中文名称
- **注意**：客队让球盘口方向与主队相反，匹配时需用客队视角的盘口

#### 第15步：客队比赛·竞彩官方欧赔
- **脚本**：`step918_extractor.py` ✅ 已创建（内置）
- **格式同第10步**

#### 第16步：客队比赛·Interwetten欧赔
- **脚本**：`step918_extractor.py` ✅ 已创建（内置）
- **格式同第11步**

#### 第17步：客队比赛·百家平均欧赔
- **脚本**：`step918_extractor.py` ✅ 已创建（内置）
- **格式同第12步**

#### 第18步：客队比赛·竞彩让球指数
- **脚本**：`step918_extractor.py` ✅ 已创建（内置）
- **格式同第13步**

#### 第19-23步：百家对比
- **数据源**：`https://odds.500.com/fenxi/ouzhi-{fid}.shtml`
- **脚本**：`step8_1923_extractor.py` ✅ 已验证（与第8步合并）
- **百家匹配规则**：
  - 只对比**主胜+客胜**（平局不参与匹配）
  - 整数+小数点第一位一致即匹配（如1.39→1.3，1.30→1.3）
  - 不允许上下浮动，必须精确匹配
- **第22步已删除**（与第19步内容重复）

#### 第24步：盘路匹配汇总
- **脚本**：`step24_extractor.py` ✅ 已创建
- **用法**：`python step24_extractor.py <match_dir> [output_path]`

#### 最终报告生成
- **脚本**：`final_report_generator.py` ✅ 已完成
- **用法**：`python jingcai/final_report_generator.py <match目录路径> [输出路径]`
- **报告命名**：`jingcai/tasks/{日期}/周几00几_主队vs客队.md`
- **支持两种meta.json格式**：
  1. `{"match": "周一002_米亚尔比vs哈尔姆斯", "fid": "...", ...}`
  2. `{"match_info": {"week": "周一", "match_no": "001", ...}}`
- **8大部分结构**：欧赔基础(1-3)/让球指数(4-5)/亚盘对比(6-8)/主队主场(9-13)/客队客场(14-18)/百家对比(19-23)/盘路匹配汇总(24)/最终结论
- **智能分析**：自动计算盘路变化、同联赛同盘口赢盘率风险、水位变化趋势、投注建议

---

## 已验证脚本（实测数据）

### step146_extractor.py
- **测试场次**：周一002（米亚尔比vs哈姆斯塔德，fid=1362643，瑞超）
- **测试结果**：
  - 第1步：竞彩1.29/4.55/7.50→1.29/4.55/7.50 ✅
  - 第1步：Interwetten 1.40/4.70/7.00→1.40/4.60/7.50 ✅
  - 第1步：百家平均 1.39/4.40/7.01→1.36/4.62/8.03 ✅
  - 第4步：竞彩让球-1，1.95/3.35/3.15→2.10/3.04/3.08 ✅
  - 第6步：威廉希尔/澳门/立博 3家 ✅
- **数据获取时间**：2026-04-28 14:41

### step918_extractor.py
- **测试场次**：周一002（米亚尔比vs哈姆斯塔德，fid=1362643，瑞超）
- **主队ID**：2465（米亚尔比）
- **客队ID**：848（哈姆斯塔德）
- **澳门盘口**：一球/球半
- **测试结果**：
  - 第9步：主队主场3场（3层过滤：主场+瑞典超+一球/球半）✅
  - 第10-13步：每场比赛独立欧赔/让球表格 ✅
  - 第14步：客队客场3场（3层过滤：客场+瑞典超+一球/球半）✅
  - 第15-18步：每场比赛独立欧赔/让球表格 ✅
  - 盘路匹配度统计：高/中/低分组统计 ✅
- **数据获取时间**：2026-04-28 15:24

### step8_1923_extractor.py
- **测试场次**：周一002（米亚尔比vs哈姆斯塔德，fid=1362643，瑞超）
- **主队ID**：2465（米亚尔比），**客队ID**：848（哈姆斯塔德）
- **澳门盘口**：一球/球半
- **联赛球队**：16支（瑞典超）
- **测试结果**：
  - Step 8：盘口匹配9场（精确匹配，无重复fid）✅
  - Step 19-23：百家匹配1场（主胜+客胜整数+第一位小数一致）✅
  - 百家基准：1.39/4.40/7.01 → 匹配 1.36/4.81/7.04（主胜1.3，客胜7.0）✅
  - 输出格式：Markdown表格+统计 ✅
- **关键修复**：
  1. 盘口精确匹配（`==` 而非 `in`），排除"一球"匹配"一球/球半"
  2. 主队+客队赛程去重（同一场比赛只保留一次）
  3. 百家匹配只对比主胜+客胜（平局不参与）
  4. 获取整个联赛135场数据（而非仅主队+客队33场）
- **数据获取时间**：2026-04-28 17:44

---

## 历史版本（已废弃）

以下脚本为开发调试过程中的历史版本，已全部整合到核心脚本中，保留仅供参考。

| 脚本 | 说明 |
|------|------|
| step8_agent_browser.py | agent-browser版step8 |
| step8_ajax.py | AJAX探索版 |
| step8_all_matches.py | 全匹配版 |
| step8_api_all.py | API版 |
| step8_batch_asian.py | 批量亚盘版 |
| step8_browser_all.py | 浏览器版 |
| step8_check_asian.py | 亚盘检查版 |
| step8_check_yazhi.py / step8_check_yazhi2.py | 亚盘验证版 |
| step8_explore.py / step8_explore2.py / step8_explore3.py / step8_explore_html.py | 探索版 |
| step8_extractor.py | 早期独立版 |
| step8_extract_all.py | 全提取版 |
| step8_find_ajax.py / step8_find_ajax2.py | AJAX发现版 |
| step8_full.py / step8_full_run.py | 完整版 |
| step8_full_schedule.py | 赛程版 |
| step8_full_search.py | 搜索版 |
| step8_get_asian.py | 亚盘获取版 |
| step8_get_html.py | HTML获取版 |
| step8_js_round.py | JS轮次版 |
| step8_league_data.py | 联赛数据版 |
| step8_league_explore.py | 联赛探索版 |
| step8_new_rules.py | 新规则版 |
| step8_parse_asian.py | 亚盘解析版 |
| step8_rounds.py | 轮次版 |
| step8_round_selector.py | 轮次选择版 |
| step8_round_url.py | 轮次URL版 |
| step8_run.py / step8_run2.py | 运行版 |
| step8_seasons.py | 赛季版 |
| step8_seasons_matches.py | 赛季比赛版 |
| step8_team_schedule.py | 球队赛程版 |
| step8_test_asian.py | 测试版 |
| merge_report.py | 旧版合并报告（已被final_report_generator.py替代） |
| step146_extractor.py | 早期1/4/6合并脚本（已整合到step146_extractor.py v2） |
| check_12_matches.py | 检查匹配 |
| check_liansai_api.py / check_liansai_structure.py | 联赛API检查 |
| check_stage_js.py | JS阶段检查 |
| extracted_data.py / extract_all.py / extract_better.py 等 | 数据提取测试脚本 |
