# -*- coding: utf-8 -*-
"""
调试 step8 历史比赛为空的根因
测试 match10_赫塔费__马洛卡（西甲，fid=1216111）
"""
import requests, json, os, re
from bs4 import BeautifulSoup
import time

meta_path = 'jingcai/tasks/2026-05-12/data/match10_赫塔费__马洛卡/meta.json'
with open(meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)

home_id = meta.get('home_id', '')
away_id = meta.get('away_id', '')
league = meta.get('league', '')
fid = meta.get('fid', '')

print('主队ID: %s' % home_id)
print('客队ID: %s' % away_id)
print('联赛: %s' % league)
print('FID: %s' % fid)
print()

sess = requests.Session()

# 1. 获取联赛球队（西甲ID=19496）
league_id = '19496'
url = 'https://liansai.500.com/zuqiu-%s/' % league_id
print('Step 1: 获取联赛球队...')
print('URL: %s' % url)
try:
    resp = sess.get(url, timeout=15)
    resp.encoding = 'gbk'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    team_ids = set()
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        m = re.search(r'/team/(\d+)', href)
        if m and '/teamfixture/' not in href:
            team_ids.add(m.group(1))
    
    print('联赛球队: %d 支' % len(team_ids))
    
except Exception as e:
    print('Error: %s' % str(e))
    team_ids = {home_id, away_id}

# 2. 获取前3支球队的赛程
print('\nStep 2: 获取球队赛程...')
all_matches = []
for team_id in sorted(list(team_ids))[:3]:
    url = 'https://liansai.500.com/team/%s/teamfixture/' % team_id
    try:
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        src_leagues = set()
        match_count = 0
        for tr in soup.find_all('tr', attrs={'data': True}):
            try:
                data = json.loads(tr.get('data', '{}'))
                name = data.get('SIMPLEGBNAME', '')
                if name:
                    src_leagues.add(name)
                match_count += 1
            except:
                continue
        
        all_matches.extend(src_leagues)
        print('  球队%s: %d场比赛, 联赛名: %s' % (team_id, match_count, src_leagues))
        time.sleep(0.5)
    except Exception as e:
        print('  球队%s: Error: %s' % (team_id, str(e)))

# 3. 检查联赛名匹配
print('\nStep 3: 检查联赛名匹配...')
print('竞彩联赛: "%s"' % league)
print('源站联赛: %s' % set(all_matches))

# 检查匹配
for src in set(all_matches):
    # league_mapper.py 的逻辑
    m = {
        '西甲': ['西甲'],
    }
    
    if src == league:
        print('  ✅ 精确匹配: "%s" == "%s"' % (src, league))
    elif len(league) >= 2 and league in src:
        print('  ✅ 包含匹配: "%s" in "%s"' % (league, src))
    elif len(src) >= 2 and src in league:
        print('  ✅ 包含匹配: "%s" in "%s"' % (src, league))
    else:
        print('  ❌ 不匹配: "%s" != "%s"' % (src, league))
