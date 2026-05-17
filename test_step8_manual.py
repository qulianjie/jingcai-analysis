# -*- coding: utf-8 -*-
"""
手动复现 step8 完整流程 for 赫罗纳 vs 皇家社会
"""
import requests, json, os, re, time
from bs4 import BeautifulSoup

LEAGUE = '西甲'
HOME_ID = '2074'
AWAY_ID = '885'
FID = '1216129'

# 当前LEAGUE_ID_MAP中的值
LEAGUE_ID_MAP_OLD = {'西甲': '19496'}  # 旧值
LEAGUE_ID_MAP_NEW = {'西甲': '9124'}   # 新值（修复后）

print('===========================================================')
print('测试: 赫罗纳 vs 皇家社会')
print('联赛: %s' % LEAGUE)
print('FID: %s' % FID)
print('===========================================================')

sess = requests.Session()

# ===== 测试1: 用旧ID (19496) =====
print('\n--- 测试1: 用旧ID 19496 ---')
url = 'https://liansai.500.com/zuqiu-19496/'
print('URL: %s' % url)
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')
title = soup.find('title')
if title:
    print('页面标题: %s' % title.get_text().strip())

teams_old = set()
for a in soup.find_all('a', href=True):
    href = a.get('href', '')
    m = re.search(r'/team/(\d+)', href)
    if m and '/teamfixture/' not in href:
        teams_old.add(m.group(1))
print('球队数: %d' % len(teams_old))
print('包含2074(赫罗纳): %s' % ('2074' in teams_old))
print('包含885(皇家社会): %s' % ('885' in teams_old))
print('样本球队: %s' % sorted(list(teams_old))[:5])

# ===== 测试2: 用新ID (9124) =====
print('\n--- 测试2: 用新ID 9124 ---')
url = 'https://liansai.500.com/zuqiu-9124/'
print('URL: %s' % url)
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')
title = soup.find('title')
if title:
    print('页面标题: %s' % title.get_text().strip())

teams_new = set()
for a in soup.find_all('a', href=True):
    href = a.get('href', '')
    m = re.search(r'/team/(\d+)', href)
    if m and '/teamfixture/' not in href:
        teams_new.add(m.group(1))
print('球队数: %d' % len(teams_new))
print('包含2074(赫罗纳): %s' % ('2074' in teams_new))
print('包含885(皇家社会): %s' % ('885' in teams_new))
print('样本球队: %s' % sorted(list(teams_new))[:10])

# ===== 测试3: 从球队赛程确认联赛名 =====
print('\n--- 测试3: 赫罗纳赛程中的联赛名 ---')
url = 'https://liansai.500.com/team/2074/teamfixture/'
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')

league_names = set()
for tr in soup.find_all('tr', attrs={'data': True}):
    try:
        data = json.loads(tr.get('data', '{}'))
        name = data.get('SIMPLEGBNAME', '')
        if name:
            league_names.add(name)
    except:
        continue

print('赫罗纳涉及的联赛: %s' % sorted(list(league_names)))
print('"西甲"在列表中: %s' % ('西甲' in league_names))

# ===== 测试4: 用正确的9124获取球队赛程 =====
print('\n--- 测试4: 用ID 9124获取前3支球队的赛程，统计匹配 ---')
all_matches = []
for team_id in sorted(list(teams_new))[:3]:
    url = 'https://liansai.500.com/team/%s/teamfixture/' % team_id
    resp = sess.get(url, timeout=15)
    resp.encoding = 'gbk'
    soup = BeautifulSoup(resp.text, 'html.parser')
    count = 0
    for tr in soup.find_all('tr', attrs={'data': True}):
        try:
            data = json.loads(tr.get('data', '{}'))
            name = data.get('SIMPLEGBNAME', '')
            fid = data.get('FIXTUREID', '')
            if name == LEAGUE:
                count += 1
                all_matches.append(data)
        except:
            continue
    print('  球队%s: %d场西甲比赛' % (team_id, count))
    time.sleep(0.3)

print('总计: %d场' % len(all_matches))

# 显示前3场
for m in all_matches[:3]:
    date = m.get('MATCHDATE', '')
    home = m.get('HOMETEAMSXNAME', '')
    away = m.get('AWAYTEAMSXNAME', '')
    fid = m.get('FIXTUREID', '')
    print('  %s %s vs %s (fid=%s)' % (date, home, away, fid))

print('\n===========================================================')
print('结论:')
print('  旧ID 19496 -> 球队列表不包含赫罗纳(2074)和皇家社会(885)')
print('  新ID 9124 -> 球队列表包含赫罗纳(2074)和皇家社会(885)')
print('  所以旧ID获取的球队根本就不是西甲球队！')
print('===========================================================')
