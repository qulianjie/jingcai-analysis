import json
import requests
import re
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

API_KEY = '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'
DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'

# 从 500.com 移动端解析的比分
# 格式: 主队 数字X 数字Y -> 比分 = X的第一位 : Y的第一位
# 例: 蔚山HD [3]11 富川FC [11]00 -> 1:0
#     大阪钢巴 00 广岛三箭 01 -> 0:1
SCORES = {
    '周日001': '1:0', '周日002': '0:1', '周日003': '1:0', '周日004': '0:2',
    '周日005': '0:1', '周日006': '2:0', '周日007': '1:1', '周日008': '2:0',
    '周日009': '1:1', '周日010': '1:1', '周日011': '0:1', '周日012': '1:2',
    '周日013': '0:0', '周日014': '1:1', '周日015': '0:1', '周日016': '0:1',
    '周日017': '0:2', '周日018': '1:0', '周日019': '0:1', '周日020': '1:2',
    '周日021': '1:3', '周日022': '2:0', '周日023': '0:1', '周日024': '1:0',
    '周日025': '0:2', '周日026': '2:0', '周日027': '1:1', '周日028': '0:0',
    '周日029': '0:1', '周日030': '2:0',
}

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json',
}

# Query Notion
data = json.dumps({
    'filter': {'and': [{'property': '比赛日期', 'date': {'equals': '2026-05-10'}}]},
    'page_size': 100
})
r = requests.post(f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=HEADERS, data=data)
pages = r.json()['results']
print(f'Notion中找到 {len(pages)} 场比赛\n')

# Build map
page_map = {}
for p in pages:
    name = p['properties']['Name']['title'][0]['plain_text']
    m = re.match(r'(周[一二三四五六日]\d+)', name)
    if m:
        page_map[m.group(1)] = p

# Update all 30
print('=== 更新30场比分 ===')
updated = 0
for mn in sorted(SCORES.keys()):
    page = page_map.get(mn)
    if not page:
        print(f'  {mn}: NOT FOUND')
        continue
    score = SCORES[mn]
    hs, as_ = map(int, score.split(':'))
    if hs > as_: ar = '胜'
    elif hs < as_: ar = '负'
    else: ar = '平'
    
    props = {
        '实际比分': {'rich_text': [{'text': {'content': score}}]},
        '实际结果': {'rich_text': [{'text': {'content': ar}}]},
        '反馈日期': {'date': {'start': '2026-05-11'}},
    }
    r = requests.patch(f'https://api.notion.com/v1/pages/{page["id"]}', headers=HEADERS, data=json.dumps({'properties': props}))
    if r.status_code == 200:
        print(f'  {mn}: {score} ({ar}) OK')
        updated += 1
    else:
        print(f'  {mn}: FAIL {r.status_code}')

# Verify
print(f'\n=== 验证 {updated}/30 ===')
r = requests.post(f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=HEADERS, data=json.dumps({
    'filter': {'and': [{'property': '比赛日期', 'date': {'equals': '2026-05-10'}}]},
    'page_size': 100
}))
pages2 = r.json()['results']
pm2 = {}
for p in pages2:
    name = p['properties']['Name']['title'][0]['plain_text']
    m = re.match(r'(周[一二三四五六日]\d+)', name)
    if m:
        pm2[m.group(1)] = p

ok = 0
for mn in sorted(SCORES.keys()):
    page = pm2.get(mn)
    if not page: continue
    cur = page['properties']['实际比分']['rich_text'][0]['plain_text'] if page['properties']['实际比分']['rich_text'] else '(空)'
    if cur == SCORES[mn]: ok += 1
    else: print(f'  {mn}: expected={SCORES[mn]} got={cur}')
print(f'{ok}/30 正确')
