import json
import requests
import re
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

API_KEY = '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'
DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
}

# 查询所有比赛
r = requests.post(f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=HEADERS, data=json.dumps({
    'filter': {'property': '比赛', 'rich_text': {'is_not_empty': True}},
    'page_size': 100
}))
pages = r.json()['results']
print(f'Notion中共有 {len(pages)} 场比赛\n')

# 提取字段
matches = []
for p in pages:
    name = p['properties']['Name']['title'][0]['plain_text']
    date_props = p['properties'].get('比赛日期', {})
    date_val = date_props.get('date', {}).get('start', '') if date_props.get('date') else ''
    
    pred = p['properties']['竞彩预测']['rich_text'][0]['plain_text'] if p['properties']['竞彩预测']['rich_text'] else ''
    step26 = p['properties'].get('步26_庄家最看好', {})
    step26_val = step26['rich_text'][0]['plain_text'] if step26.get('rich_text') and step26['rich_text'] else ''
    
    actual_score = p['properties']['实际比分']['rich_text'][0]['plain_text'] if p['properties']['实际比分']['rich_text'] else ''
    actual_result = p['properties']['实际结果']['rich_text'][0]['plain_text'] if p['properties']['实际结果']['rich_text'] else ''
    
    m = re.match(r'(周[一二三四五六日]\d+)', name)
    match_num = m.group(1) if m else ''
    
    if date_val and actual_score:  # 只有已反馈的
        # 解析实际胜平负
        hs, as_ = map(int, actual_score.split(':'))
        if hs > as_: actual_r = '胜'
        elif hs < as_: actual_r = '负'
        else: actual_r = '平'
        
        matches.append({
            'match_num': match_num,
            'date': date_val,
            'name': name,
            'pred': pred,
            'step26': step26_val,
            'score': actual_score,
            'result': actual_result,
            'actual_r': actual_r,
        })

print(f'已反馈比赛: {len(matches)} 场\n')

# 只取5月10日
yesterday = [m for m in matches if m['date'] == '2026-05-10']
print(f'5月10日比赛: {len(yesterday)} 场\n')

# 按 竞彩预测+步26 分组
from collections import defaultdict

def group_key(pred, step26):
    return f"竞彩:{pred} | 步26:{step26}"

groups = defaultdict(lambda: {'total': 0, '胜': 0, '平': 0, '负': 0, 'matches': []})

# 先统计5月10日
print('=' * 80)
print('5月10日 30场比赛分组统计')
print('=' * 80)

for m in yesterday:
    key = group_key(m['pred'], m['step26'])
    groups[key]['total'] += 1
    groups[key][m['actual_r']] += 1
    groups[key]['matches'].append(m)

for key in sorted(groups.keys()):
    g = groups[key]
    print(f'\n{key}')
    print(f'  总场次: {g["total"]} | 胜: {g["胜"]} | 平: {g["平"]} | 负: {g["负"]}')
    for m in g['matches']:
        mark = '✅' if m['result'] == m['actual_r'] else '❌'
        print(f'    {mark} {m["match_num"]} {m["score"]} {m["actual_r"]}')

# 统计所有比赛
print('\n' + '=' * 80)
print('全部已反馈比赛分组统计')
print('=' * 80)

all_groups = defaultdict(lambda: {'total': 0, '胜': 0, '平': 0, '负': 0})
for m in matches:
    key = group_key(m['pred'], m['step26'])
    all_groups[key]['total'] += 1
    all_groups[key][m['actual_r']] += 1

# 按总场次排序
for key in sorted(all_groups.keys(), key=lambda k: -all_groups[k]['total']):
    g = all_groups[key]
    correct = g.get('胜', 0)  # 注意：这里应该是预测正确的场次，不是实际胜
    print(f'\n{key} - 总: {g["total"]} | 实际胜: {g["胜"]} | 实际平: {g["平"]} | 实际负: {g["负"]}')

# 额外：竞彩预测准确率
print('\n' + '=' * 80)
print('竞彩预测准确率')
print('=' * 80)

pred_correct = defaultdict(lambda: {'total': 0, 'correct': 0})
for m in matches:
    key = m['pred']
    if key:
        pred_correct[key]['total'] += 1
        if m['result'] == m['actual_r']:
            pred_correct[key]['correct'] += 1

for key in sorted(pred_correct.keys(), key=lambda k: -pred_correct[k]['total']):
    g = pred_correct[key]
    acc = g['correct'] / g['total'] * 100 if g['total'] > 0 else 0
    print(f'  竞彩预测={key}: {g["correct"]}/{g["total"]} ({acc:.1f}%)')

# 步26准确率
print('\n' + '=' * 80)
print('步26_庄家最看好准确率')
print('=' * 80)

step26_correct = defaultdict(lambda: {'total': 0, 'correct': 0})
for m in matches:
    key = m['step26']
    if key:
        step26_correct[key]['total'] += 1
        if m['result'] == m['actual_r']:
            step26_correct[key]['correct'] += 1

for key in sorted(step26_correct.keys(), key=lambda k: -step26_correct[k]['total']):
    g = step26_correct[key]
    acc = g['correct'] / g['total'] * 100 if g['total'] > 0 else 0
    print(f'  步26={key}: {g["correct"]}/{g["total"]} ({acc:.1f}%)')
