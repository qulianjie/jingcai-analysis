# -*- coding: utf-8 -*-
"""
验证西甲联赛ID是否正确
"""
import requests, json, os, re
from bs4 import BeautifulSoup

# 测试西甲ID=19496
league_id = '19496'
url = 'https://liansai.500.com/zuqiu-%s/' % league_id

print('URL: %s' % url)

sess = requests.Session()
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')

# 获取所有球队
team_ids = set()
team_names = {}
for a in soup.find_all('a', href=True):
    href = a.get('href', '')
    m = re.search(r'/team/(\d+)', href)
    if m and '/teamfixture/' not in href:
        tid = m.group(1)
        team_ids.add(tid)
        team_names[tid] = a.get_text().strip()

print('球队数: %d' % len(team_ids))
print('前5支球队:')
for tid in sorted(list(team_ids))[:5]:
    print('  %s: %s' % (tid, team_names.get(tid, '?')))

# 获取赫塔费的球队ID（应该是838）
print('\n赫塔费ID: 838')
print('赫塔费名称: %s' % team_names.get('838', 'NOT FOUND'))

# 检查838是否在球队列表中
if '838' in team_ids:
    print('838 在球队列表中')
else:
    print('838 不在球队列表中!')
    print('球队列表: %s' % sorted(list(team_ids)))
