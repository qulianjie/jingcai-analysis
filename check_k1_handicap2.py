# -*- coding: utf-8 -*-
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from bs4 import BeautifulSoup

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

# Check韩职所有球队的HANDICAPLINENAME
all_team_ids = ['1609', '1608', '1606', '1603', '1611', '1612', '1605', '1604', '1607', '5739', '4544', '6477']
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

print(f"韩职K1联赛所有HANDICAPLINENAME: {sorted(all_k1_hcps)}")

# Check if '球半' is in there
if '球半' in all_k1_hcps:
    print("✅ '球半' exists in K1联赛 handicaps")
else:
    print("❌ '球半' NOT found in K1联赛 handicaps")

# Check what other leagues have
print("\n\n=== 检查其他联赛的SIMPLEGBNAME ===")
leagues_to_check = {
    '芬超': ['2687'],  # 赫尔辛基火花
    '荷乙': ['2664'],  # 瓦尔韦克
    '沙特': ['692'],   # 利雅得新月
    '欧冠': ['554'],   # 阿森纳
    '解放者杯': ['2271'],  # 水晶体育
}

for league, team_ids in leagues_to_check.items():
    for tid in team_ids:
        url = f'https://liansai.500.com/team/{tid}/teamfixture/'
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        simple_names = set()
        for tr in soup.find_all('tr', attrs={'data': True}):
            try:
                d = json.loads(tr.get('data', '{}'))
                sn = d.get('SIMPLEGBNAME', '')
                if sn:
                    simple_names.add(sn)
            except: pass
        print(f"{league} (team {tid}): SIMPLEGBNAME = {simple_names}")
