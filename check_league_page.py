# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests, json
from bs4 import BeautifulSoup

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
})

# Check韩职联赛页面
url = 'https://liansai.500.com/zuqiu-19554/'
print(f"Fetching: {url}")
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
print(f"Status: {resp.status_code}, Size: {len(resp.text)}")

soup = BeautifulSoup(resp.text, 'html.parser')

# Check for tr[data]
trs = soup.find_all('tr', attrs={'data': True})
print(f"tr[data] count: {len(trs)}")

# Check for any tables
tables = soup.find_all('table')
print(f"Tables: {len(tables)}")

# Check for team links
team_links = set()
for a in soup.find_all('a', href=True):
    href = a.get('href', '')
    if '/team/' in href and 'teamfixture' not in href:
        m = __import__('re').search(r'/team/(\d+)', href)
        if m:
            team_links.add(m.group(1))
print(f"Team links found: {len(team_links)}")
if team_links:
    print(f"Sample: {list(team_links)[:5]}")

# Also try team fixture page directly
print("\n\n=== Team fixture: 全北现代 (1609) ===")
url2 = 'https://liansai.500.com/team/1609/teamfixture/'
resp2 = sess.get(url2, timeout=15)
resp2.encoding = 'gbk'
print(f"Status: {resp2.status_code}, Size: {len(resp2.text)}")

soup2 = BeautifulSoup(resp2.text, 'html.parser')
trs2 = soup2.find_all('tr', attrs={'data': True})
print(f"tr[data] count: {len(trs2)}")

if trs2:
    # Show first record
    try:
        data = json.loads(trs2[0].get('data', '{}'))
        print(f"First record: {json.dumps(data, ensure_ascii=False)[:300]}")
    except:
        print(f"First record raw: {trs2[0].get('data', '')[:200]}")
