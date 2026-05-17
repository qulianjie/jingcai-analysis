# -*- coding: utf-8 -*-
"""
直接修复 fid=1411377 的 meta.json
用二进制读写避免编码问题
"""
import glob, json, os, re, sys, requests
from bs4 import BeautifulSoup

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

# 找到 fid=1411377
target_dir = None
target_meta = None
for d in glob.glob(os.path.join(base, 'tasks\\2026-05-15\\data\\match*')):
    mp = os.path.join(d, 'meta.json')
    if not os.path.exists(mp):
        continue
    with open(mp, 'rb') as f:
        raw = f.read()
    meta = json.loads(raw.decode('utf-8'))
    if meta.get('fid') == '1411377':
        target_dir = d
        target_meta = meta
        print(f"找到目录: {d}")
        break

if not target_dir:
    print("ERROR: 找不到 fid=1411377")
    sys.exit(1)

print(f"修复前 league={repr(target_meta.get('league'))}")

# 从网页提取联赛
sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

url = 'https://odds.500.com/fenxi/ouzhi-1411377.shtml'
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')
title = soup.title.get_text() if soup.title else ''
print(f"页面标题: {title}")

m = re.search(r'\((\d{4}/\d{4})([^)]+)\)', title)
league = ''
if m:
    league = m.group(2).strip()
    print(f"提取到联赛: {repr(league)}")

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

print(f"提取到 macau_line: {repr(macau_line)}")

# 更新 meta
target_meta['league'] = league
if macau_line:
    target_meta['macau_line'] = macau_line

# 用二进制写入，确保UTF-8 BOM-free
meta_path = os.path.join(target_dir, 'meta.json')
output = json.dumps(target_meta, ensure_ascii=False, indent=2)
with open(meta_path, 'wb') as f:
    f.write(output.encode('utf-8'))

# 验证
with open(meta_path, 'rb') as f:
    verify = json.loads(f.read().decode('utf-8'))

print(f"\n修复后 league={repr(verify.get('league'))}")
print(f"修复后 macau_line={repr(verify.get('macau_line'))}")

if verify.get('league') == league:
    print("✅ meta.json 修复成功!")
else:
    print("❌ meta.json 修复失败!")
