# -*- coding: utf-8 -*-
"""双引擎预测对比模块"""
import json, os, re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, 'learnings', 'model_v2.json')
DIM_ZH = ['欧赔趋势','竞彩同赔','IW同赔','澳门亚盘','让球同赔','主队主场','客队客场','百家对比','盘路匹配','庄家盈亏']

_model = None
def load_model():
    global _model
    if _model is None:
        with open(MODEL_PATH, 'r', encoding='utf-8') as f:
            _model = json.load(f)
    return _model

def get_dim_scores_from_report(report_text):
    """从报告文本提取各维度信号分"""
    dim_block = re.search(r'### 各维度信号明细.*?\n\| 维度.*?\n\|[-\|]+.*?\n((?:\|.*?\n)+)', report_text, re.DOTALL)
    if not dim_block: return {}
    scores = {}
    for line in dim_block.group(1).strip().split('\n'):
        cells = [c.strip() for c in line.split('|') if c.strip()]
        if len(cells) >= 3:
            sm = re.search(r'([+-]?\d+\.\d+)', cells[1])
            if sm and cells[0] in DIM_ZH:
                scores[cells[0]] = float(sm.group(1))
    return scores

def predict_model(dim_scores):
    """用数据驱动模型预测"""
    m = load_model()
    weights = m.get('weights', {})
    thresholds = m.get('thresholds', {})
    total = 0; total_w = 0
    for dim_zh in DIM_ZH:
        w = weights.get(dim_zh, 0.1)
        score = dim_scores.get(dim_zh, 0)
        total += score * w
        total_w += w
    final = total / total_w if total_w > 0 else 0
    th_win = thresholds.get('胜', {}).get('th', 0.1)
    th_lose = thresholds.get('负', {}).get('th', 0.1)
    if final > th_win:
        pred = '胜'; conf = min(100, max(30, int((final - th_win + 0.5) * 30 + 40)))
    elif final < -th_lose:
        pred = '负'; conf = min(100, max(30, int((-final - th_lose + 0.5) * 30 + 40)))
    else:
        pred = '平'; conf = 35
    return {'prediction': pred, 'confidence': f'{conf}%', 'composite_score': round(final, 3),
            'weights_used': {k: round(v,3) for k,v in sorted(weights.items(), key=lambda x:-x[1])[:5]}}

def predict_current(dim_scores):
    """简化的手拍引擎模拟"""
    total = sum(dim_scores.values())
    n = len([v for v in dim_scores.values() if abs(v) > 0.1])
    if n == 0: return {'prediction': '平', 'confidence': '33%', 'composite_score': 0}
    avg = total / n if n > 0 else 0
    if avg > 0.15:
        return {'prediction': '胜', 'confidence': f'{min(60, int(avg*50+45))}%', 'composite_score': round(avg, 3)}
    elif avg < -0.15:
        return {'prediction': '负', 'confidence': f'{min(60, int(-avg*50+45))}%', 'composite_score': round(avg, 3)}
    else:
        return {'prediction': '平', 'confidence': '40%', 'composite_score': round(avg, 3)}

if __name__ == '__main__':
    test_scores = {'欧赔趋势': 1.0, '盘路匹配': 0.389, '主队主场': 0.5}
    print('手拍:', predict_current(test_scores))
    print('模型:', predict_model(test_scores))
