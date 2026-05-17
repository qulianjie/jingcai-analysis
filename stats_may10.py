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
pages = r.json()['results']
print(f'5月10日比赛: {len(pages)} 场\n')

groups = defaultdict(lambda: {'total': 0, '胜': 0, '平': 0, '负': 0})

for p in pages:
    name = p['properties']['Name']['title'][0]['plain_text']
    
    # 竞彩预测 - 只取客胜/平局/主胜，去掉括号
    pred_full = p['properties']['竞彩预测']['rich_text'][0]['plain_text'] if p['properties']['竞彩预测']['rich_text'] else ''
    if '主胜' in pred_full:
        pred = '主胜'
    elif '客胜' in pred_full:
        pred = '客胜'
    elif '平局' in pred_full:
        pred = '平局'
    else:
        pred = '未知'
    
    # 步26_庄家最看好
    step26_val = ''
    s26 = p['properties'].get('步26_庄家最看好', {})
    if s26.get('rich_text') and s26['rich_text']:
        step26_val = s26['rich_text'][0]['plain_text']
    
    # 实际比分
    score = p['properties']['实际比分']['rich_text'][0]['plain_text'] if p['properties']['实际比分']['rich_text'] else ''
    if ':' in score:
        hs, as_ = map(int, score.split(':'))
        if hs > as_: actual = '胜'
        elif hs < as_: actual = '负'
        else: actual = '平'
    else:
        continue
    
    key = f'{pred} + 步26:{step26_val}'
    groups[key]['total'] += 1
    groups[key][actual] += 1

# 按总场次降序
print('5月10日30场 - 竞彩预测(主/客/平) + 步26庄家看好 分组统计\n')
print(f'{"分组":<30} {"总场":>4} {"胜":>4} {"平":>4} {"负":>4}')
print('-' * 50)
for key in sorted(groups.keys(), key=lambda k: -groups[k]['total']):
    g = groups[key]
    print(f'{key:<30} {g["total"]:>4} {g["胜"]:>4} {g["平"]:>4} {g["负"]:>4}')

# 汇总
print('\n' + '=' * 50)
print('汇总')
print('=' * 50)

# 按竞彩预测分组
pred_groups = defaultdict(lambda: {'total': 0, '胜': 0, '平': 0, '负': 0})
for p in pages:
    pred_full = p['properties']['竞彩预测']['rich_text'][0]['plain_text'] if p['properties']['竞彩预测']['rich_text'] else ''
    if '主胜' in pred_full: pred = '主胜'
    elif '客胜' in pred_full: pred = '客胜'
    elif '平局' in pred_full: pred = '平局'
    else: continue
    
    score = p['properties']['实际比分']['rich_text'][0]['plain_text'] if p['properties']['实际比分']['rich_text'] else ''
    if ':' not in score: continue
    hs, as_ = map(int, score.split(':'))
    if hs > as_: actual = '胜'
    elif hs < as_: actual = '负'
    else: actual = '平'
    
    pred_groups[pred]['total'] += 1
    pred_groups[pred][actual] += 1

print('\n按竞彩预测分组:')
for pred in ['主胜', '客胜', '平局']:
    g = pred_groups.get(pred, {'total': 0, '胜': 0, '平': 0, '负': 0})
    print(f'  竞彩{pred}: 总{g["total"]}场 | 实际胜{g["胜"]} 平{g["平"]} 负{g["负"]}')

# 按步26分组
step26_groups = defaultdict(lambda: {'total': 0, '胜': 0, '平': 0, '负': 0})
for p in pages:
    s26 = p['properties'].get('步26_庄家最看好', {})
    step26_val = s26['rich_text'][0]['plain_text'] if s26.get('rich_text') and s26['rich_text'] else '-'
    
    score = p['properties']['实际比分']['rich_text'][0]['plain_text'] if p['properties']['实际比分']['rich_text'] else ''
    if ':' not in score: continue
    hs, as_ = map(int, score.split(':'))
    if hs > as_: actual = '胜'
    elif hs < as_: actual = '负'
    else: actual = '平'
    
    step26_groups[step26_val]['total'] += 1
    step26_groups[step26_val][actual] += 1

print('\n按步26庄家看好分组:')
for key in sorted(step26_groups.keys(), key=lambda k: -step26_groups[k]['total']):
    g = step26_groups[key]
    print(f'  步26:{key}: 总{g["total"]}场 | 实际胜{g["胜"]} 平{g["平"]} 负{g["负"]}')
