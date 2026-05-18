# -*- coding: utf-8 -*-
"""找到 fid=1411377 的 match4 目录，修复 meta.json，重新跑 step8_1923"""
import glob, json, os, sys, re, subprocess

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

# 找到所有 match4 目录
all_match4 = glob.glob(os.path.join(base, 'tasks\\2026-05-15\\data\\match4*'))
print(f"找到 {len(all_match4)} 个 match4 目录:")

target_dir = None
for d in all_match4:
    meta_path = os.path.join(d, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        fid = meta.get('fid', '')
        print(f"  fid={fid}, dir={d}")
        if fid == '1411377':
            target_dir = d

if not target_dir:
    print("ERROR: 找不到 fid=1411377")
    sys.exit(1)

print(f"\n目标目录: {target_dir}")

meta_path = os.path.join(target_dir, 'meta.json')
with open(meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)

print(f"修复前: league={repr(meta.get('league'))}, macau_line={repr(meta.get('macau_line'))}")

# 从 odds.500.com 提取联赛
import requests
from bs4 import BeautifulSoup

sess = requests.Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

url = f'https://odds.500.com/fenxi/ouzhi-1411377.shtml'
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')
title = soup.title.get_text() if soup.title else ''
print(f"页面标题: {title}")

m = re.search(r'\((\d{4}/\d{4})([^)]+)\)', title)
if m:
    meta['league'] = m.group(2).strip()
    print(f"提取到联赛: {repr(meta['league'])}")

# 从 yazhi 获取 macau_line
url_yz = f'https://odds.500.com/fenxi/yazhi-1411377.shtml'
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

# 重新跑 step8_1923
print("\n" + "="*60)
print("重新跑 step8_1923_extractor.py...")
print("="*60 + "\n")

result = subprocess.run(
    [sys.executable, 'step8_1923_extractor.py', target_dir],
    cwd=base,
    timeout=300
)

# 检查结果
group03 = os.path.join(target_dir, 'group03_asian', 'step8_same_league.txt')
group06 = os.path.join(target_dir, 'group06_baijia', 'step19_baijia_compare.txt')

print("\n" + "="*60)
print("检查结果:")
print("="*60)

for fpath, label in [(group03, 'Step8'), (group06, 'Step19-23')]:
    if os.path.exists(fpath):
        size = os.path.getsize(fpath)
        with open(fpath, encoding='utf-8') as f:
            content = f.read()
        lines = content.strip().split('\n') if content.strip() else []
        table_rows = sum(1 for l in lines if l.startswith('|') and '---' not in l and '序号' not in l)
        status = "正常" if table_rows > 0 else "为空"
        print(f"{label}: {status} ({size} bytes, {len(lines)} lines, {table_rows} table rows)")
    else:
        print(f"{label}: 文件不存在")
