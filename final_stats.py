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

# 查询5月10日比赛
r = requests.post(f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=HEADERS, data=json.dumps({
    'filter': {'property': '比赛日期', 'date': {'equals': '2026-05-10'}},
    'page_size': 100
}))
may10_pages = r.json()['results']
print(f'5月10日比赛: {len(may10_pages)} 场\n')

# 查询所有比赛
r = requests.post(f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=HEADERS, data=json.dumps({
    'filter': {'property': '比赛', 'rich_text': {'is_not_empty': True}},
    'page_size': 100
}))
all_pages = r.json()['results']
print(f'所有比赛: {len(all_pages)} 场\n')

def extract_matches(pages):
    matches = []
    for p in pages:
        name = p['properties']['Name']['title'][0]['plain_text']
        date_val = p['properties']['比赛日期']['date']['start'] if p['properties']['比赛日期']['date'] else ''
        pred = p['properties']['竞彩预测']['rich_text'][0]['plain_text'] if p['properties']['竞彩预测']['rich_text'] else ''
        step26_val = ''
        step26_prop = p['properties'].get('步26_庄家最看好', {})
        if step26_prop.get('rich_text') and step26_prop['rich_text']:
            step26_val = step26_prop['rich_text'][0]['plain_text']
        score = p['properties']['实际比分']['rich_text'][0]['plain_text'] if p['properties']['实际比分']['rich_text'] else ''
        pred_correct = p['properties'].get('预测正确', {}).get('checkbox', False)
        rang_correct = p['properties'].get('让球预测正确', {}).get('checkbox', False)
        matches.append({
            'name': name,
            'date': date_val,
            'pred': pred,
            'step26': step26_val,
            'score': score,
            'pred_correct': pred_correct,
            'rang_correct': rang_correct,
        })
    return matches

may10_matches = extract_matches(may10_pages)
all_matches = extract_matches(all_pages)

# 5月10日统计
print('='*80)
print('5月10日 30场比赛 - 按竞彩预测+步26分组统计')
print('='*80)

groups_510 = defaultdict(lambda: {'total': 0, '竞彩正确': 0, '让球正确': 0, '胜': 0, '平': 0, '负': 0})
for m in may10_matches:
    key = f"竞彩:{m['pred']} | 步26:{m['step26']}"
    groups_510[key]['total'] += 1
    if m['pred_correct']: groups_510[key]['竞彩正确'] += 1
    if m['rang_correct']: groups_510[key]['让球正确'] += 1
    if ':' in m['score']:
        hs, as_ = map(int, m['score'].split(':'))
        if hs > as_: groups_510[key]['胜'] += 1
        elif hs < as_: groups_510[key]['负'] += 1
        else: groups_510[key]['平'] += 1

for key in sorted(groups_510.keys()):
    g = groups_510[key]
    acc_pred = g['竞彩正确'] / g['total'] * 100 if g['total'] > 0 else 0
    acc_rang = g['让球正确'] / g['total'] * 100 if g['total'] > 0 else 0
    print(f'\n{key}')
    print(f'  总: {g["total"]} | 竞彩正确: {g["竞彩正确"]}({acc_pred:.0f}%) | 让球正确: {g["让球正确"]}({acc_rang:.0f}%)')
    print(f'  实际胜: {g["胜"]} | 实际平: {g["平"]} | 实际负: {g["负"]}')

# 全部比赛统计
print('\n' + '='*80)
print('Notion所有比赛 - 按竞彩预测+步26分组统计')
print('='*80)

groups_all = defaultdict(lambda: {'total': 0, '竞彩正确': 0, '让球正确': 0, '胜': 0, '平': 0, '负': 0})
for m in all_matches:
    if not m['score']: continue
    key = f"竞彩:{m['pred']} | 步26:{m['step26']}"
    groups_all[key]['total'] += 1
    if m['pred_correct']: groups_all[key]['竞彩正确'] += 1
    if m['rang_correct']: groups_all[key]['让球正确'] += 1
    if ':' in m['score']:
        hs, as_ = map(int, m['score'].split(':'))
        if hs > as_: groups_all[key]['胜'] += 1
        elif hs < as_: groups_all[key]['负'] += 1
        else: groups_all[key]['平'] += 1

for key in sorted(groups_all.keys(), key=lambda k: -groups_all[k]['total']):
    g = groups_all[key]
    acc_pred = g['竞彩正确'] / g['total'] * 100 if g['total'] > 0 else 0
    acc_rang = g['让球正确'] / g['total'] * 100 if g['total'] > 0 else 0
    print(f'\n{key}')
    print(f'  总: {g["total"]} | 竞彩正确: {g["竞彩正确"]}({acc_pred:.0f}%) | 让球正确: {g["让球正确"]}({acc_rang:.0f}%)')
    print(f'  实际胜: {g["胜"]} | 实际平: {g["平"]} | 实际负: {g["负"]}')

# 汇总
print('\n' + '='*80)
print('汇总')
print('='*80)

# 5月10日汇总
total_510 = len(may10_matches)
correct_510 = sum(1 for m in may10_matches if m['pred_correct'])
rang_correct_510 = sum(1 for m in may10_matches if m['rang_correct'])
print(f'\n5月10日: {total_510}场 | 竞彩正确: {correct_510}({correct_510/total_510*100:.0f}%) | 让球正确: {rang_correct_510}({rang_correct_510/total_510*100:.0f}%)')

# 全部汇总
all_with_score = [m for m in all_matches if m['score']]
total_all = len(all_with_score)
correct_all = sum(1 for m in all_with_score if m['pred_correct'])
rang_correct_all = sum(1 for m in all_with_score if m['rang_correct'])
print(f'全部: {total_all}场 | 竞彩正确: {correct_all}({correct_all/total_all*100:.0f}%) | 让球正确: {rang_correct_all}({rang_correct_all/total_all*100:.0f}%)')
