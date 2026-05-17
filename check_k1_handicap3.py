# -*- coding: utf-8 -*-
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

# Check韩职所有球队的HANDICAPLINENAME分布
all_team_ids = ['1609', '1608', '1606', '1603', '1611', '1612', '1605', '1604', '1607', '5739', '4544', '6477']
hcp_count = {}
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
                    hcp_count[hcp] = hcp_count.get(hcp, 0) + 1
        except: pass
    time.sleep(0.1)

print("韩职K1联赛各盘口出现次数:")
for hcp, count in sorted(hcp_count.items(), key=lambda x: -x[1]):
    print(f"  {hcp}: {count}场")

# Check other leagues' team IDs from league page
print("\n\n=== 检查各联赛页的球队链接 ===")
league_ids = {
    '芬超': '19510',
    '荷乙': '19502',
    '沙特': '19506',
    '欧冠': '19538',
    '解放者杯': '19546',
}

for name, lid in league_ids.items():
    url = f'https://liansai.500.com/zuqiu-{lid}/'
    resp = sess.get(url, timeout=15)
    resp.encoding = 'gbk'
    soup = BeautifulSoup(resp.text, 'html.parser')
    team_ids = set()
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        m = __import__('re').search(r'/team/(\d+)', href)
        if m and '/teamfixture/' not in href:
            team_ids.add(m.group(1))
    print(f"{name} ({lid}): {len(team_ids)} teams - {sorted(team_ids)}")
