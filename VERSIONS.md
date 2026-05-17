# 竞彩工作区版本管理

## 版本记录

### v1.0.0 (2026-05-01) - Base 版本
**当前在用版本**

#### 流程脚本
| 脚本 | 版本 | 说明 |
|------|------|------|
| step0_fetch_matches.py | v1 | 获取竞彩比赛列表 |
| step146_extractor.py | v1 | 欧赔/让球/亚盘基础数据提取 |
| step235_runner.py | v1 | 欧赔同赔+让球同赔 |
| step7_runner.py | v1 | 澳门亚盘同赔 |
| step8_1923_extractor.py | v1 | 同联赛亚盘统计+百家对比 |
| step918_extractor.py | v1 | 主队/客队历史+盘路匹配 |
| step24_extractor.py | v1 | 盘路匹配汇总 |
| final_report_generator.py | v1 | 最终报告生成 |
| run_pipeline.py | v1 | 流水线调度 |
| batch_full.py | v1 | 历史数据全量重跑 |
| protect.py | v1 | 工作区保护（锁+标记） |

#### 功能
- 24步分析框架
- 历史数据批量重跑
- 工作区锁机制（防止多session冲突）
- Match级别标记（防止重复处理）
- 版本管理和回滚

#### 已知问题
- 无

---

## 版本管理命令

```bash
# 查看状态
python jingcai/protect.py status

# 获取锁
python jingcai/protect.py lock batch
python jingcai/protect.py unlock batch

# 版本管理
python jingcai/version.py init          # 初始化base版本
python jingcai/version.py snapshot      # 创建快照
python jingcai/version.py list          # 列出所有版本
python jingcai/version.py diff <name>   # 比较差异
python jingcai/version.py restore <name># 回滚到指定版本
```

---

## 版本变更日志

### 2026-05-01
- **v1.0.0** - 初始版本
  - 24步分析框架
  - 批量重跑
  - 工作区保护
  - 版本管理
