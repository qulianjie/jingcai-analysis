# -*- coding: utf-8 -*-
"""Step 24: 盘路完全匹配汇总
用法: python step24_extractor.py <home_id> <away_id> <league> <fid> <output_path>
"""
import sys, os
import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOME_ID = sys.argv[1] if len(sys.argv) > 1 else '2465'
AWAY_ID = sys.argv[2] if len(sys.argv) > 2 else '848'
LEAGUE = sys.argv[3] if len(sys.argv) > 3 else '瑞典超'
FID = sys.argv[4] if len(sys.argv) > 4 else '1362643'
OUTPUT_PATH = sys.argv[5] if len(sys.argv) > 5 else 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-04-27/step24_002.txt'

import requests, re, json, time
from bs4 import BeautifulSoup
from datetime import datetime

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

now = datetime.now().strftime('%Y-%m-%d %H:%M')

def gd(a, b):
    """获取盘路变化方向"""
    try:
        fa, fb = float(a), float(b)
        if fb < fa - 0.01: return '\u2b07'  # ↓
        elif fb > fa + 0.01: return '\u2b06'  # ↑
    except: pass
    return '\u27a1'  # →

def dir_str3(iw, id_, il, lw, ld, ll):
    return gd(iw, lw) + gd(id_, ld) + gd(il, ll)

def clean_text(s):
    return s.replace('\xa0', '').replace('\u2193', '').replace('\u2191', '').replace('\u2192', '').strip()

# ============ 获取当前比赛基准盘路 ============
print('获取当前比赛基准盘路...')
cur_jc = cur_iw = cur_av = cur_rq = None
try:
    r = sess.get('https://odds.500.com/fenxi/ouzhi-{}.shtml'.format(FID), timeout=10)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, 'html.parser')
    for table in soup.find_all('table'):
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 12: continue
            td0 = tds[0].get_text().strip()
            td1 = tds[1].get_text().strip()
            nums = []
            for idx in [3,4,5,6,7,8]:
                val = clean_text(tds[idx].get_text())
                try: nums.append(float(val))
                except: pass
            if len(nums) < 6: continue
            if td0 == '1':
                cur_jc = nums
            elif td0 == '6':
                cur_iw = nums
            elif '\u767e' in td1 or '\u5e73' in td1:
                cur_av = nums
    if cur_jc: print('  竞彩欧赔盘路: {}'.format(dir_str3(*cur_jc)))
    if cur_iw: print('  IWC盘路: {}'.format(dir_str3(*cur_iw)))
    if cur_av: print('  百家盘路: {}'.format(dir_str3(*cur_av)))
except Exception as e:
    print('  欧赔错误: {}'.format(e))

# 获取让球盘路
try:
    r = sess.get('https://odds.500.com/fenxi/rangqiu-{}.shtml'.format(FID), timeout=10)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, 'html.parser')
    for table in soup.find_all('table'):
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 12: continue
            if tds[0].get_text().strip() != '1': continue
            nums = []
            for idx in [4,5,6,7,8,9]:
                val = clean_text(tds[idx].get_text())
                try: nums.append(float(val))
                except: pass
            if len(nums) >= 6:
                cur_rq = nums
                break
        if cur_rq: break
    if cur_rq: print('  让球盘路: {}'.format(dir_str3(*cur_rq)))
except: pass

# 本场盘路基准
bench_jc_dir = dir_str3(*cur_jc) if cur_jc else ''
bench_iw_dir = dir_str3(*cur_iw) if cur_iw else ''
bench_av_dir = dir_str3(*cur_av) if cur_av else ''
bench_rq_dir = dir_str3(*cur_rq) if cur_rq else ''

# ============ 获取整个联赛所有比赛 ============
print()
print('获取整个联赛比赛...')

# 获取联赛名称和球队列表
league_name = None
team_ids = set()
try:
    r = sess.get('https://liansai.500.com/team/{}/teamfixture/'.format(HOME_ID), timeout=15)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, 'html.parser')
    for tr in soup.find_all('tr', attrs={'data': True}):
        try:
            d = json.loads(tr.get('data', '{}'))
            gbname = d.get('SIMPLEGBNAME', '')
            if not league_name and gbname:
                league_name = gbname
                print('  联赛名称: {}'.format(league_name))
            # Get ALL team IDs from first page (not filtered by league)
            team_ids.add(str(d.get('HOMETEAMID', '')))
            team_ids.add(str(d.get('AWAYTEAMID', '')))
        except: pass
except: pass
team_ids.discard('')
team_ids = sorted(list(team_ids))
print('  联赛球队: {} 支'.format(len(team_ids)))

# 获取所有比赛 - use team_ids filtering (not league name comparison)
all_matches = []
seen_fid = set()

for i, team_id in enumerate(team_ids, 1):
    if i % 4 == 0: print('  已获取 {}/{} 支球队...'.format(i, len(team_ids)))
    try:
        r = sess.get('https://liansai.500.com/team/{}/teamfixture/'.format(team_id), timeout=15)
        r.encoding = 'gbk'
        soup = BeautifulSoup(r.text, 'html.parser')
        for tr in soup.find_all('tr', attrs={'data': True}):
            try:
                d = json.loads(tr.get('data', '{}'))
                # Use team_ids filtering (both teams must be in league team set)
                htid = str(d.get('HOMETEAMID', ''))
                atid = str(d.get('AWAYTEAMID', ''))
                if htid not in team_ids or atid not in team_ids: continue
                fid = str(d.get('FIXTUREID', ''))
                if fid in seen_fid: continue
                seen_fid.add(fid)
                all_matches.append({
                    'fid': fid,
                    'date': d.get('MATCHDATE', ''),
                    'home': d.get('HOMETEAMSXNAME', ''),
                    'away': d.get('AWAYTEAMSXNAME', ''),
                    'score': '{}:{}'.format(d.get('HOMESCORE', 0), d.get('AWAYSCORE', 0)),
                    'result': d.get('lpl_on', '-'),
                })
            except: pass
    except: pass
    time.sleep(0.2)

print('  同联赛: {} 场 (去重后)'.format(len(all_matches)))

# ============ 获取每场比赛的欧赔+让球数据 ============
print()
print('获取欧赔+让球数据...')

match_data = []
for i, m in enumerate(all_matches, 1):
    fid = m.get('fid', '')
    if not fid: continue
    try:
        # 获取欧赔
        r = sess.get('https://odds.500.com/fenxi/ouzhi-{}.shtml'.format(fid), timeout=10)
        r.encoding = 'gbk'
        soup = BeautifulSoup(r.text, 'html.parser')
        jc = iw = av = None
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                td0 = tds[0].get_text().strip()
                td1 = tds[1].get_text().strip()
                nums = []
                for idx in [3,4,5,6,7,8]:
                    val = clean_text(tds[idx].get_text())
                    try: nums.append(float(val))
                    except: pass
                if len(nums) < 6: continue
                if td0 == '1': jc = nums
                elif td0 == '6': iw = nums
                elif '\u767e' in td1 or '\u5e73' in td1: av = nums
        
        # 获取让球
        rq = None
        try:
            r2 = sess.get('https://odds.500.com/fenxi/rangqiu-{}.shtml'.format(fid), timeout=10)
            r2.encoding = 'gbk'
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            for table in soup2.find_all('table'):
                for tr in table.find_all('tr'):
                    tds = tr.find_all('td')
                    if len(tds) < 12: continue
                    if tds[0].get_text().strip() != '1': continue
                    nums = []
                    for idx in [4,5,6,7,8,9]:
                        val = clean_text(tds[idx].get_text())
                        try: nums.append(float(val))
                        except: pass
                    if len(nums) >= 6:
                        rq = nums
                        break
                if rq: break
        except: pass
        
        match_data.append({
            **m,
            'jc': jc,
            'iw': iw,
            'av': av,
            'rq': rq,
        })
        if i % 20 == 0: print('  已获取 {}/{} 场...'.format(i, len(all_matches)))
    except: pass
    time.sleep(0.2)

print('  有效数据: {} 场'.format(len(match_data)))

# ============ 盘路完全匹配分析 ============
print()
print('盘路完全匹配分析...')
print('  竞彩欧赔基准: {}'.format(bench_jc_dir))
print('  IWC基准: {}'.format(bench_iw_dir))
print('  百家基准: {}'.format(bench_av_dir))
print('  让球基准: {}'.format(bench_rq_dir))

# 统计
jc_match = []
iw_match = []
av_match = []
rq_match = []
all_match = []

for m in match_data:
    jc = m.get('jc')
    iw = m.get('iw')
    av = m.get('av')
    rq = m.get('rq')
    
    jc_d = dir_str3(*jc) if jc else ''
    iw_d = dir_str3(*iw) if iw else ''
    av_d = dir_str3(*av) if av else ''
    rq_d = dir_str3(*rq) if rq else ''
    
    matched_companies = []
    if jc_d and jc_d == bench_jc_dir: matched_companies.append('竞彩欧赔')
    if iw_d and iw_d == bench_iw_dir: matched_companies.append('Interwetten')
    if av_d and av_d == bench_av_dir: matched_companies.append('百家平均')
    if rq_d and rq_d == bench_rq_dir: matched_companies.append('让球指数')
    
    if '竞彩欧赔' in matched_companies: jc_match.append({**m, 'dir': jc_d})
    if 'Interwetten' in matched_companies: iw_match.append({**m, 'dir': iw_d})
    if '百家平均' in matched_companies: av_match.append({**m, 'dir': av_d})
    if '让球指数' in matched_companies: rq_match.append({**m, 'dir': rq_d})
    if matched_companies:
        all_match.append({**m, 'companies': matched_companies})

print('  竞彩欧赔匹配: {} 场'.format(len(jc_match)))
print('  IWC匹配: {} 场'.format(len(iw_match)))
print('  百家匹配: {} 场'.format(len(av_match)))
print('  让球匹配: {} 场'.format(len(rq_match)))
print('  至少1项匹配: {} 场'.format(len(all_match)))

# ============ 输出 ============
out = []
out.append('# 第二十四步：盘路完全匹配汇总')
out.append('')
out.append('\U0001f4c5 数据获取时间: ' + now)
out.append('')
out.append('## 本场盘路基准')
out.append('')
out.append('| 公司 | 盘路变化 |')
out.append('|------|---------|')
out.append('| 竞彩欧赔 | {} |'.format(bench_jc_dir))
out.append('| Interwetten | {} |'.format(bench_iw_dir))
out.append('| 百家平均 | {} |'.format(bench_av_dir))
out.append('| 让球指数 | {} |'.format(bench_rq_dir))
out.append('')

# 竞彩欧赔匹配
out.append('## 竞彩欧赔完全匹配 ({} 场)'.format(len(jc_match)))
out.append('')
out.append('| 比赛日期 | 对阵 | 赛果 | 盘路变化 |')
out.append('|---------|------|------|---------|')
for m in jc_match:
    out.append('| {} | {} vs {} | {} | {} |'.format(m['date'], m['home'], m['away'], m['result'], m['dir']))
if not jc_match:
    out.append('| - | - | - | - |')
out.append('')

# IWC匹配
out.append('## Interwetten完全匹配 ({} 场)'.format(len(iw_match)))
out.append('')
out.append('| 比赛日期 | 对阵 | 赛果 | 盘路变化 |')
out.append('|---------|------|------|---------|')
for m in iw_match:
    out.append('| {} | {} vs {} | {} | {} |'.format(m['date'], m['home'], m['away'], m['result'], m['dir']))
if not iw_match:
    out.append('| - | - | - | - |')
out.append('')

# 百家匹配
out.append('## 百家平均完全匹配 ({} 场)'.format(len(av_match)))
out.append('')
out.append('| 比赛日期 | 对阵 | 赛果 | 盘路变化 |')
out.append('|---------|------|------|---------|')
for m in av_match:
    out.append('| {} | {} vs {} | {} | {} |'.format(m['date'], m['home'], m['away'], m['result'], m['dir']))
if not av_match:
    out.append('| - | - | - | - |')
out.append('')

# 让球匹配
out.append('## 让球指数完全匹配 ({} 场)'.format(len(rq_match)))
out.append('')
out.append('| 比赛日期 | 对阵 | 赛果 | 盘路变化 |')
out.append('|---------|------|------|---------|')
for m in rq_match:
    out.append('| {} | {} vs {} | {} | {} |'.format(m['date'], m['home'], m['away'], m['result'], m['dir']))
if not rq_match:
    out.append('| - | - | - | - |')
out.append('')

# 至少1项匹配汇总
out.append('## 任意公司盘路匹配汇总 ({} 场)'.format(len(all_match)))
out.append('')
out.append('| 比赛日期 | 对阵 | 赛果 | 匹配的公司 |')
out.append('|---------|------|------|-----------|')
for m in all_match:
    out.append('| {} | {} vs {} | {} | {} |'.format(m['date'], m['home'], m['away'], m['result'], ', '.join(m['companies'])))
if not all_match:
    out.append('| - | - | - | - |')
out.append('')

# ============ Write ============
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print()
print('='*60)
print('完成！')
print('输出: ' + OUTPUT_PATH)
