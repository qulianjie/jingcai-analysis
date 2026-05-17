import json
import requests
from collections import defaultdict
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

API_KEY = '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'
DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
}

# 查询所有比赛（不用日期过滤，直接全部查）
r = requests.post(f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=HEADERS, data=json.dumps({
    'filter': {'property': '比赛', 'rich_text': {'is_not_empty': True}},
    'page_size': 100
}))
pages = r.json()['results']
print(f'总比赛数: {len(pages)}\n')

# 提取所有比赛信息
all_matches = []
may10_matches = []

for p in pages:
    name = p['properties']['Name']['title'][0]['plain_text']
    
    # 比赛日期
    date_val = p['properties']['比赛日期']['date']['start'] if p['properties']['比赛日期']['date'] else ''
    
    # 竞彩预测
    pred = p['properties']['竞彩预测']['rich_text'][0]['plain_text'] if p['properties']['竞彩预测']['rich_text'] else ''
    
    # 步26_庄家最看好
    step26_val = ''
    step26_prop = p['properties'].get('步26_庄家最看好', {})
    if step26_prop.get('rich_text') and step26_prop['rich_text']:
        step26_val = step26_prop['rich_text'][0]['plain_text']
    
    # 实际比分
    score = p['properties']['实际比分']['rich_text'][0]['plain_text'] if p['properties']['实际比分']['rich_text'] else ''
    
    # 预测正确 checkbox
    pred_correct = p['properties'].get('预测正确', {}).get('checkbox', False)
    
    # 让球预测正确
    rang_correct = p['properties'].get('让球预测正确', {}).get('checkbox', False)
    
    match = {
        'name': name,
        'date': date_val,
        'pred': pred,
        'step26': step26_val,
        'score': score,
        'pred_correct': pred_correct,
        'rang_correct': rang_correct,
    }
    all_matches.append(match)
    
    if date_val and '2026-05-10' in date_val:
        may10_matches.append(match)

print(f'5月10日比赛: {len(may10_matches)} 场\n')

# 显示5月10日比赛详情
print('='*80)
print('5月10日比赛详情')
print('='*80)
for m in may10_matches:
    pred_ok = '✅' if m['pred_correct'] else '❌'
    rang_ok = '✅' if m['rang_correct'] else '❌'
    print(f'  {m["name"]} | 比分:{m["score"]} | 竞彩:{m["pred"]}{pred_ok} | 步26:{m["step26"]}{rang_ok}')

# 统计
print('\n' + '='*80)
print('按 竞彩预测+步26 分组统计')
print('='*80)

# 5月10日
groups_510 = defaultdict(lambda: {'total': 0, '竞彩正确': 0, '让球正确': 0, '胜': 0, '平': 0, '负': 0})
for m in may10_matches:
    key = f"竞彩:{m['pred']} | 步26:{m['step26']}"
    groups_510[key]['total'] += 1
    if m['pred_correct']:
        groups_510[key]['竞彩正确'] += 1
    if m['rang_correct']:
        groups_510[key]['让球正确'] += 1
    
    # 解析比分
    if ':' in m['score']:
        hs, as_ = map(int, m['score'].split(':'))
        if hs > as_: groups_510[key]['胜'] += 1
        elif hs < as_: groups_510[key]['负'] += 1
        else: groups_510[key]['平'] += 1

print('\n--- 5月10日 ---')
for key in sorted(groups_510.keys()):
    g = groups_510[key]
    acc_pred = g['竞彩正确'] / g['total'] * 100 if g['total'] > 0 else 0
    acc_rang = g['让球正确'] / g['total'] * 100 if g['total'] > 0 else 0
    print(f'\n{key}')
    print(f'  总: {g["total"]} | 竞彩正确: {g["竞彩正确"]}({acc_pred:.0f}%) | 让球正确: {g["让球正确"]}({acc_rang:.0f}%)')
    print(f'  实际胜: {g["胜"]} | 实际平: {g["平"]} | 实际负: {g["负"]}')

# 全部比赛
print('\n' + '='*80)
print('全部比赛统计')
print('='*80)

groups_all = defaultdict(lambda: {'total': 0, '竞彩正确': 0, '让球正确': 0, '胜': 0, '平': 0, '负': 0})
for m in all_matches:
    if not m['score']: continue  # 跳过没比分的
    key = f"竞彩:{m['pred']} | 步26:{m['step26']}"
    groups_all[key]['total'] += 1
    if m['pred_correct']:
        groups_all[key]['竞彩正确'] += 1
    if m['rang_correct']:
        groups_all[key]['让球正确'] += 1
    
    if ':' in m['score']:
        hs, as_ = map(int, m['score'].split(':'))
        if hs > as_: groups_all[key]['胜'] += 1
        elif hs < as_: groups_all[key]['负'] += 1
        else: groups_all[key]['平'] += 1

# 按总场次排序
for key in sorted(groups_all.keys(), key=lambda k: -groups_all[k]['total']):
    g = groups_all[key]
    acc_pred = g['竞彩正确'] / g['total'] * 100 if g['total'] > 0 else 0
    acc_rang = g['让球正确'] / g['total'] * 100 if g['total'] > 0 else 0
    print(f'\n{key}')
    print(f'  总: {g["total"]} | 竞彩正确: {g["竞彩正确"]}({acc_pred:.0f}%) | 让球正确: {g["让球正确"]}({acc_rang:.0f}%)')
    print(f'  实际胜: {g["胜"]} | 实际平: {g["平"]} | 实际负: {g["负"]}')
