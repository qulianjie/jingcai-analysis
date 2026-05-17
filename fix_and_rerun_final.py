# -*- coding: utf-8 -*-
"""Fix meta.json for fid=1411377 and rerun step8_1923"""
import glob, json, os, re, requests, subprocess, sys
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
    sys.exit(1)

meta_path = os.path.join(target_dir, 'meta.json')
with open(meta_path, 'rb') as f:
    meta = json.loads(f.read().decode('utf-8'))

print(f"修复前: league={repr(meta.get('league'))}, home={repr(meta.get('home'))}, away={repr(meta.get('away'))}")

# 从 odds.500.com 获取正确信息
sess = requests.Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

url = 'https://odds.500.com/fenxi/ouzhi-1411377.shtml'
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')
title = soup.title.get_text() if soup.title else ''
print(f"页面标题: {title}")

# 从标题提取联赛
m = re.search(r'\((\d{4}/\d{4})([^)]+)\)', title)
if m:
    meta['league'] = m.group(2).strip()
    print(f"提取到联赛: {repr(meta['league'])}")

# 提取主队客队
for table in soup.find_all('table'):
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) >= 3:
            text0 = tds[0].get_text().strip()
            text1 = tds[1].get_text().strip()
            if '主队' in text0:
                meta['home'] = text1
            elif '客队' in text0:
                meta['away'] = text1

# 获取 macau_line
url_yz = 'https://odds.500.com/fenxi/yazhi-1411377.shtml'
resp_yz = sess.get(url_yz, timeout=15)
resp_yz.encoding = 'gbk'
soup_yz = BeautifulSoup(resp_yz.text, 'html.parser')

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
                    meta['macau_line'] = val
                    break
        if meta.get('macau_line'):
            break
    if meta.get('macau_line'):
        break

# 保存
with open(meta_path, 'wb') as f:
    f.write(json.dumps(meta, ensure_ascii=False, indent=2).encode('utf-8'))

# 验证
with open(meta_path, 'rb') as f:
    verify = json.loads(f.read().decode('utf-8'))

print(f"修复后: league={repr(verify.get('league'))}, home={repr(verify.get('home'))}, away={repr(verify.get('away'))}, macau_line={repr(verify.get('macau_line'))}")

# 清除 __pycache__
cache_dir = os.path.join(base, '__pycache__')
if os.path.exists(cache_dir):
    for f in os.listdir(cache_dir):
        if 'step8_1923' in f.lower():
            os.remove(os.path.join(cache_dir, f))
            print(f"清除缓存: {f}")

# 重新跑 step8_1923
print(f"\n重新跑 step8_1923_extractor.py...")
result = subprocess.run(
    [sys.executable, 'step8_1923_extractor.py', target_dir],
    cwd=base,
    timeout=300
)

# 检查结果
group03 = os.path.join(target_dir, 'group03_asian', 'step8_same_league.txt')
group06 = os.path.join(target_dir, 'group06_baijia', 'step19_baijia_compare.txt')

print("\n=== 最终结果 ===")
for fpath, label in [(group03, 'Step8'), (group06, 'Step19-23')]:
    if os.path.exists(fpath):
        size = os.path.getsize(fpath)
        with open(fpath, 'rb') as f:
            content = f.read().decode('utf-8')
        lines = content.strip().split('\n') if content.strip() else []
        table_rows = sum(1 for l in lines if l.startswith('|') and '---' not in l and '序号' not in l)
        status = "正常" if table_rows > 0 else "为空"
        print(f"{label}: {status} ({size} bytes, {len(lines)} lines, {table_rows} table rows)")
    else:
        print(f"{label}: 文件不存在")
