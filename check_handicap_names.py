# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
})

# Check HANDICAPLINENAME for 韩职 team fixtures
url = 'https://liansai.500.com/team/1609/teamfixture/'
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'

from bs4 import BeautifulSoup
soup = BeautifulSoup(resp.text, 'html.parser')

handicap_names = set()
for tr in soup.find_all('tr', attrs={'data': True}):
    try:
        d = json.loads(tr.get('data', '{}'))
        if d.get('SIMPLEGBNAME', '') == 'K1联赛':
            hcp = d.get('HANDICAPLINENAME', '')
            if hcp:
                handicap_names.add(hcp)
    except: pass

print("韩职K1联赛 HANDICAPLINENAME values:")
for h in sorted(handicap_names):
    print(f"  '{h}'")

# Check what 澳门亚盘 we extracted
print("\nmeta.json macau_line values:")
import os
data_dir = r'jingcai\tasks\2026-05-05\data'
for d in sorted(os.listdir(data_dir)):
    meta_file = os.path.join(data_dir, d, 'meta.json')
    if os.path.isfile(meta_file):
        with open(meta_file, 'r', encoding='utf-8') as f:
            m = json.load(f)
        print(f"  {m.get('matchnum','')}: '{m.get('macau_line','')}'")
