# -*- coding: utf-8 -*-
import sys, requests, json, re
from bs4 import BeautifulSoup
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

# 欧冠 - 从联赛页获取的球队ID
ucl_ids = ['21767','81937','42878','17429','44043','42966','20935','15881','22587','43045','21877']
print("=== 欧冠球队测试 ===")
for tid in ucl_ids[:3]:
    url = f'https://liansai.500.com/team/{tid}/teamfixture/'
    r = sess.get(url, timeout=15)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, 'html.parser')
    names = set()
    for tr in soup.find_all('tr', attrs={'data': True}):
        try:
            d = json.loads(tr.get('data', '{}'))
            names.add(d.get('SIMPLEGBNAME', ''))
        except: pass
    print(f"  {tid}: {names}")

# 解放者杯
lib_ids = ['7521','3563','4487','14155','15501','89464','4502','4443']
print("\n=== 解放者杯球队测试 ===")
for tid in lib_ids[:3]:
    url = f'https://liansai.500.com/team/{tid}/teamfixture/'
    r = sess.get(url, timeout=15)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, 'html.parser')
    names = set()
    for tr in soup.find_all('tr', attrs={'data': True}):
        try:
            d = json.loads(tr.get('data', '{}'))
            names.add(d.get('SIMPLEGBNAME', ''))
        except: pass
    print(f"  {tid}: {names}")

# 沙特 - 从联赛页获取
print("\n=== 沙特联赛页测试 ===")
url = 'https://liansai.500.com/zuqiu-19506/'
r = sess.get(url, timeout=15)
r.encoding = 'gbk'
soup = BeautifulSoup(r.text, 'html.parser')
team_ids = set()
for a in soup.find_all('a', href=True):
    href = a.get('href', '')
    m = re.search(r'/team/(\d+)', href)
    if m and '/teamfixture/' not in href:
        team_ids.add(m.group(1))
print(f"  提取球队ID: {team_ids}")

# 测试提取的球队
for tid in list(team_ids)[:3]:
    url = f'https://liansai.500.com/team/{tid}/teamfixture/'
    r = sess.get(url, timeout=15)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, 'html.parser')
    names = set()
    for tr in soup.find_all('tr', attrs={'data': True}):
        try:
            d = json.loads(tr.get('data', '{}'))
            names.add(d.get('SIMPLEGBNAME', ''))
        except: pass
    print(f"  {tid}: {names}")
