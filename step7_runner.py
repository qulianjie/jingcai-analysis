# -*- coding: utf-8 -*-
"""Step 7: Macau Asian handicap same odds - v12
使用ajax接口获取数据（替代agent-browser，更快更准）
用法1: python step7_runner.py <fid> <league> [output_path]
用法2: python step7_runner.py <match_dir>  (自动从 meta.json 读取 fid/league)
"""
import sys, os, io, re, time, json
from urllib.parse import quote

# 支持两种调用方式：match_dir 模式 或 参数模式
if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    MATCH_DIR = sys.argv[1]
    meta_path = os.path.join(MATCH_DIR, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        FID = meta.get('fid', '1366313')
        LEAGUE = meta.get('league', '日职')
    else:
        FID = '1366313'
        LEAGUE = '日职'
    OUTPUT = os.path.join(MATCH_DIR, 'group03_asian', 'step7_macau_same.txt')
else:
    FID = sys.argv[1] if len(sys.argv) > 1 else '1366313'
    LEAGUE = sys.argv[2] if len(sys.argv) > 2 else '日职'
    OUTPUT = sys.argv[3] if len(sys.argv) > 3 else 'step7_output.txt'

# Redirect output to file
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
sys.stdout = io.TextIOWrapper(open(OUTPUT, 'wb'), encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

sess = requests.Session()
sess.headers.update(HEADERS)

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

def extract_macau_odds(text):
    """从yazhi页面HTML中提取澳门初盘（正则方式）"""
    # 澳门公司名在页面中为 <span class="quancheng">*门</span>
    # 初盘数据在紧随的 <td> 内（非即时盘td）
    # 模式: quancheng标签含"门" -> 跳过公司名td和即时盘td -> 找到初盘的pl_table_data
    m = re.search(r'quancheng[^<]*门.*?</span></a>.*?</td>\s*<td[^>]*>\s*<table[^>]*class="pl_table_data"[^>]*>.*?<td[^>]*>(\d+\.\d+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>(\d+\.\d+)</td>', text, re.DOTALL)
    if m:
        cp = m.group(2).strip()
        # 去掉升/降标记如 <font color="red"> 升</font>
        cp = re.sub(r'<font[^>]*>.*?</font>', '', cp).strip()
        return {'init_cp': cp, 'init_w': m.group(1), 'init_w2': m.group(3)}
    # fallback
    m = re.search(r'quancheng[^<]*门.*?</td>\s*<td[^>]*>\s*<table[^>]*>.*?<td[^>]*>(\d+\.\d+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>(\d+\.\d+)</td>', text, re.DOTALL)
    if m:
        cp = re.sub(r'<font[^>]*>.*?</font>', '', m.group(2)).strip()
        return {'init_cp': cp, 'init_w': m.group(1), 'init_w2': m.group(3)}
    return None

def fetch_same_odds_ajax(fid, cp, s1, s2):
    """通过ajax接口获取相同盘口数据"""
    # 先获取cookie
    try:
        sess.get('https://trade.500.com/', timeout=15)
    except:
        pass
    
    # 访问same页面获取vsdate
    cp_encoded = quote(cp.encode('gbk'))
    same_url = 'https://odds.500.com/fenxi1/yazhi_same.php?cid=5&cp=%s&id=%s&s1=%s&s2=%s' % (cp_encoded, fid, s1, s2)
    
    try:
        resp = sess.get(same_url, timeout=15)
        resp.encoding = 'gbk'
        text = resp.text
    except Exception as e:
        print('  ⚠️ 访问same页面失败: %s' % e)
        return []
    
    m_vs = re.search(r'vsdate[=:]\s*[\"\']?([^\"\'&,\s]+)', text)
    vsdate = m_vs.group(1) if m_vs else ''
    
    print('正在获取相同盘口数据（使用ajax接口）...')
    print('  盘口: %s | 水位: %s/%s | vsdate: %s' % (cp, s1, s2, vsdate))
    
    # 调ajax
    params = {
        'cid': '5', 'cp': cp, 's1': s1, 's2': s2,
        'id': fid, 'mid': '0', 'vsdate': vsdate,
        't': str(int(time.time() * 1000)),
    }
    headers = {'Referer': same_url, 'X-Requested-With': 'XMLHttpRequest'}
    
    try:
        r = sess.get('https://odds.500.com/fenxi1/inc/yazhi_sameajax.php',
                     params=params, timeout=20, headers=headers)
        r.encoding = 'gbk'
        
        if len(r.text) < 10:
            print('  ⚠️ ajax返回空数据')
            return []
        
        data = json.loads(r.text)
        rows_html = data.get('row', [])
        print('  获取到 %d 场历史同赔数据' % len(rows_html))
        
    except Exception as e:
        print('  ⚠️ ajax请求失败: %s' % e)
        return []
    
    # 解析每一行HTML
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
            ml = match_level(cp, s1, init_cp, init_w1)
            
            matches.append({
                'league': league, 'date': date, 'home': home, 'away': away,
                'result': result, 'panlu_result': panlu_result,
                'init_cp': init_cp, 'init_w1': init_w1, 'init_w2': init_w2,
                'final_cp': final_cp, 'final_w1': final_w1, 'final_w2': final_w2,
                'panlu': p, 'match_level': ml,
            })
        except:
            continue
    
    print('  解析完成: %d 场' % len(matches))
    return matches

# ===== Main Process =====

print('=' * 70)
print('第七步：亚盘・澳门 相同盘口')
print('=' * 70)
print()

# Get Macau initial handicap for this match (use regex to avoid BS卡顿)
try:
    html = sess.get('https://odds.500.com/fenxi/yazhi-%s.shtml' % FID, timeout=15)
    html.encoding = 'gbk'
    text = html.text
except Exception as e:
    print('获取页面失败: %s' % e)
    sys.exit(1)

macau_info = extract_macau_odds(text)
if not macau_info:
    print('未找到澳门盘口数据')
    sys.exit(0)

macau_cp_raw = macau_info['init_cp']
s1 = macau_info['init_w']
s2 = macau_info['init_w2']

cp_map = {
    '平手/半球': '平手/半球', '半球/一球': '半球/一球',
    '一球/球半': '一球/球半', '两球/两球半': '两球/两球半', '球半/两球': '球半/两球',
    '平手降': '平手/半球', '平手球': '平手/半球',
    '半球降': '半球/一球', '半球球': '半球/一球',
    '一球降': '一球/球半', '一球球': '一球/球半',
    '两球降': '两球/两球半', '球半降': '球半/两球',
}
cp_key = macau_cp_raw.replace(' ', '').replace('\xa0', '')
macau_cp = cp_map.get(cp_key, macau_cp_raw)

print('本场比赛:')
print('  FID: %s' % FID)
print('  联赛: %s' % LEAGUE)
print('  澳门初盘: %s %s / %s' % (macau_cp, s1, s2))
print()

# Fetch same-odds data via ajax
same_matches = fetch_same_odds_ajax(FID, macau_cp, s1, s2)

if not same_matches:
    print('未获取到同赔数据')
    sys.exit(0)

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
    init_str = '%s %s/%s' % (r['init_cp'], r['init_w1'], r['init_w2'])
    live_str = '%s %s/%s' % (r['final_cp'], r['final_w1'], r['final_w2'])
    print('| %s | %s | %s vs %s | %s | %s | %s | %s | %s |' % (
        r.get('league', '-'), r.get('date', '-'), r['home'], r['away'], r['result'],
        init_str, live_str, r['panlu'], r['match_level']))
if len(same_matches) > 50:
    print('| ... | ... | ... | ... | ... | ... | ... | ... | ... |（仅显示前50场）')
print()
print('📊 所有赛事统计：胜%d 平%d 负%d（共%d场），胜率%.1f%%' % (
    win, draw, lose, total, win/total*100 if total else 0))

high = sum(1 for r in same_matches if r.get('match_level') == '高')
mid = sum(1 for r in same_matches if r.get('match_level') == '中')
low = sum(1 for r in same_matches if r.get('match_level') == '低')
print('盘路匹配度：高%d 中%d 低%d' % (high, mid, low))
print()
print('数据来源：ajax接口（替代agent-browser）')
