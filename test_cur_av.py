# -*- coding: utf-8 -*-
"""
测试cur_av是否有值
"""
import requests, json, os
from bs4 import BeautifulSoup
import re

def clean_text(text):
    text = re.sub(r'[<>/\[\](){}]', '', text)
    text = text.replace(',', '').replace('*', '')
    return text.strip()

def fetch_cur_av(fid):
    """获取当前比赛的百家平均"""
    url = 'https://odds.500.com/fenxi/ouzhi-%s.shtml' % fid
    sess = requests.Session()
    r = sess.get(url, timeout=15)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, 'html.parser')
    
    jc = iw = av = None
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
            company = {
                'row': td0,
                'name': td1,
                'jc': '{:.2f}'.format(nums[0]),
                'id': '{:.2f}'.format(nums[1]),
                'il': '{:.2f}'.format(nums[2]),
                'lw': '{:.2f}'.format(nums[3]),
                'ld': '{:.2f}'.format(nums[4]),
                'll': '{:.2f}'.format(nums[5]),
            }
            all_companies.append(company)
            if td0 == '1':
                jc = company
            elif td0 == '6':
                iw = company
            elif '\u767e' in td1 or '\u5e73' in td1:
                av = company
    
    return jc, iw, av, len(all_companies)

# 测试多个比赛
test_cases = [
    ('成功-0507', '1409616'),  # 周日001
    ('成功-0514', '1216098'),  # match3
    ('失败-0508', '1216122'),  # match12
    ('失败-0509', '1409633'),  # match1
    ('失败-0510', '1202679'),  # match10
]

results = []
for label, fid in test_cases:
    jc, iw, av, count = fetch_cur_av(fid)
    results.append('%s (fid=%s): %d companies' % (label, fid, count))
    results.append('  竞彩: %s' % (jc if jc else 'NONE'))
    results.append('  IW: %s' % (iw if iw else 'NONE'))
    results.append('  百家平均: %s' % (av if av else 'NONE'))
    results.append('')

with open('jingcai/cur_av_test.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done')
