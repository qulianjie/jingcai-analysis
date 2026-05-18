# -*- coding: utf-8 -*-
"""
调试：找出所有公司名称，看看百家平均叫什么
"""
import requests, json, os, sys
from bs4 import BeautifulSoup

# 测试match12莱万特vs奥萨苏纳
fid = '1216122'
url = 'https://odds.500.com/fenxi/ouzhi-%s.shtml' % fid
sess = requests.Session()
r = sess.get(url, timeout=15)
r.encoding = 'gbk'
soup = BeautifulSoup(r.text, 'html.parser')

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
        all_companies.append({'row': td0, 'name': td1, 'nums': nums})

print('Total companies: %d\n' % len(all_companies))
print('All company names:')
for c in all_companies:
    has_bai = any(ch in c['name'] for ch in ['\u767e', '\u5e73', '\u5747', '\u5e73\u5747'])
    flag = ' <-- MATCH' if has_bai else ''
    # 输出原始字符
    print('  [%s] "%s" %s' % (c['row'], c['name'], [str(x) for x in c['nums'][:3]] + flag))
