# -*- coding: utf-8 -*-
"""
调试：查看一个失败match的历史比赛数据中的联赛名
"""
import requests, json, os, re
from bs4 import BeautifulSoup

# 测试match10_赫塔费__马洛卡（西甲，fid=1373117）
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

# 获取主队赛程
sess = requests.Session()
url = 'https://liansai.500.com/team/%s/teamfixture/' % home_id
print('获取主队赛程: %s' % url)
try:
    resp = sess.get(url, timeout=15)
    resp.encoding = 'gbk'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # 收集所有联赛名
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
    
    print('比赛数: %d' % match_count)
    print('源站联赛名: %s' % src_leagues)
    print()
    
    # 检查是否匹配
    match_found = False
    for src in src_leagues:
        # 简单的包含匹配
        if league in src or src in league or src == league:
            print('匹配: "%s" == "%s"' % (league, src))
            match_found = True
    
    if not match_found:
        print('*** 不匹配! ***')
        print('竞彩联赛: "%s"' % league)
        print('源站联赛: %s' % src_leagues)

except Exception as e:
    print('Error: %s' % str(e))
