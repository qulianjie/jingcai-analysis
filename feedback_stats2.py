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
    
    # 比赛日期
    date_props = p['properties'].get('比赛日期', {})
    date_val = ''
    if date_props.get('date'):
        date_val = date_props['date'].get('start', '')
    
    # 竞彩预测
    pred = p['properties']['竞彩预测']['rich_text'][0]['plain_text'] if p['properties']['竞彩预测']['rich_text'] else ''
    
    # 步26_庄家最看好
    step26 = p['properties'].get('步26_庄家最看好', {})
    step26_val = step26['rich_text'][0]['plain_text'] if step26.get('rich_text') and step26['rich_text'] else ''
    
    # 实际比分
    actual_score = p['properties']['实际比分']['rich_text'][0]['plain_text'] if p['properties']['实际比分']['rich_text'] else ''
    
    # 预测正确 checkbox
    pred_correct = p['properties'].get('预测正确', {}).get('checkbox', False)
    
    m = re.match(r'(周[一二三四五六日]\d+)', name)
    match_num = m.group(1) if m else ''
    
    matches.append({
        'match_num': match_num,
        'name': name,
        'date': date_val,
        'pred': pred,
        'step26': step26_val,
        'score': actual_score,
        'pred_correct': pred_correct,
    })

# 检查日期格式
print('日期格式样本:')
for m in matches[:5]:
    print(f'  {m["name"]} | date={m["date"]} | score={m["score"]}')

# 有比分的比赛
with_score = [m for m in matches if m['score']]
print(f'\n有比分的比赛: {len(with_score)} 场')

# 5月10日比赛
may10 = [m for m in matches if m['date'] == '2026-05-10' or m['date'].startswith('2026-05-10')]
print(f'5月10日比赛: {len(may10)} 场')
if not may10:
    print('  没找到，尝试其他匹配...')
    for m in matches:
        if '05-10' in str(m['date']) or '0510' in m['name'] or '5月10' in m['name']:
            print(f'  可能匹配: {m["name"]} | date={m["date"]}')
