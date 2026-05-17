# -*- coding: utf-8 -*-
"""从足彩网获取竞彩足球开奖结果，写入meta.json"""
import os, json, requests

BASE = os.path.join('jingcai', 'tasks')

# 收集所有日期
dates = set()
for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if os.path.isdir(dp):
        data_dir = os.path.join(dp, 'data')
        if os.path.isdir(data_dir):
            dates.add(d)

print(f'需要获取比分的日期: {len(dates)}个')

# 从zgzcw.com获取开奖结果
def fetch_zgzcw_results():
    """从足彩网获取开奖结果"""
    url = 'https://cp.zgzcw.com/dc/getKaijiangFootBall.action'
    try:
        resp = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://cp.zgzcw.com/',
        }, timeout=15)
        resp.encoding = 'utf-8'
        return resp.text
    except Exception as e:
        print(f'  [ERROR] 获取失败: {e}')
        return None

content = fetch_zgzcw_results()
if not content:
    print('获取开奖结果失败')
    exit()

# 解析HTML
import re

# 找到所有比赛结果行
# 格式: <tr>...周几001...比分...<tr>
rows = re.findall(r'<tr[^>]*>(.*?)</tr>', content, re.DOTALL)

score_map = {}
for row in rows:
    # 提取竞彩编号: 周几001
    num_match = re.search(r'(周[一二三四五六日]\d+)', row)
    if not num_match:
        continue
    match_num = num_match.group(1)
    
    # 提取比分: 比分(半场)列
    # 格式: "1:1 (1:0)" 或 "2:0 (0:0)"
    score_match = re.search(r'(\d{1,2})[：:](\d{1,2})\s*\(\d{1,2}[：:]\d{1,2}\)', row)
    if not score_match:
        continue
    
    home_score = int(score_match.group(1))
    away_score = int(score_match.group(2))
    score_map[match_num] = f'{home_score}:{away_score}'

print(f'获取到 {len(score_map)} 场比赛结果')
for k, v in sorted(score_map.items()):
    print(f'  {k}: {v}')

# 写入meta.json
updated = 0
for d in sorted(dates):
    dp = os.path.join(BASE, d)
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    
    date_updated = 0
    for m in sorted(os.listdir(data_dir)):
        if not m.startswith('match'):
            continue
        meta_path = os.path.join(data_dir, m, 'meta.json')
        if not os.path.exists(meta_path):
            continue
        
        meta = json.load(open(meta_path, 'r', encoding='utf-8'))
        matchnum = meta.get('matchnum', '')
        
        if matchnum in score_map:
            meta['score'] = score_map[matchnum]
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            updated += 1
            date_updated += 1
    
    if date_updated > 0:
        print(f'  {d}: 更新{date_updated}场')

print(f'\n总更新: {updated}场')

# 打印所有比分
print('\n所有比分:')
all_scores = {}
for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    data_dir = os.path.join(dp, 'data')
    if not os.path.isdir(data_dir):
        continue
    for m in sorted(os.listdir(data_dir)):
        if not m.startswith('match'):
            continue
        meta_path = os.path.join(data_dir, m, 'meta.json')
        if os.path.exists(meta_path):
            meta = json.load(open(meta_path, 'r', encoding='utf-8'))
            score = meta.get('score', '')
            matchnum = meta.get('matchnum', '')
            if score and matchnum:
                all_scores[matchnum] = score

for k, v in sorted(all_scores.items()):
    print(f'  {k}: {v}')

print(f'\n总共 {len(all_scores)} 场有比分')
