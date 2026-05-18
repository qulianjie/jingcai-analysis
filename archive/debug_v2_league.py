# -*- coding: utf-8 -*-
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests, re
from bs4 import BeautifulSoup

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

# Get韩职球队列表 from league page
url = 'https://liansai.500.com/zuqiu-19554/'
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')
team_ids = set()
for a in soup.find_all('a', href=True):
    href = a.get('href', '')
    m = re.search(r'/team/(\d+)', href)
    if m and '/teamfixture/' not in href:
        team_ids.add(m.group(1))

print(f"联赛页球队ID: {sorted(team_ids)}")

# Get fixtures for these teams
all_data = []
for tid in sorted(team_ids):
    url = f'https://liansai.500.com/team/{tid}/teamfixture/'
    resp = sess.get(url, timeout=15)
    resp.encoding = 'gbk'
    soup = BeautifulSoup(resp.text, 'html.parser')
    for tr in soup.find_all('tr', attrs={'data': True}):
        try:
            all_data.append(json.loads(tr.get('data', '{}')))
        except: pass
    time.sleep(0.1)

print(f"总记录: {len(all_data)}")

# Filter for韩职
current_fids = {'1373089', '1373138', '1373122'}  # 3韩职比赛FIDs
league_data = []
for d in all_data:
    fid = str(d.get('FIXTUREID', ''))
    if fid in current_fids: continue
    sn = d.get('SIMPLEGBNAME', '')
    if sn == 'K1联赛':
        hcp = (d.get('HANDICAPLINENAME') or '').replace('升','').replace('降','').strip()
        if hcp:
            league_data.append({'fid': fid, 'hcp': hcp, 'home': d.get('HOMETEAMSXNAME',''), 'away': d.get('AWAYTEAMSXNAME',''), 'date': d.get('MATCHDATE','')})

print(f"同联赛(去当前): {len(league_data)}")

# Check handicap distribution
hcp_count = {}
for d in league_data:
    h = d['hcp']
    hcp_count[h] = hcp_count.get(h, 0) + 1

print("盘口分布:")
for h, count in sorted(hcp_count.items(), key=lambda x: -x[1]):
    print(f"  {repr(h)}: {count}场")

# Check for '球半' matches
print(f"\n'球半' matches: {hcp_count.get('球半', 0)}场")
if hcp_count.get('球半', 0) > 0:
    for d in league_data:
        if d['hcp'] == '球半':
            print(f"  {d['date']} {d['home']}vs{d['away']} FID={d['fid']}")
