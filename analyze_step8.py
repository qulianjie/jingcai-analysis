# -*- coding: utf-8 -*-
"""
检查step8文件内容，提取历史比赛fid，然后测试这些fid能否抓到av
"""
import os, json, requests
from bs4 import BeautifulSoup
import re

def clean_text(text):
    text = re.sub(r'[<>/\[\](){}]', '', text)
    text = text.replace(',', '').replace('*', '')
    return text.strip()

def fetch_av(fid):
    url = 'https://odds.500.com/fenxi/ouzhi-%s.shtml' % fid
    sess = requests.Session()
    try:
        r = sess.get(url, timeout=10)
        r.encoding = 'gbk'
        soup = BeautifulSoup(r.text, 'html.parser')
        av = None
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
                if td0 == '1' or '\u767e' in td1 or '\u5e73' in td1:
                    if '\u767e' in td1 or '\u5e73' in td1:
                        av = {
                            'name': td1,
                            'lw': '{:.2f}'.format(nums[3]),
                            'ld': '{:.2f}'.format(nums[4]),
                            'll': '{:.2f}'.format(nums[5]),
                        }
        return av
    except:
        return None

# 读取一个失败match的step8，提取历史比赛fid
match_dir = 'jingcai/tasks/2026-05-12/data/match10_赫塔费__马洛卡'
step8_file = os.path.join(match_dir, 'group03_asian', 'step8_same_league.txt')

results = []
if os.path.exists(step8_file):
    with open(step8_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    results.append('step8 size: %d bytes' % len(content))
    results.append('')
    
    # 从step8内容中提取比赛信息
    # 格式可能是 "对阵 | 日期 | fid=xxx"
    lines = content.split('\n')
    fids = []
    for line in lines:
        # 找fid
        fid_match = re.search(r'fid[=:](\d+)', line)
        if fid_match:
            fids.append(fid_match.group(1))
    
    results.append('Found %d fids in step8' % len(fids))
    if fids:
        results.append('Sample fids: ' + ', '.join(fids[:5]))
    else:
        results.append('No fids found! This explains why step19 is empty.')
        results.append('Step8 content preview:')
        results.append(content[:500])
else:
    results.append('step8 file not found')

# 测试2个历史比赛的av
if fids:
    results.append('')
    results.append('Testing historical match odds...')
    for fid in fids[:3]:
        av = fetch_av(fid)
        results.append('  fid=%s: av=%s' % (fid, av if av else 'NONE'))

with open('jingcai/step8_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done')
