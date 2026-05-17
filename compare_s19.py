# -*- coding: utf-8 -*-
import requests, json, os
from bs4 import BeautifulSoup
import re

def clean_text(text):
    text = re.sub(r'[<>/\[\](){}]', '', text)
    text = text.replace(',', '').replace('*', '')
    return text.strip()

def fetch_odds(fid):
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
            td1 = clean_text(tds[1].get_text())
            nums = []
            for idx in [3,4,5,6,7,8]:
                val = clean_text(tds[idx].get_text())
                try:
                    nums.append(float(val))
                except:
                    pass
            if len(nums) < 6:
                continue
            all_companies.append({'row': td0, 'name': td1, 'nums': nums})
    return all_companies

test_cases = [
    ('成功', '2026-05-14', 'match3_比利亚雷__塞维利亚', '1216098'),
    ('失败', '2026-05-08', 'match12_莱万特__奥萨苏纳', '1216122'),
]

results = []
for status, date, name, fid in test_cases:
    results.append('='*60)
    results.append('%s: %s/%s (fid=%s)' % (status, date, name, fid))
    
    companies = fetch_odds(fid)
    results.append('Total companies: %d' % len(companies))
    
    jc = iw = av = None
    found_av_list = []
    for c in companies:
        if c['row'] == '1':
            jc = c
        elif c['row'] == '6':
            iw = c
        elif '\u767e' in c['name'] or '\u5e73' in c['name']:
            found_av_list.append(c['name'])
            av = c
    
    results.append('Found av names: %s' % (found_av_list if found_av_list else 'NONE'))
    results.append('竞彩(row1): %s' % (jc['name'] if jc else 'NONE'))
    results.append('IW(row6): %s' % (iw['name'] if iw else 'NONE'))
    results.append('百家平均: %s' % (av['name'] if av else 'NONE'))
    results.append('')
    results.append('All companies:')
    for c in companies:
        flag = ''
        if c['row'] == '1': flag = ' [竞彩]'
        elif c['row'] == '6': flag = ' [IW]'
        elif '\u767e' in c['name'] or '\u5e73' in c['name']: flag = ' [百家匹配]'
        results.append('  [%s] "%s"%s' % (c['row'], c['name'], flag))
    results.append('')

with open('jingcai/compare_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done')
