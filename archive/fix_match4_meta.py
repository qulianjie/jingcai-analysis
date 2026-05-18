# -*- coding: utf-8 -*-
"""
Fix meta.json for fid=1411377
Current: league='法乙', home='圣埃蒂安', away='罗德兹' (WRONG!)
Should be: league='西甲', home='赫罗纳', away='皇家社会' (from odds page)
"""
import glob, json, os, re, requests
from bs4 import BeautifulSoup

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

# 找到 fid=1411377
target_dir = None
for d in glob.glob(os.path.join(base, 'tasks\\2026-05-15\\data\\match*')):
    mp = os.path.join(d, 'meta.json')
    if not os.path.exists(mp):
        continue
    with open(mp, 'rb') as f:
        meta = json.loads(f.read().decode('utf-8'))
    if meta.get('fid') == '1411377':
        target_dir = d
        break

if not target_dir:
    print("ERROR: 找不到 fid=1411377")
    import sys
    sys.exit(1)

meta_path = os.path.join(target_dir, 'meta.json')
with open(meta_path, 'rb') as f:
    meta = json.loads(f.read().decode('utf-8'))

print(f"当前 meta.json:")
print(f"  league = {repr(meta.get('league'))}")
print(f"  home = {repr(meta.get('home'))}")
print(f"  away = {repr(meta.get('away'))}")
print(f"  dir = {os.path.basename(target_dir)}")

# 从 odds.500.com 获取正确信息
sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

url = 'https://odds.500.com/fenxi/ouzhi-1411377.shtml'
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')
title = soup.title.get_text() if soup.title else ''
print(f"\n网页标题: {title}")

# 从标题提取联赛
m = re.search(r'\((\d{4}/\d{4})([^)]+)\)', title)
league = ''
if m:
    league = m.group(2).strip()
    print(f"提取到联赛: {repr(league)}")

# 提取主队客队
home = away = ''
for table in soup.find_all('table'):
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) >= 3:
            text0 = tds[0].get_text().strip()
            text1 = tds[1].get_text().strip()
            if '主队' in text0 or '客队' in text0:
                if '主队' in text0:
                    home = text1
                elif '客队' in text0:
                    away = text1

print(f"提取到主队: {repr(home)}")
print(f"提取到客队: {repr(away)}")

# 更新 meta.json
meta['league'] = league
if home:
    meta['home'] = home
if away:
    meta['away'] = away

# 获取 macau_line
url_yz = 'https://odds.500.com/fenxi/yazhi-1411377.shtml'
resp_yz = sess.get(url_yz, timeout=15)
resp_yz.encoding = 'gbk'
soup_yz = BeautifulSoup(resp_yz.text, 'html.parser')

macau_line = ''
for table in soup_yz.find_all('table'):
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 10:
            continue
        name = tds[1].get_text().strip()
        if '澳门' not in name:
            continue
        for idx in [3, 4, 5, 10, 11]:
            if idx >= len(tds):
                continue
            val = tds[idx].get_text().strip().replace('\u00a0', '')
            if any(c in val for c in ['让', '球', '半', '盘', '受让']):
                val = re.sub(r'[\u2b06\u2b07\u27a1\u2191\u2193\u2194\n\r|]', '', val)
                val = re.sub(r'[\d\.]+', '', val).strip()
                val = val.replace('升', '').replace('降', '').strip()
                if val:
                    macau_line = val
                    break
        if macau_line:
            break
    if macau_line:
        break

if macau_line:
    meta['macau_line'] = macau_line
    print(f"提取到 macau_line: {repr(macau_line)}")

# 保存
with open(meta_path, 'wb') as f:
    f.write(json.dumps(meta, ensure_ascii=False, indent=2).encode('utf-8'))

# 验证
with open(meta_path, 'rb') as f:
    verify = json.loads(f.read().decode('utf-8'))

print(f"\n修复后:")
print(f"  league = {repr(verify.get('league'))}")
print(f"  home = {repr(verify.get('home'))}")
print(f"  away = {repr(verify.get('away'))}")
print(f"  macau_line = {repr(verify.get('macau_line'))}")
