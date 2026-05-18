# -*- coding: utf-8 -*-
"""
调试step19：检查历史比赛的赔率数据
"""
import requests, json, os
from bs4 import BeautifulSoup
import re

def clean_text(text):
    text = re.sub(r'[<>/\[\](){}]', '', text)
    text = text.replace(',', '').replace('*', '')
    return text.strip()

def fetch_odds_page(fid):
    url = 'https://odds.500.com/fenxi/ouzhi-%s.shtml' % fid
    sess = requests.Session()
    try:
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
    except Exception as e:
        return None, None, None, 0

# 测试一个成功的比赛的历史比赛
# 05-14 match3 (成功) 的历史比赛
print('测试成功比赛的历史比赛赔率...')
# 从step19内容看，成功比赛有历史比赛数据
# 让我检查一个历史比赛的fid

# 先检查一个失败比赛的历史比赛
# 05-08 match12 (失败) 的历史比赛
print('测试失败比赛的历史比赛赔率...')

# 让我直接运行step8_1923_extractor.py并查看输出
# 先检查step8数据
match_dir = 'jingcai/tasks/2026-05-08/data/match12_莱万特__奥萨苏纳'
step8_file = os.path.join(match_dir, 'group03_asian', 'step8_same_league.txt')

if os.path.exists(step8_file):
    with open(step8_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print('step8 size: %d bytes' % len(content))
    print('step8 content (first 1000 chars):')
    print(content[:1000])
else:
    print('step8 file not found')

# 检查step8中的历史比赛fid
# 让我从step8内容中提取fid
print('\n检查step8中的历史比赛...')
lines = content.split('\n')
fid_count = 0
for line in lines:
    if 'fid=' in line or 'fid:' in line:
        fid_count += 1
        if fid_count <= 5:
            print('  ' + line.strip()[:100])

print('Total fid lines: %d' % fid_count)
