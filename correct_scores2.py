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

# 从多个搜索结果确认的实际比分
# 来源: live.zgzcw.com (最详细) + vipc.cn
# 之前 reapply_scores4.py 解析500.com移动端HTML有误
CORRECT_SCORES = {
    '周日001': '1:0', '周日002': '0:1', '周日003': '1:0', '周日004': '0:2',
    '周日005': '0:1', '周日006': '3:1', '周日007': '1:1', '周日008': '2:0',
    '周日009': '1:0', '周日010': '2:2', '周日011': '0:0', '周日012': '3:0',
    '周日013': '0:0', '周日014': '1:1', '周日015': '0:1', '周日016': '0:1',
    '周日017': '0:2', '周日018': '1:0', '周日019': '0:1', '周日020': '1:2',
    '周日021': '1:3', '周日022': '2:0', '周日023': '0:1', '周日024': '1:0',
    '周日025': '0:2', '周日026': '2:0', '周日027': '1:1', '周日028': '0:0',
    '周日029': '0:1', '周日030': '2:0',
}

# 之前错误写入的比分
WRONG_SCORES = {
    '周日006': '2:0',   # 实际3:1
    '周日009': '1:1',   # 实际1:0
    '周日010': '1:1',   # 实际2:2
    '周日011': '0:1',   # 实际0:0
    '周日012': '1:2',   # 实际3:0
}

print('=== 差异对比 ===')
for k in sorted(CORRECT_SCORES.keys()):
    if k in WRONG_SCORES:
        print(f'  {k}: 错误={WRONG_SCORES[k]} → 正确={CORRECT_SCORES[k]}')

print(f'\n=== 查询Notion中5月10日30场比赛 ===')

r = requests.post(f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=HEADERS, data=json.dumps({
    'filter': {'property': '比赛日期', 'date': {'equals': '2026-05-10'}},
    'page_size': 100
}))
pages = r.json()['results']
print(f'找到 {len(pages)} 场比赛\n')

page_map = {}
for p in pages:
    name = p['properties']['Name']['title'][0]['plain_text']
    m = re.match(r'(周[一二三四五六日]\d+)', name)
    if m:
        page_map[m.group(1)] = p

# 更新所有比分
print('=== 更新比分 ===')
updated = 0
for mn in sorted(CORRECT_SCORES.keys()):
    page = page_map.get(mn)
    if not page:
        continue
    
    score = CORRECT_SCORES[mn]
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
        if mn in WRONG_SCORES:
            print(f'  {mn}: {WRONG_SCORES[mn]} → {score} ({ar}) ✅ 修正')
        updated += 1
    else:
        print(f'  {mn}: FAIL {r.status_code}')

print(f'\n更新 {updated}/30 场')

# 验证
print('\n=== 验证 ===')
r = requests.post(f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=HEADERS, data=json.dumps({
    'filter': {'property': '比赛日期', 'date': {'equals': '2026-05-10'}},
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
for mn in sorted(CORRECT_SCORES.keys()):
    page = pm2.get(mn)
    if not page: continue
    cur = page['properties']['实际比分']['rich_text'][0]['plain_text'] if page['properties']['实际比分']['rich_text'] else '(空)'
    if cur == CORRECT_SCORES[mn]: ok += 1
    else: print(f'  {mn}: expected={CORRECT_SCORES[mn]} got={cur}')
print(f'{ok}/30 正确')

# 重新计算预测正确
print('\n=== 重新计算预测正确 ===')
correct_count = 0
for mn in sorted(CORRECT_SCORES.keys()):
    page = pm2.get(mn)
    if not page: continue
    score = CORRECT_SCORES[mn]
    pred = page['properties']['竞彩预测']['rich_text'][0]['plain_text'] if page['properties']['竞彩预测']['rich_text'] else ''
    hs, as_ = map(int, score.split(':'))
    if hs > as_: actual_r = '胜'
    elif hs < as_: actual_r = '负'
    else: actual_r = '平'
    
    pred_r = None
    if '主胜' in pred: pred_r = '胜'
    elif '客胜' in pred: pred_r = '负'
    elif '平局' in pred: pred_r = '平'
    
    is_correct = pred_r == actual_r if pred_r else False
    if is_correct: correct_count += 1
    
    props = {
        '预测正确': {'checkbox': is_correct},
    }
    requests.patch(f'https://api.notion.com/v1/pages/{page["id"]}', headers=HEADERS, data=json.dumps({'properties': props}))
    
    mark = '✅' if is_correct else '❌'
    if mn in WRONG_SCORES:
        print(f'  {mark} {mn}: {score} {actual_r} | 竞彩:{pred}→{pred_r} (之前{WRONG_SCORES[mn]})')

print(f'\n竞彩正确: {correct_count}/30 ({correct_count/30*100:.0f}%)')
