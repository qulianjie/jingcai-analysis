# -*- coding: utf-8 -*-
import json, re, os

fid = '1411377'
meta_path = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-15\data\match4_赫罗纳__皇家社会\meta.json'

# 从 odds.500.com 页面标题提取联赛名
import requests
from bs4 import BeautifulSoup

sess = requests.Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

url = f'https://odds.500.com/fenxi/ouzhi-{fid}.shtml'
resp = sess.get(url, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')

title = soup.title.get_text() if soup.title else ''
print(f"页面标题: {title}")

# 从标题提取联赛: "赫罗纳VS皇家社会(2025/2026西甲)-欧赔-500球探"
# 匹配括号里的赛季+联赛
m = re.search(r'\((\d{4}/\d{4})([^)]+)\)', title)
if m:
    season = m.group(1)
    league = m.group(2).strip()
    print(f"赛季: {season}, 联赛: {league}")
    
    # 更新 meta.json
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    meta['league'] = league
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"已更新 league={league}")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
else:
    print("未能从标题提取联赛名")
