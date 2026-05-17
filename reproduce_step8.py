# -*- coding: utf-8 -*-
"""
复现 step8_1923_extractor.py 的完整流程
测试 match10_赫塔费__马洛卡
"""
import requests, json, os, re
from bs4 import BeautifulSoup
import time

meta_path = 'jingcai/tasks/2026-05-12/data/match10_赫塔费__马洛卡/meta.json'
with open(meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)

HOME_ID = meta.get('home_id', '')
AWAY_ID = meta.get('away_id', '')
LEAGUE = meta.get('league', '')
FID = meta.get('fid', '')
MACAU_LINE = meta.get('macau_line', '')

LEAGUE_ID_MAP = {
    '西甲': '19496',
    '英超': '19495',
    '意甲': '19497',
    '德甲': '19498',
    '法甲': '19499',
    '荷甲': '19500',
    '葡超': '19503',
    '韩职': '19524',
    '挪超': '19509',
}

def league_match(src, target):
    if src == target: return True
    if not src or not target: return False
    if len(target) >= 2 and target in src: return True
    if len(src) >= 2 and src in target: return True
    return False

sess = requests.Session()
results = []

# Step 1: 获取联赛球队
league_id = LEAGUE_ID_MAP.get(LEAGUE, '')
results.append('Step 1: Get league teams')
results.append('  LEAGUE: %s' % LEAGUE)
results.append('  league_id: %s' % league_id)

team_ids = set()
if league_id:
    url = 'https://liansai.500.com/zuqiu-%s/' % league_id
    try:
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            m = re.search(r'/team/(\d+)', href)
            if m and '/teamfixture/' not in href:
                team_ids.add(m.group(1))
    except Exception as e:
        results.append('  Error: %s' % str(e))

results.append('  team_ids: %d teams' % len(team_ids))
results.append('  sample: %s' % str(sorted(list(team_ids))[:5]))

# Step 2: 获取所有球队赛程
results.append('')
results.append('Step 2: Get team fixtures')
all_matches = []
for i, team_id in enumerate(sorted(list(team_ids))[:5], 1):  # only first 5
    url = 'https://liansai.500.com/team/%s/teamfixture/' % team_id
    try:
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        count = 0
        for tr in soup.find_all('tr', attrs={'data': True}):
            try:
                data = json.loads(tr.get('data', '{}'))
                all_matches.append(data)
                count += 1
            except:
                continue
        results.append('  team %s: %d matches' % (team_id, count))
    except:
        pass
    time.sleep(0.2)

results.append('  Total records: %d' % len(all_matches))

# Step 3: 筛选同联赛
results.append('')
results.append('Step 3: Filter by league')
league_matches = []
seen_fid = set()
for d in all_matches:
    src_name = d.get('SIMPLEGBNAME', '')
    fid = str(d.get('FIXTUREID', ''))
    if fid in seen_fid:
        continue
    seen_fid.add(fid)
    
    if league_match(src_name, LEAGUE):
        league_matches.append(d)

results.append('  league_matches: %d (after dedup)' % len(league_matches))

# 显示前3场
for m in league_matches[:3]:
    date = m.get('MATCHDATE', '')
    home = m.get('HOMETEAMSXNAME', '')
    away = m.get('AWAYTEAMSXNAME', '')
    result = m.get('lpl_on', '')
    fid = m.get('FIXTUREID', '')
    results.append('  %s %s vs %s (%s) fid=%s' % (date, home, away, result, fid))

if len(league_matches) == 0:
    # 检查源站返回的联赛名
    results.append('')
    results.append('DEBUG: Source league names:')
    src_names = set()
    for d in all_matches:
        src_names.add(d.get('SIMPLEGBNAME', ''))
    results.append('  %s' % str(sorted(list(src_names))))

with open('jingcai/full_step8_debug.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done - see jingcai/full_step8_debug.txt')
