# -*- coding: utf-8 -*-
"""Step 2/3/5 - 欧赔同赔 + 让球同赔 (一次调用生成3个文件)
   V2: 明细加同联赛字段，统计分"相同联赛"和"所有赛事"两个维度

用法: python step235_runner.py <fid> <league> <step2_out> <step3_out> <step5_out>
"""
import sys, os, requests, json, io

FID = sys.argv[1] if len(sys.argv) > 1 else '1199680'
LEAGUE = sys.argv[2] if len(sys.argv) > 2 else '意甲'
STEP2_OUT = sys.argv[3] if len(sys.argv) > 3 else 'step02_jingcai_same.md'
STEP3_OUT = sys.argv[4] if len(sys.argv) > 4 else 'step03_interwetten_same.md'
STEP5_OUT = sys.argv[5] if len(sys.argv) > 5 else 'step05_handicap_same.md'

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}
AJAX_H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',
}

sess = requests.Session()
sess.headers.update(HEADERS)
sess.get('https://odds.500.com/', timeout=10)

def dir_str(init_vals, live_vals):
    result = ''
    for a, b in zip(init_vals, live_vals):
        if b > a + 0.005:
            result += '↑'
        elif b < a - 0.005:
            result += '↓'
        else:
            result += '→'
    return result

def match_level(bench_dir, hist_dir):
    same = sum(1 for a, b in zip(bench_dir, hist_dir) if a == b)
    if same == 3: return '高'
    elif same >= 2: return '中'
    return '低'

def fetch_ouzi_odds(fid):
    try:
        url = 'https://odds.500.com/fenxi/ouzhi-%s.shtml' % fid
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                td0 = tds[0].get_text().strip()
                if td0 == '1':
                    nums = []
                    for idx in [3, 4, 5, 6, 7, 8]:
                        s = tds[idx].get_text().strip().replace(chr(160), '')
                        try: nums.append(float(s))
                        except: pass
                    if len(nums) >= 6:
                        return {'init': (nums[0], nums[1], nums[2]), 'live': (nums[3], nums[4], nums[5])}
    except: pass
    return None

def fetch_rangqiu_odds(fid):
    try:
        url = 'https://odds.500.com/fenxi/rangqiu-%s.shtml' % fid
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                td0 = tds[0].get_text().strip()
                if td0 == '1':
                    nums = []
                    for idx in [4, 5, 6, 7, 8, 9]:
                        s = tds[idx].get_text().strip().replace(chr(160), '')
                        try: nums.append(float(s))
                        except: pass
                    if len(nums) >= 6:
                        return {'init': (nums[0], nums[1], nums[2]), 'live': (nums[3], nums[4], nums[5])}
    except: pass
    return None

def fetch_same_odds(cid, win, draw, lost, fid, is_rangqiu=False, handicap=''):
    if is_rangqiu:
        ajax_url = 'https://odds.500.com/fenxi1/inc/rangqiu_sameajax.php'
        referer = 'https://odds.500.com/fenxi1/rangqiu_same.php?cid=%s&handicapline=%s&win=%s&draw=%s&lost=%s&id=%s' % (cid, handicap, win, draw, lost, fid)
    else:
        ajax_url = 'https://odds.500.com/fenxi1/inc/ouzhi_sameajax.php'
        referer = 'https://odds.500.com/fenxi1/ouzhi_same.php?cid=%s&win=%s&draw=%s&lost=%s&fixtureid=%s' % (cid, win, draw, lost, fid)
    h = AJAX_H.copy()
    h['Referer'] = referer
    params = {'cid': str(cid), 'win': str(win), 'draw': str(draw), 'lost': str(lost), 'id': str(fid), 'mid': '0'}
    if is_rangqiu: params['handicapline'] = str(handicap)
    resp = sess.get(ajax_url, params=params, headers=h, timeout=15)
    try: return json.loads(resp.text.strip())
    except: return None

# ============ 获取本场欧赔和让球数据 ============
resp = sess.get('https://odds.500.com/fenxi/ouzhi-%s.shtml' % FID, timeout=15)
resp.encoding = 'gbk'
soup = BeautifulSoup(resp.text, 'html.parser')
companies = {}
for table in soup.find_all('table'):
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 12: continue
        td0 = tds[0].get_text().strip()
        if td0.isdigit():
            nums = []
            for idx in [3, 4, 5, 6, 7, 8]:
                s = tds[idx].get_text().strip().replace(chr(160), '')
                try: nums.append(float(s))
                except: pass
            if len(nums) >= 6:
                companies[int(td0)] = {'init_w': nums[0], 'init_d': nums[1], 'init_l': nums[2],
                    'live_w': nums[3], 'live_d': nums[4], 'live_l': nums[5]}

jc = companies.get(1)
iwc = companies.get(6) or companies.get(4)

resp_rq = sess.get('https://odds.500.com/fenxi/rangqiu-%s.shtml' % FID, timeout=15)
resp_rq.encoding = 'gbk'
soup_rq = BeautifulSoup(resp_rq.text, 'html.parser')
rq_companies = {}
for table in soup_rq.find_all('table'):
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 12: continue
        td0 = tds[0].get_text().strip()
        td2 = tds[2].get_text().strip().replace(chr(160), '')
        if td0.isdigit():
            nums = []
            for idx in [4, 5, 6, 7, 8, 9]:
                s = tds[idx].get_text().strip().replace(chr(160), '')
                try: nums.append(float(s))
                except: pass
            if len(nums) >= 6:
                rq_companies[int(td0)] = {'handicap': td2,
                    'init_w': nums[0], 'init_d': nums[1], 'init_l': nums[2],
                    'live_w': nums[3], 'live_d': nums[4], 'live_l': nums[5]}

rq_jc = rq_companies.get(1)

result_map = {0: '胜', 1: '平', 2: '负'}

def write_step(title, bench_odds, data, fetch_func, is_rangqiu=False, out=sys.stdout):
    def p(s=''):
        print(s, file=out)
    p('=' * 70)
    p(title)
    p('=' * 70)
    p()
    
    if not data:
        p('无同赔数据')
        p()
        return
    
    wins, draws, losses = data.get('counts', [0, 0, 0])
    total = wins + draws + losses
    match_map = data.get('match', {})
    rows = data.get('row', [])
    
    parsed = []
    for r in rows:
        lid = str(r[0])
        league = match_map.get(lid, lid)
        date = r[3]
        home = r[5]
        hs = str(r[6])
        as_ = str(r[7])
        away = r[8]
        result = result_map.get(r[9], '?')
        hist_live = (float(r[10]), float(r[11]), float(r[12]))
        fid = r[4]
        
        odds_info = fetch_func(fid)
        if odds_info:
            hist_init = odds_info['init']
            hist_live_from_page = odds_info['live']
            if abs(hist_live[0] - hist_live_from_page[0]) > 0.01:
                hist_live = hist_live_from_page
            hist_dir = dir_str(hist_init, hist_live)
        else:
            hist_init = hist_live
            hist_dir = '→→→'
        
        bench_dir = dir_str(bench_odds['init'], bench_odds['live'])
        ml = match_level(bench_dir, hist_dir)
        is_same = (league == LEAGUE)
        
        parsed.append({
            'league': league, 'date': date,
            'home': home, 'hs': hs, 'as_': as_, 'away': away,
            'result': result,
            'hist_init': hist_init, 'hist_live': hist_live,
            'hist_dir': hist_dir, 'match_level': ml,
            'is_same_league': is_same,
        })
    
    same_league = [x for x in parsed if x['is_same_league']]
    diff_league = [x for x in parsed if not x['is_same_league']]
    
    level_order = {'高': 0, '中': 1, '低': 2}
    same_league.sort(key=lambda x: level_order.get(x['match_level'], 3))
    diff_league.sort(key=lambda x: level_order.get(x['match_level'], 3))
    
    def fmt_row(x):
        lg_mark = '同联赛' if x['is_same_league'] else ''
        return '| %s | %s | %s %s:%s %s | %s | %.2f/%.2f/%.2f | %.2f/%.2f/%.2f | %s | %s | %s |' % (
            x['league'], x['date'], x['home'], x['hs'], x['as_'], x['away'],
            x['result'],
            x['hist_init'][0], x['hist_init'][1], x['hist_init'][2],
            x['hist_live'][0], x['hist_live'][1], x['hist_live'][2],
            x['hist_dir'], x['match_level'], lg_mark)
    
    # ===== 第一部分：相同联赛统计和明细 =====
    if same_league:
        sl_total = len(same_league)
        sl_w = sum(1 for x in same_league if x['result'] == '胜')
        sl_d = sum(1 for x in same_league if x['result'] == '平')
        sl_l = sum(1 for x in same_league if x['result'] == '负')
        
        p('【一、相同联赛（%s）】%d场' % (LEAGUE, sl_total))
        p()
        p('| 赛事 | 日期 | 对阵 | 赛果 | 初盘 | 终盘 | 盘路 | 匹配度 | 联赛 |')
        p('|------|------|------|------|------|------|------|--------|------|')
        for x in same_league:
            p(fmt_row(x))
        p()
        p('📊 相同联赛统计（%s）：胜%d 平%d 负%d（共%d场），胜率%.1f%%' % (
            LEAGUE, sl_w, sl_d, sl_l, sl_total, sl_w/sl_total*100 if sl_total else 0))
        p()
        p('=' * 70)
        p()
    
    # ===== 第二部分：所有赛事统计和明细 =====
    p('【二、所有赛事】%d场' % total)
    p()
    p('| 赛事 | 日期 | 对阵 | 赛果 | 初盘 | 终盘 | 盘路 | 匹配度 | 联赛 |')
    p('|------|------|------|------|------|------|------|--------|------|')
    for x in same_league:
        p(fmt_row(x))
    for x in diff_league:
        p(fmt_row(x))
    p()
    p('📊 所有赛事统计：胜%d 平%d 负%d（共%d场），胜率%.1f%%' % (
        wins, draws, losses, total, wins/total*100 if total else 0))
    p()

# ============ Step 2: 竞彩官网同赔 ============
if jc:
    bench_jc = {'init': (jc['init_w'], jc['init_d'], jc['init_l']),
                'live': (jc['live_w'], jc['live_d'], jc['live_l'])}
    with open(STEP2_OUT, 'w', encoding='utf-8') as f:
        p = lambda s='': print(s, file=f)
        p('竞彩初盘：%.2f / %.2f / %.2f' % bench_jc['init'])
        p('竞彩终盘：%.2f / %.2f / %.2f' % bench_jc['live'])
        p('当前联赛：%s' % LEAGUE)
        p()
        data2 = fetch_same_odds(1, '%.2f' % jc['init_w'], '%.2f' % jc['init_d'], '%.2f' % jc['init_l'], FID)
        write_step('竞彩官网 相同赔率', bench_jc, data2, fetch_ouzi_odds, out=f)
    print('[OK] Step 2: %s' % STEP2_OUT)

# ============ Step 3: Interwetten同赔 ============
if iwc:
    bench_iwc = {'init': (iwc['init_w'], iwc['init_d'], iwc['init_l']),
                 'live': (iwc['live_w'], iwc['live_d'], iwc['live_l'])}
    with open(STEP3_OUT, 'w', encoding='utf-8') as f:
        p = lambda s='': print(s, file=f)
        p('Interwetten初盘：%.2f / %.2f / %.2f' % bench_iwc['init'])
        p('Interwetten终盘：%.2f / %.2f / %.2f' % bench_iwc['live'])
        p('当前联赛：%s' % LEAGUE)
        p()
        data3 = fetch_same_odds(4, '%.2f' % iwc['init_w'], '%.2f' % iwc['init_d'], '%.2f' % iwc['init_l'], FID)
        write_step('Interwetten 相同赔率', bench_iwc, data3, fetch_ouzi_odds, out=f)
    print('[OK] Step 3: %s' % STEP3_OUT)

# ============ Step 5: 让球同赔 ============
if rq_jc:
    bench_rq = {'init': (rq_jc['init_w'], rq_jc['init_d'], rq_jc['init_l']),
                'live': (rq_jc['live_w'], rq_jc['live_d'], rq_jc['live_l'])}
    with open(STEP5_OUT, 'w', encoding='utf-8') as f:
        p = lambda s='': print(s, file=f)
        p('让球数：%s' % rq_jc['handicap'])
        p('竞彩让球初盘：%.2f / %.2f / %.2f' % bench_rq['init'])
        p('竞彩让球终盘：%.2f / %.2f / %.2f' % bench_rq['live'])
        p('当前联赛：%s' % LEAGUE)
        p()
        data5 = fetch_same_odds(1, '%.2f' % rq_jc['init_w'], '%.2f' % rq_jc['init_d'], '%.2f' % rq_jc['init_l'], FID,
            is_rangqiu=True, handicap=rq_jc['handicap'])
        write_step('竞彩让球 相同赔率', bench_rq, data5, fetch_rangqiu_odds, is_rangqiu=True, out=f)
    print('[OK] Step 5: %s' % STEP5_OUT)
