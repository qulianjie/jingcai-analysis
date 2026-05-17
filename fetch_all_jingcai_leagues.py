# -*- coding: utf-8 -*-
"""从 trade.500.com 全量提取竞彩联赛简称（多日期扫描）"""
import requests, re, json, os, time
from bs4 import BeautifulSoup

SCRIPT_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

# 扫描最近30天的比赛
from datetime import datetime, timedelta
dates = []
for i in range(30):
    d = datetime.now() - timedelta(days=i)
    dates.append(d.strftime('%Y-%m-%d'))

all_leagues = set()
total_matches = 0

for date in dates:
    try:
        url = f'https://trade.500.com/jczq/?playid=269&g=2&date={date}'
        resp = sess.get(url, timeout=15)
        html = resp.content.decode('gbk', errors='ignore')
        
        # 提取 data-simpleleague
        leagues = re.findall(r'data-simpleleague="([^"]*)"', html)
        for l in leagues:
            if l.strip():
                all_leagues.add(l.strip())
        
        # 统计比赛数
        matches = re.findall(r'data-fixtureid="[^"]*"', html)
        total_matches += len(matches)
        
        if leagues:
            print(f'  {date}: {len(matches)}场, {len(set(leagues))}个联赛')
        
        time.sleep(0.3)
    except Exception as e:
        print(f'  {date}: 失败 - {e}')

print(f'\n总计: {total_matches}场比赛, {len(all_leagues)}个竞彩联赛简称')
print('\n竞彩联赛简称列表:')
for l in sorted(all_leagues):
    print(f'  {l}')

# 保存
out_path = os.path.join(SCRIPT_DIR, 'jingcai_league_names_full.txt')
with open(out_path, 'w', encoding='utf-8') as f:
    for l in sorted(all_leagues):
        f.write(l + '\n')
print(f'\n已保存到: {out_path}')
