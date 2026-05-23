# CHANGELOG

## 2026-05-23

### 新增
- **让球支持率算法升级** (final_conclusion_generator.py):
  - 新增 `get_rq_cache_support()` 使用联赛缓存查历史相似盘口+相近赔率
  - 最终信心 = 联赛历史(0.7) + 同赔数据(0.3)
  - 输出样本来源注释 (e.g. "联赛31场+同赔4场")
- **联赛缓存系统** (precache_leagues.py, _league_util.py):
  - 从 `liansai.500.com` 自动获取联赛比赛数据并缓存
  - 2轮反向发现机制：从已知队爬取对手扩大覆盖面
  - `--enrich` 模式并行获取每场的赔率详情
  - 增量保存：每50个FID自动保存一次，防止超时丢失
  - 批量富化脚本 batch_enrich_standalone.py 处理大联赛
- **赛后反馈增强** (sync_feedback.js):
  - fetchFinalOdds 增加降级：如果 `matches_data.json` 没匹配目录，直接从 odds.500.com 按FID获取
- **汇总同步增强** (sync_summary.js):
  - 修复路径问题：改用 `__dirname` 而不是硬编码 jingcai/ 前缀

### 修复
- **联赛ID映射** (_league_util.py): 49个联赛ID全部修正（26个错误 → 正确ID）
  - 原映射错误举例：澳超 19528→19200, 意甲 19498→9080, 西甲 19496→9124 等
- **让球指数盘路字段** (final_conclusion_generator.py):
  - 修正 regex 双转义问题（line 913）
  - step1 读盘口加入 .txt 降级
  - meta.json 缺少 rq 字段 → 从 matches_data.json 补齐
  - step5 文件为空时从 step4 读让球
- **Notion同步降级** (sync_notion.js):
  - 所有步骤文件 `.md` → `.txt` 降级读取（step01_europe_basic.md → step1_europe_base.txt 等）
  - 澳门亚盘盘路 (step6/step8)、让球指数盘路 (step4) 增加 .txt fallback
- **同步后自检** (sync_notion.js):
  - 新增 post-sync verify：检查 Notion 所有字段非空
  - 空字段自动溯源（缺失源文件/解析bug/旧流水线结构）
- **蓝军FHH联赛数据质变** (precache_leagues.py):
  - 2轮反向发现前只拿到27场 → 反向发现后 514场（19倍提升）
- **A-League数据质变**：
  - 反向发现前55场 → 反向发现后590场（10.7倍提升）

### 优化方向（待实现）
- 让球支持率加权系数弹性化（同联赛样本数决定权重）
- Wilson置信区间取代直出胜率
- 历史准确率贝叶斯校准信心
