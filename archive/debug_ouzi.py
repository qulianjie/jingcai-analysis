# -*- coding: utf-8 -*-
import sys, os, json, requests
from bs4 import BeautifulSoup
import io

# Fix stdout encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sess = requests.Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0'})
sess.get('https://odds.500.com/', timeout=10)

match_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-08\data\match3_帕德博恩__卡斯鲁厄'
meta_path = os.path.join(match_dir, 'meta.json')
with open(meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)
fid = meta['fid']
print('FID: %s' % fid)

# Try the ouzhi page
print('\n=== Fetching ouzhi page ===')
resp = sess.get('https://odds.500.com/fenxi/ouzhi-%s.shtml' % fid, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')
companies = {}
for table in soup.find_all('table'):
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 12: continue
        td0 = tds[0].get_text().strip()
        if td0 == '1':
            nums = []
            for idx in [3,4,5,6,7,8]:
                s = tds[idx].get_text().strip().replace(chr(160), '')
                try: nums.append(float(s))
                except: pass
            if len(nums) >= 6:
                companies[1] = {'init': (nums[0],nums[1],nums[2]), 'live': (nums[3],nums[4],nums[5])}
                print('竞彩赔率: init=%.2f/%.2f/%.2f live=%.2f/%.2f/%.2f' % (nums[0],nums[1],nums[2],nums[3],nums[4],nums[5]))

print('Total companies found: %d' % len(companies))

if 1 in companies:
    win, draw, lost = companies[1]['init']
    print('\n=== AJAX request (ouzhi) ===')
    ajax_url = 'https://odds.500.com/fenxi1/inc/ouzhi_sameajax.php'
    referer = 'https://odds.500.com/fenxi1/ouzhi_same.php?cid=1&win=%.2f&draw=%.2f&lost=%.2f&fixtureid=%s' % (win, draw, lost, fid)
    h = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': referer,
    }
    params = {'cid': '1', 'win': '%.2f' % win, 'draw': '%.2f' % draw, 'lost': '%.2f' % lost, 'id': fid, 'mid': '0'}
    print('Referer: %s' % referer)
    r2 = sess.get(ajax_url, params=params, headers=h, timeout=15)
    print('Status: %d' % r2.status_code)
    print('Content-type: %s' % r2.headers.get('content-type', 'unknown'))
    print('Text length: %d' % len(r2.text))
    print('Text[:500]: %s' % repr(r2.text[:500]))
    try:
        j = json.loads(r2.text)
        print('Type: %s' % ('dict' if isinstance(j, dict) else 'list'))
        if isinstance(j, dict):
            for k in list(j.keys())[:10]:
                v = j[k]
                if isinstance(v, list):
                    print('  %s: list[%d]' % (k, len(v)))
                    if v: print('    first: %s' % str(v[0])[:200])
                else:
                    print('  %s: %s' % (k, str(v)[:120]))
    except Exception as e:
        print('JSON error: %s' % str(e)[:200])

# Rangqiu
print('\n=== Fetching rangqiu page ===')
resp2 = sess.get('https://odds.500.com/fenxi/rangqiu-%s.shtml' % fid, timeout=15)
resp2.encoding = 'gbk'
soup2 = BeautifulSoup(resp2.text, 'html.parser')
rq_companies = {}
for table in soup2.find_all('table'):
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 12: continue
        td0 = tds[0].get_text().strip()
        if td0 == '1':
            nums = []
            for idx in [4,5,6,7,8,9]:
                s = tds[idx].get_text().strip().replace(chr(160), '')
                try: nums.append(float(s))
                except: pass
            if len(nums) >= 6:
                td2 = tds[2].get_text().strip().replace(chr(160), '')
                rq_companies[1] = {'handicap': td2, 'init': (nums[0],nums[1],nums[2]), 'live': (nums[3],nums[4],nums[5])}
                print('让球赔率: handicap=%s init=%.2f/%.2f/%.2f live=%.2f/%.2f/%.2f' % (td2, nums[0],nums[1],nums[2],nums[3],nums[4],nums[5]))

print('Total rq companies: %d' % len(rq_companies))

if 1 in rq_companies:
    rq = rq_companies[1]
    win, draw, lost = rq['init']
    hd = rq['handicap']
    print('\n=== AJAX request (rangqiu) ===')
    ajax_url2 = 'https://odds.500.com/fenxi1/inc/rangqiu_sameajax.php'
    referer2 = 'https://odds.500.com/fenxi1/rangqiu_same.php?cid=1&handicapline=%s&win=%.2f&draw=%.2f&lost=%.2f&id=%s' % (hd, win, draw, lost, fid)
    h2 = h.copy()
    h2['Referer'] = referer2
    params2 = {'cid': '1', 'handicapline': hd, 'win': '%.2f' % win, 'draw': '%.2f' % draw, 'lost': '%.2f' % lost, 'id': fid, 'mid': '0'}
    print('Referer: %s' % referer2)
    r3 = sess.get(ajax_url2, params=params2, headers=h2, timeout=15)
    print('Status: %d' % r3.status_code)
    print('Text length: %d' % len(r3.text))
    print('Text[:500]: %s' % repr(r3.text[:500]))
    try:
        j3 = json.loads(r3.text)
        print('Type: %s' % ('dict' if isinstance(j3, dict) else 'list'))
        if isinstance(j3, dict):
            for k in list(j3.keys())[:10]:
                v = j3[k]
                if isinstance(v, list):
                    print('  %s: list[%d]' % (k, len(v)))
                    if v: print('    first: %s' % str(v[0])[:200])
                else:
                    print('  %s: %s' % (k, str(v)[:120]))
    except Exception as e:
        print('JSON error: %s' % str(e)[:200])

# Also check match1 and match2
for m in ['match1_TPS图尔__赫尔辛基', 'match2_坦佩雷山猫__AC奥卢']:
    md = os.path.join(r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-08\data', m)
    mp = os.path.join(md, 'meta.json')
    if os.path.exists(mp):
        with open(mp, 'r', encoding='utf-8') as f:
            mm = json.load(f)
        ff = mm['fid']
        # Check if step2 has data
        s2 = os.path.join(md, 'group01_europe', 'step2_jingcai_same.txt')
        if os.path.exists(s2):
            with open(s2, 'r', encoding='utf-8') as f:
                sc = f.read()
            has_count = '共0' not in sc and ('胜' in sc and '平' in sc)
            if '共0' in sc or (len(sc) < 2000):
                print('\n%s: FID=%s step2 SHORT (%d bytes, empty)' % (m, ff, len(sc)))
            else:
                print('\n%s: FID=%s step2 OK (%d bytes)' % (m, ff, len(sc)))
