import requests
import re
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

API_KEY = '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'
DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'

# 从截图识别的比分
# 第一张图（竖图）：周日001-周日015
# 第二张图（横图）：周日016-周日030（023-030在右侧区域）
#
# 仔细辨认：
# 周日001: 1:0
# 周日002: 0:0 (或0:1)  
# 周日003: 1:1
# 周日004: 3:0
# 周日005: 3:2
# 周日006: 1:0
# 周日007: 0:0
# 周日008: 1:0
# 周日009: 1:1
# 周日010: 3:1
# 周日011: 1:2
# 周日012: 1:1
# 周日013: 1:1
# 周日014: 2:1
# 周日015: 2:1
# 周日016: 0:1
# 周日017: 2:1
# 周日018: 2:2
# 周日019: 1:2
# 周日020: 1:0
# 周日021: 0:2
# 周日022: 0:3
# 周日023: 1:0
# 周日024: 2:1
# 周日025: 2:2
# 周日026: 1:1
# 周日027: 3:1
# 周日028: 1:0
# 周日029: 0:2
# 周日030: 2:1

# 重新仔细辨认两张图片后的比分
# 图片1（竖图）：周日001-周日015 + 周日016-周日022部分
# 图片2（横图）：周日001-周日015 + 比分列

SCORES = {
    '周日001': '1:0', '周日002': '0:0', '周日003': '1:1', '周日004': '3:0',
    '周日005': '3:2', '周日006': '1:0', '周日007': '0:0', '周日008': '1:0',
    '周日009': '1:1', '周日010': '3:1', '周日011': '1:2', '周日012': '1:1',
    '周日013': '1:1', '周日014': '2:1', '周日015': '2:1', '周日016': '0:1',
    '周日017': '2:1', '周日018': '2:2', '周日019': '1:2', '周日020': '1:0',
    '周日021': '0:2', '周日022': '0:3', '周日023': '1:0', '周日024': '2:1',
    '周日025': '2:2', '周日026': '1:1', '周日027': '3:1', '周日028': '1:0',
    '周日029': '0:2', '周日030': '2:1',
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
