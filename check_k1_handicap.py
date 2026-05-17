# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

# Check all handicap linename values for K1联赛 matches in team fixtures
url = 'https://liansai.500.com/team/1609/teamfixture/'
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')

hcp_by_league = {}
for tr in soup.find_all('tr', attrs={'data': True}):
    try:
        d = json.loads(tr.get('data', '{}'))
        sn = d.get('SIMPLEGBNAME', '')
        hcp = d.get('HANDICAPLINENAME', '').replace('升','').replace('降','').strip()
        if hcp:
            if sn not in hcp_by_league:
                hcp_by_league[sn] = set()
            hcp_by_league[sn].add(hcp)
    except: pass

print("全北现代(1609) 各联赛的HANDICAPLINENAME:")
for league, hcps in sorted(hcp_by_league.items()):
    print(f"  {league}: {sorted(hcps)}")

# Now check: in the 151 filtered韩职 matches, how many have '球半' handicap?
# Let's get all韩职 handicaps
all_k1_hcps = set()
all_team_ids = ['1609', '1608', '1606', '1603', '1611', '1612', '1605', '1604', '1607', '5739', '4544', '6477']
for tid in all_team_ids:
    url = f'https://liansai.500.com/team/{tid}/teamfixture/'
    resp = sess.get(url, timeout=15)
    resp.encoding = 'gbk'
    soup = BeautifulSoup(resp.text, 'html.parser')
    for tr in soup.find_all('tr', attrs={'data': True}):
        try:
            d = json.loads(tr.get('data', '{}'))
            sn = d.get('SIMPLEGBNAME', '')
            if sn == 'K1联赛':
                hcp = d.get('HANDICAPLINENAME', '').replace('升','').replace('降','').strip()
                if hcp:
                    all_k1_hcps.add(hcp)
        except: pass
    time.sleep(0.1)

import time
all_k1_hcps = set()
for tid in all_team_ids:
    url = f'https://liansai.500.com/team/{tid}/teamfixture/'
    resp = sess.get(url, timeout=15)
    resp.encoding = 'gbk'
    soup = BeautifulSoup(resp.text, 'html.parser')
    for tr in soup.find_all('tr', attrs={'data': True}):
        try:
            d = json.loads(tr.get('data', '{}'))
            sn = d.get('SIMPLEGBNAME', '')
            if sn == 'K1联赛':
                hcp = d.get('HANDICAPLINENAME', '').replace('升','').replace('降','').strip()
                if hcp:
                    all_k1_hcps.add(hcp)
        except: pass
    time.sleep(0.1)

print(f"\n韩职K1联赛所有HANDICAPLINENAME: {sorted(all_k1_hcps)}")
