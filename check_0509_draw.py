# -*- coding: utf-8 -*-
"""Find 05-09 matches where prediction=平 AND 庄家看好=平"""
import os, sys, json

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

LEARNINGS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings'
TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

# Load feedback
with open(os.path.join(LEARNINGS_DIR, 'feedback.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get 05-09 data
date_data = data.get('dates', data).get('2026-05-09', {})
matches = date_data.get('feedback', [])

print(f'05-09 total matches: {len(matches)}')
print()

# Find matches where predicted=平 AND 庄家看好=平
found = []
for m in matches:
    predicted = m.get('predicted', '')
    s25 = m.get('s25', {})
    s26 = m.get('s26', {})
    zhuangjia_dir = s25.get('庄家方向', '')
    zhuangjia_hot = s25.get('大热方', '')
    s26_best = s26.get('综合盈亏方向', '')
    
    # Check if prediction is 平
    pred_is_draw = (predicted in ['平', '平局'])
    # Check if bookmaker favors 平
    bookmaker_favors_draw = (zhuangjia_dir in ['平局', '平'] or s26_best in ['平局', '平'])
    
    if pred_is_draw and bookmaker_favors_draw:
        found.append(m)
        print(f'=== {m.get("match_num","")} {m.get("league","")} {m.get("home","")} vs {m.get("away","")} ===')
        print(f'  竞彩预测: {predicted}')
        print(f'  竞彩信心: {m.get("confidence","")}')
        print(f'  庄家方向(step25): {zhuangjia_dir}')
        print(f'  庄家大热(step25): {zhuangjia_hot}')
        print(f'  庄家最看好(step26): {s26_best}')
        print(f'  实际比分: {m.get("score","")}')
        print(f'  实际结果: {m.get("actual","")}')
        print(f'  预测正确: {m.get("correct",False)}')
        print(f'  combos: {json.dumps(m.get("combos", {}), ensure_ascii=False)[:200]}')
        print()
    elif pred_is_draw:
        print(f'{m.get("match_num","")} 预测=平, 庄家方向={zhuangjia_dir}, 庄家最看好={s26_best} → 庄家不看好平')

print(f'\n=== 统计 ===')
print(f'竞彩预测=平的场次: {sum(1 for m in matches if m.get("predicted","") in ["平","平局"])}')
print(f'竞彩预测=平 AND 庄家看好=平: {len(found)}')

# Also check all dates for this pattern
print(f'\n=== 全量数据中 预测=平 AND 庄家看好=平 ===')
total_draw_draw = 0
total_draw_draw_correct = 0
total_pred_draw = 0

for date, date_info in data.get('dates', data).items():
    for m in date_info.get('feedback', []):
        predicted = m.get('predicted', '')
        if predicted not in ['平', '平局']:
            continue
        total_pred_draw += 1
        s25 = m.get('s25', {})
        s26 = m.get('s26', {})
        zhuangjia_dir = s25.get('庄家方向', '')
        s26_best = s26.get('综合盈亏方向', '')
        if zhuangjia_dir in ['平局', '平'] or s26_best in ['平局', '平']:
            total_draw_draw += 1
            if m.get('correct', False):
                total_draw_draw_correct += 1

print(f'所有日期 竞彩预测=平: {total_pred_draw}')
print(f'所有日期 预测=平 AND 庄家看好=平: {total_draw_draw}')
print(f'其中预测正确: {total_draw_draw_correct}')
if total_draw_draw > 0:
    print(f'准确率: {total_draw_draw_correct}/{total_draw_draw} = {total_draw_draw_correct/total_draw_draw*100:.1f}%')
