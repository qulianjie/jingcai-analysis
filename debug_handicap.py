# -*- coding: utf-8 -*-
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

# Get all韩职球队赛程
all_team_ids = ['1609', '1608', '1606', '1603', '1611', '1612', '1605', '1604', '1607', '5739', '4544', '6477']
all_data = []
for tid in all_team_ids:
    url = f'https://liansai.500.com/team/{tid}/teamfixture/'
    resp = sess.get(url, timeout=15)
    resp.encoding = 'gbk'
    soup = BeautifulSoup(resp.text, 'html.parser')
    for tr in soup.find_all('tr', attrs={'data': True}):
        try:
            all_data.append(json.loads(tr.get('data', '{}')))
        except: pass
    time.sleep(0.1)

# Filter for K1联赛
k1_data = []
for d in all_data:
    sn = d.get('SIMPLEGBNAME', '')
    if sn == 'K1联赛':
        k1_data.append(d)

print(f"K1联赛总记录: {len(k1_data)}")

# Check handicap distribution
hcp_count = {}
for d in k1_data:
    hcp = (d.get('HANDICAPLINENAME') or '').replace('升','').replace('降','').strip()
    if hcp:
        hcp_count[hcp] = hcp_count.get(hcp, 0) + 1

print("盘口分布:")
for hcp, count in sorted(hcp_count.items(), key=lambda x: -x[1]):
    print(f"  {repr(hcp)}: {count}场")

# Check if '球半' is in there
if '球半' in hcp_count:
    print(f"\n✅ '球半' exists: {hcp_count['球半']}场")
    
    # Show the 球半 matches
    print("\n球半盘口比赛详情:")
    for d in k1_data:
        hcp = (d.get('HANDICAPLINENAME') or '').replace('升','').replace('降','').strip()
        if hcp == '球半':
            print(f"  {d.get('MATCHDATE','')} {d.get('HOMETEAMSXNAME','')}vs{d.get('AWAYTEAMSXNAME','')} FID={d.get('FIXTUREID','')} hcp={repr(hcp)}")
else:
    print("\n❌ '球半' NOT found")
