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

# 从500.com移动端获取5月10日比分
scores_url = 'https://live.m.500.com/home/zq/jczq/2026-05-10'
r = requests.get(scores_url, headers={'User-Agent': 'Mozilla/5.0'})
html = r.text

# 解析比分
import re
matches_500 = re.findall(r'周日(\d+).*?完场\s+(\d):(\d)', html)
scores = {}
for m in matches_500:
    num = f'周日{m[0]}'
    score = f'{m[1]}:{m[2]}'
    scores[num] = score

print(f'从500.com获取到 {len(scores)} 场比分')
for k in sorted(scores.keys()):
    print(f'  {k}: {scores[k]}')

# 查询Notion中5月10日的比赛
r = requests.post(f'https://api.notion.com/v1/databases/{DB_ID}/query', headers=HEADERS, data=json.dumps({
    'filter': {
        'and': [
            {'property': '比赛日期', 'date': {'equals': '2026-05-10'}},
            {'property': '比赛', 'rich_text': {'is_not_empty': True}}
        ]
    },
    'page_size': 100
}))
pages = r.json()['results']
print(f'\nNotion中5月10日比赛: {len(pages)} 场')

if len(pages) == 0:
    print('⚠️ 5月10日比赛不在Notion中！')
    print('需要先从竞彩任务目录同步比赛信息')
    
    # 检查任务目录
    import os
    task_dir = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-10'
    if os.path.exists(task_dir):
        files = [f for f in os.listdir(task_dir) if f.endswith('.md')]
        print(f'任务目录中有 {len(files)} 场比赛')
        for f in sorted(files)[:5]:
            print(f'  {f}')
    else:
        print(f'任务目录不存在: {task_dir}')
else:
    # 更新比分
    print('\n更新比分...')
    for p in pages:
        name = p['properties']['Name']['title'][0]['plain_text']
        m = re.match(r'(周[一二三四五六日]\d+)', name)
        if not m: continue
        mn = m.group(1)
        if mn not in scores: continue
        
        score = scores[mn]
        hs, as_ = map(int, score.split(':'))
        if hs > as_: ar = '胜'
        elif hs < as_: ar = '负'
        else: ar = '平'
        
        props = {
            '实际比分': {'rich_text': [{'text': {'content': score}}]},
            '实际结果': {'rich_text': [{'text': {'content': ar}}]},
            '反馈日期': {'date': {'start': '2026-05-11'}},
        }
        r = requests.patch(f'https://api.notion.com/v1/pages/{p["id"]}', headers=HEADERS, data=json.dumps({'properties': props}))
        if r.status_code == 200:
            print(f'  {mn}: {score} ({ar}) OK')
        else:
            print(f'  {mn}: FAIL {r.status_code}')
