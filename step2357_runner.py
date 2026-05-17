# -*- coding: utf-8 -*-
"""Step 2/3/5/7 - 同赔统一获取 (一次调用生成4个文件)
   欧赔同赔(2) + Interwetten同赔(3) + 让球同赔(5) + 澳门亚盘同赔(7)
   全部使用AJAX接口，不再依赖agent-browser

用法: python step2357_runner.py <fid> <league> <step2_out> <step3_out> <step5_out> <step7_out>
"""
import sys, os, requests, json, io, time, re

FID = sys.argv[1] if len(sys.argv) > 1 else '1199680'
LEAGUE = sys.argv[2] if len(sys.argv) > 2 else '意甲'
STEP2_OUT = sys.argv[3] if len(sys.argv) > 3 else 'step02_jingcai_same.md'
STEP3_OUT = sys.argv[4] if len(sys.argv) > 4 else 'step03_interwetten_same.md'
STEP5_OUT = sys.argv[5] if len(sys.argv) > 5 else 'step05_handicap_same.md'
STEP7_OUT = sys.argv[6] if len(sys.argv) > 6 else 'step07_macau_same.md'

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

# ============ 通用工具函数 ============

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

def fetch_yazhi_odds(fid):
    """获取指定FID的澳门亚盘数据"""
    try:
        url = 'https://odds.500.com/fenxi/yazhi-%s.shtml' % fid
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td', recursive=False)
                if len(tds) < 5: continue
                name = tds[1].get_text().strip()
                if '门' in name:
                    # 终盘
                    live_td = tds[2]
                    nested = live_td.find('table')
                    if nested:
                        ntds = nested.find_all('td')
                        if len(ntds) >= 3:
                            cp_live = ntds[1].get_text().strip()
                            w1_m = re.search(r'(\d+\.\d+)', ntds[0].get_text())
                            w2_m = re.search(r'(\d+\.\d+)', ntds[2].get_text())
                    else:
                        cp_live = tds[2].get_text().strip().replace(' ', '').replace('\xa0', '')
                        w1_m = re.search(r'(\d+\.\d+)', tds[2].get_text()) if len(tds) > 2 else None
                        w2_m = re.search(r'(\d+\.\d+)', tds[3].get_text()) if len(tds) > 3 else None
                    # 初盘
                    init_td = tds[4]
                    nested = init_td.find('table')
                    if nested:
                        ntds = nested.find_all('td')
                        if len(ntds) >= 3:
                            cp_init = ntds[1].get_text().strip()
                            w1_m2 = re.search(r'(\d+\.\d+)', ntds[0].get_text())
                            w2_m2 = re.search(r'(\d+\.\d+)', ntds[2].get_text())
                    else:
                        cp_init = init_td.get_text().strip() if init_td else ''
                        cp_init = cp_init.replace(' ', '').replace('\xa0', '')
                        w1_m2 = re.search(r'(\d+\.\d+)', init_td.get_text()) if init_td else None
                        w2_m2 = re.search(r'(\d+\.\d+)', tds[5].get_text()) if len(tds) > 5 else None
                    if w1_m and w2_m and w1_m2 and w2_m2:
                        return {
                            'init_cp': cp_init, 'init_w1': float(w1_m2.group(1)), 'init_w2': float(w2_m2.group(1)),
                            'live_cp': cp_live, 'live_w1': float(w1_m.group(1)), 'live_w2': float(w2_m.group(1)),
                        }
    except: pass
    return None

# ============ 同赔AJAX获取 ============

def fetch_same_odds_europe(cid, win, draw, lost, fid):
    """欧赔同赔 AJAX (步2/3)"""
    ajax_url = 'https://odds.500.com/fenxi1/inc/ouzhi_sameajax.php'
    referer = 'https://odds.500.com/fenxi1/ouzhi_same.php?cid=%s&win=%s&draw=%s&lost=%s&fixtureid=%s' % (
        cid, win, draw, lost, fid)
    h = AJAX_H.copy()
    h['Referer'] = referer
    params = {'cid': str(cid), 'win': str(win), 'draw': str(draw), 'lost': str(lost), 'id': str(fid), 'mid': '0'}
    resp = sess.get(ajax_url, params=params, headers=h, timeout=15)
    try: return json.loads(resp.text.strip())
    except: return None

def fetch_same_odds_handicap(cid, win, draw, lost, fid, handicap):
    """让球同赔 AJAX (步5)"""
    ajax_url = 'https://odds.500.com/fenxi1/inc/rangqiu_sameajax.php'
    referer = 'https://odds.500.com/fenxi1/rangqiu_same.php?cid=%s&handicapline=%s&win=%s&draw=%s&lost=%s&id=%s' % (
        cid, handicap, win, draw, lost, fid)
    h = AJAX_H.copy()
    h['Referer'] = referer
    params = {'cid': str(cid), 'handicapline': str(handicap), 'win': str(win), 'draw': str(draw),
              'lost': str(lost), 'id': str(fid), 'mid': '0'}
    resp = sess.get(ajax_url, params=params, headers=h, timeout=15)
    try: return json.loads(resp.text.strip())
    except: return None

def fetch_same_odds_macau(cid, cp, s1, s2, fid, vsdate=''):
    """澳门亚盘同赔 AJAX (步7) - 与步2/3/5统一使用AJAX接口"""
    ajax_url = 'https://odds.500.com/fenxi1/inc/yazhi_sameajax.php'
    import urllib.parse
    cp_enc = urllib.parse.quote(cp.encode('gbk'))
    referer = 'https://odds.500.com/fenxi1/yazhi_same.php?cid=%s&cp=%s&id=%s&s1=%s&s2=%s' % (
        cid, cp_enc, fid, s1, s2)
    h = AJAX_H.copy()
    h['Referer'] = referer
    # 先访问页面建立session
    sess.get(referer, timeout=15)
    # cp必须传GBK解码后的字符串，让requests自动URL编码
    params = {
        'cid': str(cid), 'cp': cp, 's1': str(s1), 's2': str(s2),
        'id': str(fid), 'mid': '0',
        'vsdate': vsdate, 't': str(int(time.time() * 1000)),
    }
    resp = sess.get(ajax_url, params=params, headers=h, timeout=15)
    try: return json.loads(resp.text.strip())
    except: return None

# ============ 欧赔/让球同赔输出 (步2/3/5共用) ============

result_map = {0: '胜', 1: '平', 2: '负'}

def write_europe_step(title, bench_odds, data, fetch_func, out=sys.stdout):
    """输出欧赔/让球同赔结果"""
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

# ============ 澳门亚盘同赔输出 (步7) ============

HANDICAP_ORDER = [
    '受球半/两球', '受一球/球半', '受半球/一球', '受平手/半球', '受平手',
    '平手', '平手/半球', '半球', '半球/一球', '一球', '一球/球半',
    '球半', '球半/两球', '两球', '两球/两球半', '两球半/三球', '三球'
]

def handicap_val(cp):
    cp = cp.replace(' ', '').replace('\xa0', '')
    if cp in HANDICAP_ORDER:
        return HANDICAP_ORDER.index(cp)
    for i, h in enumerate(HANDICAP_ORDER):
        if h in cp or cp in h:
            return i
    return 999

def panlu_dir(init_cp, init_w, final_cp, final_w):
    parts = []
    iv = handicap_val(init_cp)
    fv = handicap_val(final_cp)
    if fv > iv: parts.append('升盘')
    elif fv < iv: parts.append('降盘')
    else: parts.append('盘口不变')
    try:
        if float(final_w) > float(init_w) + 0.005: parts.append('升水')
        elif float(final_w) < float(init_w) - 0.005: parts.append('降水')
        else: parts.append('水位不变')
    except: parts.append('水位不变')
    return ' '.join(parts)

def match_level_yazhi(bench_cp, bench_w, hist_cp, hist_w):
    bd = handicap_val(bench_cp)
    hd = handicap_val(hist_cp)
    score = 0
    if bd == hd: score += 1
    else:
        diff = abs(bd - hd)
        if diff <= 1: score += 0.5
    try:
        wb = float(bench_w)
        wh = float(hist_w)
        if abs(wb - wh) <= 0.05: score += 1
        elif abs(wb - wh) <= 0.1: score += 0.5
    except: pass
    if score >= 1.5: return '高'
    elif score >= 0.8: return '中'
    return '低'

def parse_macau_ajax_html(html_str):
    """解析澳门同赔AJAX返回的HTML行"""
    soup = BeautifulSoup(html_str, 'html.parser')
    rows = []
    for tr in soup.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) < 8: continue
        row = {}
        # 联赛
        league_a = tds[0].find('a')
        row['league'] = league_a.get_text().strip() if league_a else tds[0].get_text().strip()
        # 日期
        row['date'] = tds[1].get_text().strip() if len(tds) > 1 else ''
        # 对阵
        match_a = tds[2].find('a') if len(tds) > 2 else None
        if match_a:
            match_text = match_a.get_text().strip()
            # 解析 "主队  比分  客队"
            m = re.search(r'([^\s&]+)\s+([\d]+:[\d]+)\s+([^\s&]+)', match_text)
            if m:
                row['home'] = m.group(1).strip()
                row['score'] = m.group(2)
                row['away'] = m.group(3).strip()
                parts = m.group(2).split(':')
                hs, aw = int(parts[0]), int(parts[1])
                row['result'] = '胜' if hs > aw else ('平' if hs == aw else '负')
        # 盘路结果
        pan_span = tds[3].find('span') if len(tds) > 3 else None
        row['panlu_result'] = pan_span.get_text().strip() if pan_span else ''
        # 初盘水位
        row['init_w1'] = tds[4].get_text().strip() if len(tds) > 4 else ''
        # 初盘盘口
        row['init_cp'] = tds[5].get_text().strip() if len(tds) > 5 else ''
        # 初盘水位2
        row['init_w2'] = tds[6].get_text().strip() if len(tds) > 6 else ''
        # 终盘水位
        row['final_w1'] = tds[7].get_text().strip() if len(tds) > 7 else ''
        # 终盘盘口
        row['final_cp'] = tds[8].get_text().strip() if len(tds) > 8 else ''
        # 终盘水位2
        row['final_w2'] = tds[9].get_text().strip() if len(tds) > 9 else ''
        # 详细链接
        detail_a = tds[-1].find('a') if len(tds) > 0 else None
        if detail_a and detail_a.get('href'):
            href = detail_a.get('href', '')
            # 优先从最后一个TD找yazhi/daxiao链接
            fid_m = re.search(r'(?:yazhi|daxiao)-(\d+)', href)
            if fid_m:
                row['fid'] = fid_m.group(1)
        # Fallback: 从TD[2]的shuju链接找FID
        if 'fid' not in row and len(tds) > 2:
            match_a = tds[2].find('a')
            if match_a and match_a.get('href'):
                href2 = match_a.get('href', '')
                fid_m2 = re.search(r'shuju-(\d+)', href2)
                if fid_m2:
                    row['fid'] = fid_m2.group(1)
        rows.append(row)
    return rows

def write_macau_step(title, bench_cp, bench_w1, data, out=sys.stdout):
    """输出澳门亚盘同赔结果"""
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
    
    raw_rows = data.get('row', [])
    if not raw_rows:
        p('无同赔数据')
        p()
        return
    
    # 解析HTML行
    all_html = ''.join(raw_rows)
    parsed_rows = parse_macau_ajax_html(all_html)
    
    # 获取本场vsdate用于后续查询
    vsdate = ''
    
    # 逐场获取亚盘数据
    print('  澳门同赔: 获取%d场历史盘口数据...' % len(parsed_rows))
    for i, r in enumerate(parsed_rows):
        fid = r.get('fid', '')
        if not fid:
            r['init_str'] = '-'; r['live_str'] = '-'; r['panlu'] = '-'; r['match_level'] = '-'
            continue
        yazhi_data = fetch_yazhi_odds(fid)
        if yazhi_data:
            r['init_str'] = '%s %.3f/%.3f' % (yazhi_data['init_cp'], yazhi_data['init_w1'], yazhi_data['init_w2'])
            r['live_str'] = '%s %.3f/%.3f' % (yazhi_data['live_cp'], yazhi_data['live_w1'], yazhi_data['live_w2'])
            r['panlu'] = panlu_dir(yazhi_data['init_cp'], yazhi_data['init_w1'],
                                   yazhi_data['live_cp'], yazhi_data['live_w1'])
            r['match_level'] = match_level_yazhi(bench_cp, bench_w1,
                                                  yazhi_data['init_cp'], yazhi_data['init_w1'])
        else:
            r['init_str'] = '-'; r['live_str'] = '-'; r['panlu'] = '-'; r['match_level'] = '-'
        if (i + 1) % 10 == 0:
            print('  已处理 %d/%d' % (i+1, len(parsed_rows)))
        time.sleep(0.2)
    
    valid_rows = [r for r in parsed_rows if r.get('home') and r.get('away')]
    total = len(valid_rows)
    if total == 0:
        p('无有效同赔数据')
        p()
        return
    
    win = sum(1 for r in valid_rows if r.get('result') == '胜')
    draw = sum(1 for r in valid_rows if r.get('result') == '平')
    lose = sum(1 for r in valid_rows if r.get('result') == '负')
    
    level_order = {'高': 0, '中': 1, '低': 2, '-': 3}
    valid_rows.sort(key=lambda x: level_order.get(x.get('match_level', '-'), 3))
    
    p('澳门初盘: %s 水位: %.3f' % (bench_cp, float(bench_w1)))
    p('当前联赛: %s' % LEAGUE)
    p()
    
    p('【所有赛事】%d场' % total)
    p()
    p('| 赛事 | 日期 | 对阵 | 赛果 | 初盘 | 终盘 | 盘路变化 | 盘路匹配度 |')
    p('|------|------|------|------|------|------|----------|-----------|')
    for r in valid_rows[:50]:
        print('| %s | %s | %s vs %s | %s | %s | %s | %s | %s |' % (
            r.get('league', '-'), r.get('date', '-'), r['home'], r['away'], r.get('result', '-'),
            r.get('init_str', '-'), r.get('live_str', '-'),
            r.get('panlu', '-'), r.get('match_level', '-')), file=out)
    if len(valid_rows) > 50:
        p('| ... | ... | ... | ... | ... | ... | ... | ... |（仅显示前50场）')
    p()
    p('📊 所有赛事统计：胜%d 平%d 负%d（共%d场），胜率%.1f%%' % (
        win, draw, lose, total, win/total*100 if total else 0))
    
    high = sum(1 for r in valid_rows if r.get('match_level') == '高')
    mid = sum(1 for r in valid_rows if r.get('match_level') == '中')
    low = sum(1 for r in valid_rows if r.get('match_level') == '低')
    p('盘路匹配度：高%d 中%d 低%d' % (high, mid, low))
    p()

# ============ 获取本场数据 ============

# --- 欧赔数据 ---
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

# --- 让球数据 ---
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

# --- 澳门亚盘数据 ---
resp_yz = sess.get('https://odds.500.com/fenxi/yazhi-%s.shtml' % FID, timeout=15)
resp_yz.encoding = 'gbk'
soup_yz = BeautifulSoup(resp_yz.text, 'html.parser')

macau_cp = ''
macau_s1 = ''
macau_s2 = ''
macau_vsdate = ''

# 从原始HTML字节中提取macau参数（避免BeautifulSoup的编码问题）
raw_html = resp_yz.content
# HTML中URL使用 & 作为分隔符，cp值用 [^&]* 匹配（不含&字符）
raw_m = re.search(rb'cid=5&cp=([^&]*)&id=' + FID.encode() + rb'&s1=([^&]*)&s2=([^&"]*)', raw_html)
if raw_m:
    cp_bytes = raw_m.group(1)
    try:
        macau_cp = cp_bytes.decode('gbk')
    except:
        macau_cp = cp_bytes.decode('gb2312', errors='replace')
    macau_s1 = raw_m.group(2).decode('ascii')
    macau_s2 = raw_m.group(3).decode('ascii')
    print('  澳门初盘: %s 水位: %s/%s' % (macau_cp, macau_s1, macau_s2))
else:
    print('  警告: 未找到澳门亚盘链接')

# 获取vsdate - 先尝试从yazhi页面提取（比赛时间）
match_time = ''
for script in soup_yz.find_all('script'):
    content = script.string or ''
    # 查找比赛时间
    mt_m = re.search(r'(?:match_time|vsdate|matchdate|begintime)["\s:]+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', content)
    if mt_m:
        match_time = mt_m.group(1)
        break

# 如果yazhi页面找不到，尝试从页面其他位置提取
if not match_time:
    # 从yazhi页面的table中提取日期
    date_m = re.search(rb'\d{4}-\d{2}-\d{2}', resp_yz.content)
    if date_m:
        date_str = date_m.group().decode('ascii')
        match_time = date_str + ' 14:00:00'

print(f'  vsdate: {match_time}')

# 如果通过链接没找到，尝试从页面JS中直接提取macau参数
if not macau_cp:
    for script in soup_yz.find_all('script'):
        content = script.string or ''
        # 查找 yazhi_sameajax 调用中的 cp 参数
        cp_m = re.search(r'cp:\s*["\x27]([^"\x27]+)["\x27]', content)
        s1_m = re.search(r's1:\s*["\x27]([^"\x27]+)["\x27]', content)
        s2_m = re.search(r's2:\s*["\x27]([^"\x27]+)["\x27]', content)
        if cp_m and s1_m and s2_m:
            macau_cp = cp_m.group(1)
            macau_s1 = s1_m.group(1)
            macau_s2 = s2_m.group(1)
            break

# 如果还是没找到，尝试从原始HTML字节中提取
if not macau_cp:
    raw_html = resp_yz.content
    # 查找 cid=5 的链接中的 cp 参数
    raw_m = re.search(rb'cid=5&cp=([^&]*)&id=' + FID.encode(), raw_html)
    if raw_m:
        cp_bytes = raw_m.group(1)
        try:
            macau_cp = cp_bytes.decode('gbk')
        except:
            macau_cp = cp_bytes.decode('gb2312', errors='replace')
        # 同时提取 s1, s2
        s1_m = re.search(rb'cid=5&cp=[^&]*&id=' + FID.encode() + rb'&s1=([^&]*)&s2=([^&]*)', raw_html)
        if s1_m:
            macau_s1 = s1_m.group(1).decode('ascii')
            macau_s2 = s1_m.group(2).decode('ascii')

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
        data2 = fetch_same_odds_europe(1, '%.2f' % jc['init_w'], '%.2f' % jc['init_d'], '%.2f' % jc['init_l'], FID)
        write_europe_step('竞彩官网 相同赔率', bench_jc, data2, fetch_ouzi_odds, out=f)
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
        data3 = fetch_same_odds_europe(4, '%.2f' % iwc['init_w'], '%.2f' % iwc['init_d'], '%.2f' % iwc['init_l'], FID)
        write_europe_step('Interwetten 相同赔率', bench_iwc, data3, fetch_ouzi_odds, out=f)
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
        data5 = fetch_same_odds_handicap(1, '%.2f' % rq_jc['init_w'], '%.2f' % rq_jc['init_d'],
            '%.2f' % rq_jc['init_l'], FID, rq_jc['handicap'])
        write_europe_step('竞彩让球 相同赔率', bench_rq, data5, fetch_rangqiu_odds, out=f)
    print('[OK] Step 5: %s' % STEP5_OUT)

# ============ Step 7: 澳门亚盘同赔 ============
if macau_cp and macau_s1:
    with open(STEP7_OUT, 'w', encoding='utf-8') as f:
        write_macau_step('澳门 相同盘口', macau_cp, macau_s1,
            fetch_same_odds_macau(5, macau_cp, macau_s1, macau_s2, FID, match_time), out=f)
    print('[OK] Step 7: %s' % STEP7_OUT)
else:
    print('[WARN] Step 7: 未找到澳门盘口数据')
