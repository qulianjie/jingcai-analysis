# -*- coding: utf-8 -*-
"""
用正确的联赛ID重新测试 step8
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

# 正确的联赛ID（从球队赛程提取）
CORRECT_LEAGUE_ID_MAP = {
    '西甲': '9124',
    '英超': '9110',
    '意甲': '9116',
    '德甲': '9119',
    '法甲': '9122',
    '荷甲': '9125',
    '葡超': '9128',
    '韩职': '9131',
    '挪超': '9134',
}

def league_match(src, target):
    if src == target: return True
    if not src or not target: return False
    if len(target) >= 2 and target in src: return True
    if len(src) >= 2 and src in target: return True
    return False

sess = requests.Session()
results = []

# 用正确的联赛ID
league_id = CORRECT_LEAGUE_ID_MAP.get(LEAGUE, '')
results.append('LEAGUE: %s' % LEAGUE)
results.append('league_id: %s (corrected)' % league_id)

# 获取联赛球队
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
        results.append('Error: %s' % str(e))

results.append('team_ids: %d teams' % len(team_ids))
results.append('contains %s: %s' % (HOME_ID, HOME_ID in team_ids))
results.append('contains %s: %s' % (AWAY_ID, AWAY_ID in team_ids))

# 获取所有球队赛程
all_matches = []
for i, team_id in enumerate(sorted(list(team_ids)), 1):
    url = 'https://liansai.500.com/team/%s/teamfixture/' % team_id
    try:
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tr in soup.find_all('tr', attrs={'data': True}):
            try:
                data = json.loads(tr.get('data', '{}'))
                all_matches.append(data)
            except:
                continue
    except:
        pass
    time.sleep(0.2)

results.append('Total records: %d' % len(all_matches))

# 筛选同联赛
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

results.append('league_matches: %d (after dedup)' % len(league_matches))

# 显示前3场
for m in league_matches[:3]:
    date = m.get('MATCHDATE', '')
    home = m.get('HOMETEAMSXNAME', '')
    away = m.get('AWAYTEAMSXNAME', '')
    result = m.get('lpl_on', '')
    fid = m.get('FIXTUREID', '')
    results.append('  %s %s vs %s (%s) fid=%s' % (date, home, away, result, fid))

with open('jingcai/correct_league_id_test.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done - see jingcai/correct_league_id_test.txt')
