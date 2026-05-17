# -*- coding: utf-8 -*-
"""
调试step19为什么空数据 - 测试单个match
"""
import requests, json, os, sys
from bs4 import BeautifulSoup
import re

# 测试一个空数据的match
test_match = ('2026-05-08', 'match12_莱万特__奥萨苏纳')
date, name = test_match
meta_path = 'jingcai/tasks/%s/data/%s/meta.json' % test_match

with open(meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)

fid = meta.get('fid', '')
league = meta.get('league', '')
home = meta.get('home', '')
away = meta.get('away', '')

print('Testing: %s vs %s' % (home, away))
print('League: %s' % league)
print('FID: %s' % fid)
print('')

# Step 1: 测试当前比赛的赔率页
url = 'https://odds.500.com/fenxi/ouzhi-%s.shtml' % fid
print('Fetching: %s' % url)
try:
    sess = requests.Session()
    r = sess.get(url, timeout=15)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, 'html.parser')
    
    table_count = len(soup.find_all('table'))
    print('Tables found: %d' % table_count)
    
    jc = iw = av = None
    all_companies = []
    for table in soup.find_all('table'):
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 12:
                continue
            td0 = tds[0].get_text().strip()
            td1 = tds[1].get_text().strip()
            nums = []
            for idx in [3,4,5,6,7,8]:
                val = tds[idx].get_text().strip().replace(',','').replace('*','')
                try:
                    nums.append(float(val))
                except:
                    pass
            if len(nums) < 6:
                continue
            company = {
                'row': td0, 'name': td1,
                'nums': nums
            }
            all_companies.append(company)
            if td0 == '1':
                jc = company
            elif td0 == '6':
                iw = company
    
    print('Companies found: %d' % len(all_companies))
    print('竞彩 (row1): %s' % (jc if jc else 'NONE'))
    print('Interwetten (row6): %s' % (iw if iw else 'NONE'))
    
    # 显示前3家公司
    for c in all_companies[:5]:
        print('  %s [%s]: %s' % (c['row'], c['name'], c['nums'][:3]))
    
    if len(all_companies) == 0:
        print('')
        print('*** 问题: 该页面没有赔率数据 ***')
        print('HTML长度: %d' % len(r.text))
        # 找一下页面中是否有任何td
        all_td = soup.find_all('td')
        print('Total td elements: %d' % len(all_td))
        if all_td:
            print('Sample td text: %s' % all_td[0].get_text().strip()[:50])

except Exception as e:
    print('Error: %s' % str(e))
