# -*- coding: utf-8 -*-
"""
验证西甲的正确联赛ID
方法：从赫塔费的赛程中找西甲的联赛ID
"""
import requests, json, os, re
from bs4 import BeautifulSoup

home_id = '838'  # 赫塔费
url = 'https://liansai.500.com/team/%s/teamfixture/' % home_id

print('获取赫塔费赛程: %s' % url)

sess = requests.Session()
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')

# 从链接中提取联赛ID
league_ids = {}
for a in soup.find_all('a', href=True):
    href = a.get('href', '')
    # 格式: /zuqiu-19496/ 或类似的
    m = re.search(r'/zuqiu-(\d+)/', href)
    if m:
        lid = m.group(1)
        text = a.get_text().strip()
        if lid not in league_ids:
            league_ids[lid] = set()
        league_ids[lid].add(text)

print('从赛程页面找到的联赛ID:')
for lid, names in sorted(league_ids.items()):
    print('  %s: %s' % (lid, names))

# 检查西甲的联赛ID
print('\n西甲应该在哪个ID下?')
print('LEAGUE_ID_MAP 中: 西甲 -> 19496')

# 验证19496的页面
print('\n验证 /zuqiu-19496/:')
url = 'https://liansai.500.com/zuqiu-19496/'
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')

# 获取页面标题
title = soup.find('title')
if title:
    print('  页面标题: %s' % title.get_text().strip())

# 获取所有球队
team_ids = set()
for a in soup.find_all('a', href=True):
    href = a.get('href', '')
    m = re.search(r'/team/(\d+)', href)
    if m and '/teamfixture/' not in href:
        team_ids.add(m.group(1))

print('  球队数: %d' % len(team_ids))
print('  包含838: %s' % ('838' in team_ids))

# 如果838不在19496下，找包含838的联赛
if '838' not in team_ids:
    print('\n838 不在19496下，尝试从赛程直接获取联赛ID...')
    # 从赛程链接中提取
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        if '/team/838/' in href:
            print('  找到838链接: %s' % href)
