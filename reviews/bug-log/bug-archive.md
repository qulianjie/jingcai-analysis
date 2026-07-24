# Bug 归档

> 记录已修复的关键Bug，防止回归

---

## [B001] Step25 庄家盈亏Profit负号被吃掉

**严重程度**: 🔴 高（影响所有预测结论）

**发现日期**: 2026-05-??（可能更早）

**根因**: `step25_zhuangjia.py:79`

```python
'profit': int(profit_raw.replace(',', '').replace('-', ''))
#                                    ^^^^^^^^^^^^
# 把负号也去掉了，所有方向profit变正数
```

**连锁影响**:
1. `final_conclusion_generator.py:1206` 用 `max(profits)` 选庄家最看好 → 选了亏损最大的方向（完全错误）
2. `conclusion_signals.py:380-382` 用错误数据算score
3. 报告全正数，迷惑性极大

**修复**:
```python
'profit': int(profit_raw.replace(',', '')) if profit_raw else 0,
```

**验证方法**:
```python
# 检查raw有负号但parsed为正 → bug回归
assert (parsed < 0) == (raw.lstrip('-').replace(',', '') != raw.replace(',', ''))
```

**参考**: `references/step25-profit-sign-bug.md`（完整案例分析）

---

## [B002] Notion同步400错误（空字符串字段）

**严重程度**: 🔴 高（同步失败）

**发现日期**: 2026-05-??

**根因**: 来源字段传空字符串 `""` 给Notion API，Notion不接受空字符串类型的rich_text，返回400

**修复**: 源字段为空时传 `null` 而非 `""`

**附加修复**: rich_text截断加1990字限制，防止超长文本被Notion拒绝

---

## [B003] 路径错误导致cron运行失败（no_agent模式）

**严重程度**: 🟡 中（cron任务）

**发现日期**: 2026-05-??

**根因**: no_agent模式下，Win主机bash执行脚本时，WSL bash不认 `C:\...` 路径，返回exit 127

**修复**: 
- no_agent模式改为agent+terminal模式
- 路径使用 `/mnt/c/...` WSL路径格式

---

## [B004] WSL Node.js 通过 stdio 读写 Windows 文件报 EISDIR

**严重程度**: 🟡 中（跨平台开发）

**根因**: WSL内Node.js通过stdio接口读写Windows文件系统时，路径解析错误导致被当作目录

**修复**: 改为Windows Python桥接 → Windows Node.js 执行

**方案**: `WSL Python → Windows Python → Windows Node.js`

---

## [B005] sporttery.cn 数据源失效

**严重程度**: 🔴 高（数据源不可用）

**发现日期**: 2026-??-??

**原因**: 源站停止服务

**处理**: 
- 标记 `sporttery.cn` 为已停用
- 所有依赖此数据源的功能迁移到 `trade.500.com` / `odds.500.com`

---

## [B006] write_file工具写/mnt/c/返回成功但文件不存在

**严重程度**: 🟡 中（开发工具）

**发现日期**: 2026-05-??

**根因**: Hermes的write_file工具在跨文件系统（WSL→Windows NTFS）时状态报告不可靠

**修复**: 改用 `cat > << 'PYEOF'` heredoc方式写入 `/mnt/c/` 路径

---

## [B007] 联赛ID映射大量错误

**严重程度**: 🟡 中（数据准确率）

**发现日期**: 2026-05-17

**根因**: `_league_util.py` 中49个联赛ID有26个错误

**示例**: 澳超 19528→19200, 意甲 19498→9080, 西甲 19496→9124 等

**修复**: 全部49个联赛ID修正

**影响**: 修正后蓝军FHH从27场→514场（19倍），A-League从55场→590场（10.7倍）

---

## [B008] 同步后字段空值无法自动溯源

**严重程度**: 🟡 中（数据质量）

**发现日期**: 2026-05-??（添加post-sync verify时）

**根因**: 写入Notion后不做回读验证，空字段无法区分"缺失源文件"/"解析bug"/"旧流水线结构"

**修复**: 新增post-sync verify，检查Notion所有字段非空，空字段自动溯源
