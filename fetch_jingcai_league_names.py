# -*- coding: utf-8 -*-
"""从竞彩官网提取所有竞彩联赛简称"""
import requests, re, json, os
from bs4 import BeautifulSoup

SCRIPT_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

# 竞彩官网 - 足球竞彩页面
url = 'https://www.sporttery.cn/jc/jczq/index.html'
print(f'获取竞彩官网: {url}')

try:
    resp = sess.get(url, timeout=15)
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    leagues = set()
    # 查找所有联赛相关的链接
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        text = a.get_text().strip()
        if text and len(text) > 1:
            leagues.add(text)
    
    print(f'找到 {len(leagues)} 个联赛/赛事:')
    for l in sorted(leagues):
        print(f'  {l}')
except Exception as e:
    print(f'获取失败: {e}')

# 尝试另一个URL
print('\n尝试 odds.500.com...')
try:
    resp2 = sess.get('https://odds.500.com/jczq/index.shtml', timeout=15)
    resp2.encoding = 'gbk'
    soup2 = BeautifulSoup(resp2.text, 'html.parser')
    
    leagues2 = set()
    # 从 data-* 属性提取
    for div in soup2.find_all(attrs={'data-league': True}):
        league = div.get('data-league', '').strip()
        if league:
            leagues2.add(league)
    
    # 从表格列头提取
    for th in soup2.find_all('th'):
        text = th.get_text().strip()
        if text and len(text) > 1 and not text.isdigit():
            leagues2.add(text)
    
    print(f'找到 {len(leagues2)} 个联赛:')
    for l in sorted(leagues2):
        print(f'  {l}')
except Exception as e:
    print(f'odds.500.com 获取失败: {e}')

# 合并
all_names = set()
all_names.update(leagues)
all_names.update(leagues2)

print(f'\n总计 {len(all_names)} 个竞彩联赛简称')
if all_names:
    out_path = os.path.join(SCRIPT_DIR, 'jingcai_league_names_full.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        for name in sorted(all_names):
            f.write(name + '\n')
    print(f'已保存到: {out_path}')
