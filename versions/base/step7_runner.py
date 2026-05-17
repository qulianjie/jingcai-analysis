# -*- coding: utf-8 -*-
"""Step 7: Macau Asian handicap same odds - v11
使用agent-browser获取真实数据（修复Windows subprocess &截断问题）
用法: python step7_runner.py <fid> <league> [output_path]
"""
import sys, os, io, re, time, subprocess, json
from urllib.parse import quote

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

FID = sys.argv[1] if len(sys.argv) > 1 else '1366313'
LEAGUE = sys.argv[2] if len(sys.argv) > 2 else '日职'
OUTPUT = sys.argv[3] if len(sys.argv) > 3 else 'step7_output.txt'

# Redirect output to file
sys.stdout = io.TextIOWrapper(open(OUTPUT, 'wb'), encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

# Find agent-browser executable
# CRITICAL: On Windows, the .cmd wrapper uses %* which splits on & in URLs.
# We must call the .exe directly.
AB_CMD = None
if os.name == 'nt':
    exe_path = os.path.expandvars(r'%APPDATA%\npm\node_modules\agent-browser\bin\agent-browser-win32-x64.exe')
    if os.path.exists(exe_path):
        AB_CMD = exe_path
if not AB_CMD:
    import shutil
    AB_CMD = shutil.which('agent-browser') or 'agent-browser'

def run_ab(*args, timeout=30):
    """Run agent-browser command. On Windows, calls .exe directly to avoid
    .cmd wrapper's %* splitting & in URLs."""
    return subprocess.run([AB_CMD] + list(args), capture_output=True, text=False, timeout=timeout)

sess = requests.Session()
sess.headers.update(HEADERS)

HANDICAP_ORDER = [
    '受球半/两球', '受一球/球半', '受半球/一球', '受平手/半球', '受平手',
    '平手', '平手/半球', '半球', '半球/一球', '一球', '一球/球半',
    '球半', '球半/两球', '两球', '两球/两球半', '两球半/三球', '三球'
]

KNOWN_LEAGUES = [
    '欧冠', '欧联', '欧协联', '亚冠杯', '亚冠联', '解放者杯', '南美杯', '南俱杯', '美冠杯',
    '世预赛', '欧国联', '欧预赛',
    '英超', '西甲', '德甲', '意甲', '法甲', '葡超', '荷甲', '俄超', '比甲',
    '土超', '巴甲', '巴乙', '阿甲', '智甲', '墨西联', '美职联', '日职', '日职乙',
    '日丙', '韩职', '中超', '挪超', '瑞典超', '丹超', '芬超', '波兰超',
    '苏超', '英冠', '英甲', '英乙', '西协甲', '西协乙', '意丙', '德乙', '法乙',
    '荷乙', '瑞超', '澳超', '公开赛', '女超', '女甲', '女联',
    '英足总', '英联赛', '德国杯', '意大利杯', '法国杯', '国王杯',
    '瑞典甲', '挪甲', '丹甲', '芬甲', '瑞士超', '奥甲', '苏甲',
    '乌超', '罗甲', '以甲', '以超', '塞浦甲', '克罗甲',
    '厄甲', '哥甲', '委超', '秘鲁甲', '乌拉超', '哥伦甲', '哥斯甲',
    '印超', '泰超', '越超', '马超', '新超', '港超', '中甲',
    '澳女联', '葡甲', '土甲', '荷杯', '德丙', '意丁',
    '阿乙', '巴米', '巴保', '巴圣', '巴东北',
    '智乙', '墨西冠', '墨西乙',
    '比乙', '冰超', '冰甲', '爱超', '爱甲', '苏冠', '苏挑',
    '友谊赛', '球会友', 'U21', 'U23', 'U19', 'U17', '青年',
    '日 联 杯', '日联杯', '西超', '西协超',
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

def match_level(bench_cp, bench_w, hist_cp, hist_w):
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

def extract_date(body_text):
    for pattern in [r'(\d{4})-(\d{2})-(\d{2})', r'(\d{4})/(\d{2})/(\d{2})']:
        m = re.search(pattern, body_text)
        if m:
            year = int(m.group(1))
            if year >= 2024:
                return '%s-%s-%s' % (m.group(1), m.group(2), m.group(3))
    for pattern in [r'(\d{4})-(\d{2})-(\d{2})', r'(\d{4})/(\d{2})/(\d{2})']:
        matches = re.findall(pattern, body_text)
        if matches:
            last = matches[-1]
            return '%s-%s-%s' % (last[0], last[1], last[2])
    return ''

def fetch_macau_yazhi(fid):
    """Fetch Macau Asian handicap data for a given FID"""
    try:
        resp = sess.get('https://odds.500.com/fenxi/yazhi-%s.shtml' % fid, timeout=10)
        resp.encoding = 'gbk'
        body_text = resp.text
        soup = BeautifulSoup(body_text, 'html.parser')
        
        date = extract_date(body_text)
        
        league = ''
        title_match = re.search(rb'<title>(.*?)</title>', resp.content, re.IGNORECASE)
        if title_match:
            title_text = title_match.group(1).decode('gbk', errors='ignore')
            for lv in KNOWN_LEAGUES:
                if lv in title_text:
                    league = lv
                    break
        
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds_direct = tr.find_all('td', recursive=False)
                if len(tds_direct) < 5: continue
                name = tds_direct[1].get_text().strip()
                if '门' in name:
                    live_td = tds_direct[2]
                    nested_live = live_td.find('table')
                    if nested_live:
                        ntds = nested_live.find_all('td')
                        if len(ntds) >= 3:
                            cp_live = ntds[1].get_text().strip()
                            w1_live = re.search(r'(\d+\.\d+)', ntds[0].get_text())
                            w2_live = re.search(r'(\d+\.\d+)', ntds[2].get_text())
                    else:
                        cp_live = tds_direct[2].get_text().strip() if len(tds_direct) > 2 else ''
                        cp_live = cp_live.replace(' ', '').replace('\xa0', '')
                        w1_live = re.search(r'(\d+\.\d+)', tds_direct[2].get_text()) if len(tds_direct) > 2 else None
                        w2_live = re.search(r'(\d+\.\d+)', tds_direct[3].get_text()) if len(tds_direct) > 3 else None
                    
                    init_td = tds_direct[4]
                    nested_init = init_td.find('table')
                    if nested_init:
                        ntds = nested_init.find_all('td')
                        if len(ntds) >= 3:
                            cp_init = ntds[1].get_text().strip()
                            w1_init = re.search(r'(\d+\.\d+)', ntds[0].get_text())
                            w2_init = re.search(r'(\d+\.\d+)', ntds[2].get_text())
                    else:
                        cp_init = init_td.get_text().strip() if init_td else ''
                        cp_init = cp_init.replace(' ', '').replace('\xa0', '')
                        w1_init = re.search(r'(\d+\.\d+)', init_td.get_text()) if init_td else None
                        w2_init = re.search(r'(\d+\.\d+)', tds_direct[5].get_text()) if len(tds_direct) > 5 else None
                    
                    init_str = '%s %s/%s' % (cp_init, w1_init.group(1), w2_init.group(1)) if w1_init and w2_init else cp_init
                    live_str = '%s %s/%s' % (cp_live, w1_live.group(1), w2_live.group(1)) if w1_live and w2_live else cp_live
                    
                    return {
                        'league': league, 'date': date,
                        'init_cp': cp_init, 'init_w': w1_init.group(1) if w1_init else '0.000',
                        'live_cp': cp_live, 'live_w': w1_live.group(1) if w1_live else '0.000',
                        'init_str': init_str, 'live_str': live_str,
                    }
    except: pass
    return None

def fetch_same_odds(fid, cp, s1, s2):
    """Fetch same-odds data via agent-browser (page loads data via JS)"""
    cp_encoded = quote(cp.encode('gbk'))
    url = 'https://odds.500.com/fenxi1/yazhi_same.php?cid=5&cp=%s&id=%s&s1=%s&s2=%s' % (cp_encoded, fid, s1, s2)
    
    print('正在获取相同盘口数据（使用agent-browser渲染JS）...')
    print('URL: %s' % url)
    
    # Open page with agent-browser
    run_ab('open', url, timeout=30)
    time.sleep(10)  # Wait for JS to load data
    
    # Get snapshot
    result = run_ab('snapshot', '-i', '--json', timeout=20)
    stdout = result.stdout.decode('utf-8', errors='replace')
    data = json.loads(stdout)
    refs = data.get('data', {}).get('refs', {})
    
    if not refs:
        print('警告：快照为空，页面可能未完全加载')
        return []
    
    # Sort refs by number
    def ref_sort_key(r):
        try:
            return int(r.replace('e', ''))
        except:
            return 0
    
    sorted_refs = sorted(refs.keys(), key=ref_sort_key)
    
    # Find the "历史相同盘口" heading
    heading_idx = None
    for i, ref in enumerate(sorted_refs):
        info = refs[ref]
        if info.get('role') == 'heading' and '历史相同盘口' in info.get('name', ''):
            heading_idx = i
            break
    
    if heading_idx is None:
        print('警告：未找到"历史相同盘口"标题')
        # Debug: show all headings
        for ref in sorted_refs:
            info = refs[ref]
            if info.get('role') == 'heading':
                print('  heading: %s' % repr(info.get('name', '')[:100]))
        return []
    
    # Extract cells after heading
    cell_refs = []
    for ref in sorted_refs[heading_idx + 1:]:
        info = refs[ref]
        if info.get('role') != 'cell':
            continue
        name = info.get('name', '').strip()
        if not name:
            continue
        cell_refs.append((ref, name))
    
    print('快照中获取到 %d 个cell' % len(cell_refs))
    
    # Parse cells into records (11 cells per row)
    CELLS_PER_ROW = 11
    matches = []
    
    i = 0
    while i + CELLS_PER_ROW - 1 < len(cell_refs):
        row = cell_refs[i:i + CELLS_PER_ROW]
        league = row[0][1]
        date = row[1][1]
        score_text = row[2][1]
        panlu = row[3][1]
        init_w1 = row[4][1]
        init_cp = row[5][1]
        init_w2 = row[6][1]
        final_w1 = row[7][1]
        final_cp = row[8][1]
        final_w2 = row[9][1]
        xiexi = row[10][1]
        
        # Validate
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
            i += 1
            continue
        if panlu not in ('赢盘', '输盘', '走盘'):
            i += 1
            continue
        
        # Parse score
        score_m = re.match(r'^(.+?)\s+(\d+):(\d+)\s+(.+)$', score_text)
        if not score_m:
            i += 1
            continue
        
        home = score_m.group(1).strip()
        away = score_m.group(4).strip()
        hs = int(score_m.group(2))
        aw = int(score_m.group(3))
        result = '胜' if hs > aw else ('平' if hs == aw else '负')
        
        # Validate odds
        if not re.match(r'^\d+\.\d{3}$', init_w1) or not re.match(r'^\d+\.\d{3}$', init_w2):
            i += 1
            continue
        if not re.match(r'^\d+\.\d{2}$', final_w1) or not re.match(r'^\d+\.\d{2}$', final_w2):
            i += 1
            continue
        
        matches.append({
            'league': league,
            'date': date,
            'home': home,
            'away': away,
            'result': result,
            'panlu_result': panlu,
            'init_w1': init_w1,
            'init_cp': init_cp,
            'init_w2': init_w2,
            'final_w1': final_w1,
            'final_cp': final_cp,
            'final_w2': final_w2,
            'fid': '',
        })
        
        i += CELLS_PER_ROW
    
    print('获取到 %d 场相同盘口' % len(matches))
    return matches

# ===== Main Process =====

print('=' * 70)
print('第七步：亚盘・澳门 相同盘口')
print('=' * 70)
print()

# Get Macau initial handicap for this match
html = sess.get('https://odds.500.com/fenxi/yazhi-%s.shtml' % FID, timeout=15)
html.encoding = 'gbk'
soup = BeautifulSoup(html.text, 'html.parser')

macau_cp = ''
s1 = ''
s2 = ''
found = False
for table in soup.find_all('table'):
    for tr in table.find_all('tr'):
        tds_direct = tr.find_all('td', recursive=False)
        if len(tds_direct) < 5: continue
        name = tds_direct[1].get_text().strip()
        if '门' in name:
            init_td = tds_direct[4]
            nested_init = init_td.find('table')
            if nested_init:
                ntds = nested_init.find_all('td')
                if len(ntds) >= 3:
                    cp_raw = ntds[1].get_text().strip()
                    m3 = re.search(r'(\d+\.\d+)', ntds[0].get_text())
                    m5 = re.search(r'(\d+\.\d+)', ntds[2].get_text())
            else:
                cp_raw = init_td.get_text().strip() if init_td else ''
                m3 = re.search(r'(\d+\.\d+)', init_td.get_text()) if init_td else None
                m5 = None
            
            cp_map = {
                '平手/半球': '平手/半球', '半球/一球': '半球/一球',
                '一球/球半': '一球/球半', '两球/两球半': '两球/两球半', '球半/两球': '球半/两球',
                '平手降': '平手/半球', '平手球': '平手/半球',
                '半球降': '半球/一球', '半球球': '半球/一球',
                '一球降': '一球/球半', '一球球': '一球/球半',
                '两球降': '两球/两球半', '球半降': '球半/两球',
            }
            cp_key = cp_raw.replace(' ', '').replace('\xa0', '')
            macau_cp = cp_map.get(cp_key, cp_raw)
            if m3: s1 = m3.group(1)
            if m5: s2 = m5.group(1)
            found = True
            break
    if found: break

if not found:
    print('未找到澳门盘口数据')
    sys.exit(0)

print('本场比赛:')
print('  澳门初盘: %s %s / %s' % (macau_cp, s1, s2))
print()

# Fetch same-odds data
same_matches = fetch_same_odds(FID, macau_cp, s1, s2)

if not same_matches:
    print('未解析到同赔数据')
    sys.exit(0)

print('解析到 %d 场同赔' % len(same_matches))
print()

# Fetch Macau Asian handicap for each same-odds match
# The snapshot already contains init/final odds, so compute init_str, live_str, panlu, match_level from it
print('正在计算盘路数据（%d场）...' % len(same_matches))
for i, r in enumerate(same_matches):
    r['init_str'] = '%s %s/%s' % (r.get('init_cp', '-'), r.get('init_w1', '0.000'), r.get('init_w2', '0.000'))
    r['live_str'] = '%s %s/%s' % (r.get('final_cp', '-'), r.get('final_w1', '0.00'), r.get('final_w2', '0.00'))
    r['panlu'] = panlu_dir(r.get('init_cp', ''), r.get('init_w1', '0.000'), r.get('final_cp', ''), r.get('final_w1', '0.00'))
    r['match_level'] = match_level(macau_cp, s1, r.get('init_cp', ''), r.get('init_w1', '0.000'))

# Stats
total = len(same_matches)
win = sum(1 for r in same_matches if r['result'] == '胜')
draw = sum(1 for r in same_matches if r['result'] == '平')
lose = sum(1 for r in same_matches if r['result'] == '负')

level_order = {'高': 0, '中': 1, '低': 2, '-': 3}
same_matches.sort(key=lambda x: level_order.get(x.get('match_level', '-'), 3))

print()
print('【所有赛事】%d场' % total)
print()
print('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘 | 终盘 | 盘路变化 | 盘路匹配度 |')
print('|------|---------|------|------|------|------|----------|-----------|')
for r in same_matches[:50]:
    print('| %s | %s | %s vs %s | %s | %s | %s | %s | %s |' % (
        r.get('league', '-'), r.get('date', '-'), r['home'], r['away'], r['result'],
        r.get('init_str', '-'), r.get('live_str', '-'),
        r.get('panlu', '-'), r.get('match_level', '-')))
if len(same_matches) > 50:
    print('| ... | ... | ... | ... | ... | ... | ... | ... | ... |（仅显示前50场）')
print()
print('📊 所有赛事统计：胜%d 平%d 负%d（共%d场），胜率%.1f%%' % (
    win, draw, lose, total, win/total*100 if total else 0))

high = sum(1 for r in same_matches if r.get('match_level') == '高')
mid = sum(1 for r in same_matches if r.get('match_level') == '中')
low = sum(1 for r in same_matches if r.get('match_level') == '低')
print('盘路匹配度：高%d 中%d 低%d' % (high, mid, low))
