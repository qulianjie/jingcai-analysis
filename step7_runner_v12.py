"""改进版 step7 — 用 ajax 替代 agent-browser"""
import sys, io, requests, re, json, time, os
from bs4 import BeautifulSoup
from urllib.parse import quote

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 参数
if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    MATCH_DIR = sys.argv[1]
    meta_path = os.path.join(MATCH_DIR, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        FID = meta.get('fid', '')
        LEAGUE = meta.get('league', '')
    else:
        FID = LEAGUE = ''
    OUTPUT = os.path.join(MATCH_DIR, 'group03_asian', 'step7_macau_same.txt')
else:
    FID = sys.argv[1]
    LEAGUE = sys.argv[2] if len(sys.argv) > 2 else ''
    OUTPUT = sys.argv[3] if len(sys.argv) > 3 else 'step7_output.txt'

print('=' * 70)
print('第七步：亚盘・澳门 相同盘口')
print('=' * 70)
print()

# 复写 stdout 到文件
sys.stdout = io.TextIOWrapper(open(OUTPUT, 'wb'), encoding='utf-8', errors='replace')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

sess = requests.Session()
sess.headers.update(HEADERS)

# 1. 获取 cookie
try:
    sess.get('https://trade.500.com/', timeout=15)
except:
    pass

# 2. 获取本场澳门初盘
print('本场比赛信息:')
print('  FID: %s, 联赛: %s' % (FID, LEAGUE))

macau_cp = ''
s1 = s2 = ''

try:
    resp = sess.get('https://odds.500.com/fenxi/yazhi-%s.shtml' % FID, timeout=15)
    resp.encoding = 'gbk'
    text = resp.text
    soup = BeautifulSoup(text, 'html.parser')
    
    for table in soup.find_all('table'):
        for tr in table.find_all('tr'):
            tds = tr.find_all('td', recursive=False)
            if len(tds) < 5:
                continue
            name = tds[1].get_text().strip()
            if '门' not in name:
                continue
            init_td = tds[4]
            nested = init_td.find('table')
            if nested:
                ntds = nested.find_all('td')
                if len(ntds) >= 3:
                    cp_raw = ntds[1].get_text().strip()
                    m3 = re.search(r'(\d+\.\d+)', ntds[0].get_text())
                    m5 = re.search(r'(\d+\.\d+)', ntds[2].get_text())
                    s1 = m3.group(1) if m3 else ''
                    s2 = m5.group(1) if m5 else ''
            else:
                cp_raw = init_td.get_text().strip() if init_td else ''
                m3 = re.search(r'(\d+\.\d+)', init_td.get_text()) if init_td else None
                s1 = m3.group(1) if m3 else ''
            
            # 清理盘口名
            cp_map = {
                '平手降': '平手/半球', '平手球': '平手/半球',
                '半球降': '半球/一球', '半球球': '半球/一球',
                '一球降': '一球/球半', '一球球': '一球/球半',
                '两球降': '两球/两球半', '球半降': '球半/两球',
            }
            cp_key = cp_raw.replace(' ', '').replace('\xa0', '')
            macau_cp = cp_map.get(cp_key, cp_raw)
            break
        if macau_cp:
            break
    
    if not macau_cp:
        print('⚠️ 未找到澳门盘口')
        sys.exit(0)
    
    print('  澳门初盘: %s %s / %s' % (macau_cp, s1, s2))
except Exception as e:
    print('⚠️ 获取澳门盘口失败: %s' % e)
    sys.exit(0)

print()

# 3. 调同赔 ajax
cp_enc = quote(macau_cp.encode('gbk'))
same_url = 'https://odds.500.com/fenxi1/yazhi_same.php?cid=5&cp=%s&id=%s&s1=%s&s2=%s' % (cp_enc, FID, s1, s2)

try:
    resp = sess.get(same_url, timeout=15)
    resp.encoding = 'gbk'
    text = resp.text
    
    # 提取 vsdate
    m_vs = re.search(r'vsdate[=:]\s*[\"\']?([^\"\'&,\s]+)', text)
    vsdate = m_vs.group(1) if m_vs else ''
    
    # 调 ajax
    params = {
        'cid': '5', 'cp': macau_cp, 's1': s1, 's2': s2,
        'id': FID, 'mid': '0', 'vsdate': vsdate,
        't': str(int(time.time() * 1000)),
    }
    ajax_headers = {
        'Referer': same_url,
        'X-Requested-With': 'XMLHttpRequest',
    }
    
    r_ajax = sess.get('https://odds.500.com/fenxi1/inc/yazhi_sameajax.php',
                      params=params, timeout=20, headers=ajax_headers)
    r_ajax.encoding = 'gbk'
    
    if len(r_ajax.text) < 10:
        print('⚠️ ajax 返回空数据')
        sys.exit(0)
    
    data = json.loads(r_ajax.text)
    rows_html = data.get('row', [])
    
    print('获取到 %d 场历史同赔数据' % len(rows_html))
    print()
    
except Exception as e:
    print('⚠️ 获取同赔数据失败: %s' % e)
    sys.exit(0)

# 4. 解析每一行
def handicap_val(cp):
    HANDICAP_ORDER = [
        '受球半/两球', '受一球/球半', '受半球/一球', '受平手/半球', '受平手',
        '平手', '平手/半球', '半球', '半球/一球', '一球', '一球/球半',
        '球半', '球半/两球', '两球', '两球/两球半', '两球半/三球', '三球'
    ]
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
    except:
        parts.append('水位不变')
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
    except:
        pass
    if score >= 1.5: return '高'
    elif score >= 0.8: return '中'
    return '低'

matches = []
for row_html in rows_html:
    try:
        soup = BeautifulSoup(row_html, 'html.parser')
        cells = soup.find_all('td')
        if len(cells) < 11:
            continue
        vals = [c.get_text().strip().replace('\xa0', '') for c in cells]
        league = vals[0]
        date = vals[1]
        score_text = vals[2]
        panlu_result = vals[3]
        init_w1 = vals[4]
        init_cp = vals[5]
        init_w2 = vals[6]
        final_w1 = vals[7]
        final_cp = vals[8]
        final_w2 = vals[9]
        
        # 解析比分
        score_m = re.match(r'^(.+?)\s+(\d+):(\d+)\s+(.+)$', score_text)
        if not score_m:
            continue
        home = score_m.group(1).strip()
        away = score_m.group(4).strip()
        hs = int(score_m.group(2))
        aw = int(score_m.group(3))
        result = '胜' if hs > aw else ('平' if hs == aw else '负')
        
        p = panlu_dir(init_cp, init_w1, final_cp, final_w1)
        ml = match_level(macau_cp, s1, init_cp, init_w1)
        
        matches.append({
            'league': league, 'date': date, 'home': home, 'away': away,
            'result': result, 'panlu_result': panlu_result,
            'init_cp': init_cp, 'init_w1': init_w1, 'init_w2': init_w2,
            'final_cp': final_cp, 'final_w1': final_w1, 'final_w2': final_w2,
            'panlu': p, 'match_level': ml,
        })
    except:
        continue

if not matches:
    print('⚠️ 未解析到有效数据')
    sys.exit(0)

# 5. 排序输出
level_order = {'高': 0, '中': 1, '低': 2, '-': 3}
matches.sort(key=lambda x: level_order.get(x.get('match_level', '-'), 3))

total = len(matches)
win = sum(1 for m in matches if m['result'] == '胜')
draw = sum(1 for m in matches if m['result'] == '平')
lose = sum(1 for m in matches if m['result'] == '负')

print('【所有赛事】%d场' % total)
print()
print('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘 | 终盘 | 盘路变化 | 盘路匹配度 |')
print('|------|---------|------|------|------|------|----------|-----------|')
for m in matches[:100]:
    init_str = '%s %s/%s' % (m['init_cp'], m['init_w1'], m['init_w2'])
    live_str = '%s %s/%s' % (m['final_cp'], m['final_w1'], m['final_w2'])
    print('| %s | %s | %s vs %s | %s | %s | %s | %s | %s |' % (
        m['league'], m['date'], m['home'], m['away'], m['result'],
        init_str, live_str, m['panlu'], m['match_level']))
if total > 100:
    print('| ... | ... | ... | ... | ... | ... | ... | ... |（仅显示前100场）')
print()
print('📊 所有赛事统计：胜%d 平%d 负%d（共%d场），胜率%.1f%%' % (
    win, draw, lose, total, win/total*100 if total else 0))

high = sum(1 for m in matches if m['match_level'] == '高')
mid = sum(1 for m in matches if m['match_level'] == '中')
low = sum(1 for m in matches if m['match_level'] == '低')
print('盘路匹配度：高%d 中%d 低%d' % (high, mid, low))
print()
print('🟢 数据来源：ajax接口（替代agent-browser）')
