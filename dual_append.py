# -*- coding: utf-8 -*-
"""在已生成的报告后追加双引擎对比"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dual_predict import get_dim_scores_from_report, predict_model, predict_current

def append_dual_section(report_path):
    with open(report_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 如果已有双引擎对比，跳过
    if '## 双引擎预测对比' in text:
        return False
    
    # 获取维度分
    scores = get_dim_scores_from_report(text)
    if not scores:
        return False
    
    # 两套预测
    current = predict_current(scores)
    model_pred = predict_model(scores)
    
    # 从原报告提取手拍预测
    old_pred = ''
    m = re.search(r'\*\*竞彩预测\*\*\s*\|?\s*([^\n|]+)', text)
    if m: old_pred = m.group(1).strip()
    
    section = f'''
---
## 双引擎预测对比

| 引擎 | 预测 | 综合分 | 置信度 |
|------|------|--------|--------|
| **手拍规则** （现行） | {old_pred} | {current.get("composite_score", "?")} | {current.get("confidence", "?")} |
| **数据驱动** （V2试验） | {model_pred["prediction"]} | {model_pred["composite_score"]} | {model_pred["confidence"]} |

> 数据驱动模型基于 {model_pred.get("weights_used",{})} 维度权重
> 两套同时运行中，赛果后自动比对准确率

'''
    
    with open(report_path, 'a', encoding='utf-8') as f:
        f.write(section)
    return True

if __name__ == '__main__':
    if len(sys.argv) > 1:
        append_dual_section(sys.argv[1])
        print(f'双引擎对比已追加: {sys.argv[1]}')
    else:
        print('用法: python dual_append.py <report.md>')
