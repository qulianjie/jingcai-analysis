# -*- coding: utf-8 -*-
"""直接修复 meta.json + 重新跑 step8_1923"""
import glob, json, os, re, requests, subprocess, sys
from bs4 import BeautifulSoup

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
dirs = glob.glob(os.path.join(base, 'tasks\\2026-05-15\\data\\match4*'))
match_dir = dirs[0]
meta_path = os.path.join(match_dir, 'meta.json')

with open(meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)

print(f"修复前: league={repr(meta.get('league'))}")

sess = requests.Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

fid = meta.get('fid', '')

# 从 odds.500.com 提取联赛
url = f'https://odds.500.com/fenxi/ouzhi-{fid}.shtml'
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
title = BeautifulSoup(resp.text, 'html.parser').title.get_text() if BeautifulSoup(resp.text, 'html.parser').title else ''
print(f"页面标题: {title}")
m = re.search(r'\((\d{4}/\d{4})([^)]+)\)', title)
if m:
    meta['league'] = m.group(2).strip()
    print(f"提取到联赛: {repr(meta['league'])}")

# 从 yazhi 获取 macau_line
url_yz = f'https://odds.500.com/fenxi/yazhi-{fid}.shtml'
resp_yz = sess.get(url_yz, timeout=15)
resp_yz.encoding = 'gbk'
soup_yz = BeautifulSoup(resp_yz.text, 'html.parser')

for table in soup_yz.find_all('table'):
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 10: continue
        name = tds[1].get_text().strip()
        if '澳门' in name:
            for idx in [3, 4, 5, 10, 11]:
                if idx < len(tds):
                    val = tds[idx].get_text().strip().replace('\u00a0', '')
                    if any(c in val for c in ['让', '球', '半', '盘', '受让']):
                        val = re.sub(r'[\u2b06\u2b07\u27a1\u2191\u2193\u2194\n\r|]', '', val)
                        val = re.sub(r'[\d\.]+', '', val).strip()
                        val = val.replace('升', '').replace('降', '').strip()
                        if val:
                            meta['macau_line'] = val
                            break
            if meta.get('macau_line'): break
    if meta.get('macau_line'): break

# 保存
with open(meta_path, 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

with open(meta_path, 'r', encoding='utf-8') as f:
    verify = json.load(f)
print(f"修复后: league={repr(verify.get('league'))}, macau_line={repr(verify.get('macau_line'))}")
print(f"目录: {match_dir}")

# 重新跑 step8_1923
print("\n" + "="*60)
print("重新跑 step8_1923_extractor.py...")
print("="*60)

result = subprocess.run(
    [sys.executable, 'step8_1923_extractor.py', match_dir],
    cwd=base,
    timeout=300
)
