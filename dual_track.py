# -*- coding: utf-8 -*-
"""双引擎追踪：赛后比对两套预测谁更准"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dual_predict import get_dim_scores_from_report, predict_model, predict_current

TRACK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'learnings', 'dual_track.json')

def process_day(date_str):
    """处理一天的比赛，记录双引擎预测"""
    tasks_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasks')
    feedback_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'learnings', 'feedback.json')
    
    # 加载赛果
    with open(feedback_path, 'r', encoding='utf-8') as f:
        fb = json.load(f)
    day_fb = fb.get('dates', {}).get(date_str, {}).get('feedback', [])
    results = {}
    for rec in day_fb:
        mn = rec.get('match_num', '').strip()
        actual = rec.get('actual', '')
        if mn and actual in ('胜', '平', '负'):
            results[mn] = actual
    
    # 加载已有追踪数据
    track = {}
    if os.path.exists(TRACK_FILE):
        with open(TRACK_FILE, 'r', encoding='utf-8') as f:
            track = json.load(f)
    
    # 扫描当天报告
    day_dir = os.path.join(tasks_dir, date_str)
    if not os.path.isdir(day_dir):
        return 0
    
    updated = 0
    for f in sorted(os.listdir(day_dir)):
        if not f.endswith('.md') or f in ['sunday_matches.md','monday_matches.md','season_schedule.md']:
            continue
        
        # 提取match_num
        m = re.search(r'(\d{3})', f)
        if not m: continue
        mn = m.group(1)
        
        # 跳过已追踪的
        key = f'{date_str}_{mn}'
        if key in track and track[key].get('actual'):
            continue
        
        # 取实际赛果
        actual = results.get(mn) or results.get(str(int(mn)))
        if not actual: continue
        
        # 读报告
        report_path = os.path.join(day_dir, f)
        with open(report_path, 'r', encoding='utf-8') as fh:
            text = fh.read()
        
        scores = get_dim_scores_from_report(text)
        if not scores: continue
        
        # 两套预测
        current = predict_current(scores)
        model_pred = predict_model(scores)
        
        # 从原报告提取手拍预测
        old_pred = ''
        mp = re.search(r'\*\*竞彩预测\*\*\s*\|?\s*([^\n|]+)', text)
        if mp: old_pred = mp.group(1).strip()
        
        # 判断胜负
        def result_to_label(r):
            if '胜' in r: return '胜'
            if '负' in r: return '负'
            return '平'
        
        old_label = result_to_label(old_pred)
        model_label = model_pred['prediction']
        
        track[key] = {
            'date': date_str,
            'match_num': mn,
            'match': f.replace('.md', ''),
            'actual': actual,
            'hand_picked': {'prediction': old_label, 'confidence': '', 'raw': old_pred},
            'data_driven': {'prediction': model_label, 'confidence': model_pred['confidence'], 'score': model_pred['composite_score']},
            'hand_correct': old_label == actual,
            'model_correct': model_label == actual,
        }
        updated += 1
    
    if updated > 0:
        with open(TRACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(track, f, ensure_ascii=False, indent=2)
    
    return updated

def show_stats():
    """显示追踪统计"""
    if not os.path.exists(TRACK_FILE): return
    with open(TRACK_FILE, 'r', encoding='utf-8') as f:
        track = json.load(f)
    
    completed = {k: v for k, v in track.items() if v.get('actual')}
    if not completed: return
    
    hand_correct = sum(1 for v in completed.values() if v.get('hand_correct'))
    model_correct = sum(1 for v in completed.values() if v.get('model_correct'))
    total = len(completed)
    
    print(f'双引擎追踪统计 ({total}场):')
    print(f'  手拍规则: {hand_correct}/{total} ({hand_correct/total*100:.1f}%)')
    print(f'  数据驱动: {model_correct}/{total} ({model_correct/total*100:.1f}%)')

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'stats':
        show_stats()
    elif len(sys.argv) > 1:
        updated = process_day(sys.argv[1])
        print(f'更新 {updated} 条追踪记录')
        show_stats()
    else:
        print('用法: python dual_track.py <date> 或 python dual_track.py stats')
