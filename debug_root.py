# -*- coding: utf-8 -*-
import requests, json, os, re
from bs4 import BeautifulSoup
import time

meta_path = 'jingcai/tasks/2026-05-12/data/match10_赫塔费__马洛卡/meta.json'
with open(meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)

home_id = meta.get('home_id', '')
league = meta.get('league', '')
fid = meta.get('fid', '')

results = []
results.append('home_id: %s' % home_id)
results.append('league: %s' % league)
results.append('fid: %s' % fid)

sess = requests.Session()

# 获取主队赛程
url = 'https://liansai.500.com/team/%s/teamfixture/' % home_id
results.append('url: %s' % url)

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
    
    results.append('match_count: %d' % match_count)
    results.append('src_leagues: %s' % str(sorted(list(src_leagues))))
    
    # 检查匹配
    matched = False
    for src in src_leagues:
        if src == league:
            results.append('MATCH_EXACT: "%s" == "%s"' % (src, league))
            matched = True
        elif len(league) >= 2 and league in src:
            results.append('MATCH_CONTAINS: "%s" in "%s"' % (league, src))
            matched = True
    
    if not matched:
        results.append('NO MATCH FOUND')
        results.append('league: "%s"' % league)
        results.append('src_leagues: %s' % str(sorted(list(src_leagues))))

except Exception as e:
    results.append('Error: %s' % str(e))

with open('jingcai/debug_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done - see jingcai/debug_result.txt')
