# -*- coding: utf-8 -*-
"""从 trade.500.com 全量提取竞彩联赛简称"""
import requests, re, json, os
from bs4 import BeautifulSoup

SCRIPT_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

# 尝试多个日期获取更多联赛
dates = ['2026-05-16', '2026-05-17', '2026-05-15', '2026-05-14', '2026-05-13']
all_leagues = set()

for date in dates:
    print(f'\n获取 {date}...')
    try:
        url = f'https://trade.500.com/jczq/?playid=269&g=2&date={date}'
        resp = sess.get(url, timeout=15)
        html = resp.content.decode('gbk', errors='ignore')
        
        # 从 data-simpleleague 提取
        leagues = re.findall(r'data-simpleleague="([^"]*)"', html)
        for l in leagues:
            if l.strip():
                all_leagues.add(l.strip())
        
        print(f'  找到 {len(set(leagues))} 个联赛')
    except Exception as e:
        print(f'  失败: {e}')

print(f'\n总计 {len(all_leagues)} 个竞彩联赛简称:')
for l in sorted(all_leagues):
    print(f'  {l}')

# 保存到文件
out_path = os.path.join(SCRIPT_DIR, 'jingcai_league_names_full.txt')
with open(out_path, 'w', encoding='utf-8') as f:
    for l in sorted(all_leagues):
        f.write(l + '\n')
print(f'\n已保存到: {out_path}')

# 与之前硬编码的对比
hardcoded = ['英超','西甲','德甲','意甲','法甲','英冠','德乙','韩职','K1联赛','日职','J1','J2',
         '欧冠','欧联','欧协联','解放者杯','巴甲','阿甲','中超','澳超','美职足','荷甲','葡超',
         '瑞超','挪超','丹超','比甲','土超','俄超','苏超','瑞士超','奥超','波兰超','芬超',
         '日职乙','日职丙','韩K1','韩K2','K联赛','K2联赛','巴乙','智甲','哥甲','厄甲',
         '委内超','乌拉超','巴拉联','德国杯','国王杯','意大利杯','法国杯','足总杯',
         '联赛杯','亚冠','英甲','英乙','西乙','意乙','法乙','荷乙']

new_leagues = all_leagues - set(hardcoded)
missing_leagues = set(hardcoded) - all_leagues

print(f'\n对比分析:')
print(f'  新发现: {len(new_leagues)} 个')
for l in sorted(new_leagues):
    print(f'    + {l}')
print(f'  硬编码中没有找到的: {len(missing_leagues)} 个')
for l in sorted(missing_leagues):
    print(f'    - {l}')
