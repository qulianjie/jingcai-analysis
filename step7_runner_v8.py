# -*- coding: utf-8 -*-
"""Step 7: Macau Asian handicap same odds - v8 使用agent-browser获取真实数据
用法: python step7_runner.py <fid> <league> [output_path]
"""
import sys, os, io, json, subprocess, re, time
from urllib.parse import quote

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

FID = sys.argv[1] if len(sys.argv) > 1 else '1366313'
LEAGUE = sys.argv[2] if len(sys.argv) > 2 else '日职'
OUTPUT = sys.argv[3] if len(sys.argv) > 3 else 'step7_output.txt'

# 重定向输出到文件
sys.stdout = io.TextIOWrapper(open(OUTPUT, 'wb'), encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

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

KNOWN_LEAGUES = ['欧冠', '欧联', '欧协联', '亚冠杯', '亚冠联', '解放者杯', '南美杯', '南俱杯', '美冠杯',
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
    '友谊赛', '球会友',
    'U21', 'U23', 'U19', 'U17', '青年',
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

def fetch_same_odds_with_browser(fid, cp, s1, s2):
    """用agent-browser获取同赔数据"""
    cp_encoded = quote(cp.encode('gbk'))
    url = 'https://odds.500.com/fenxi1/yazhi_same.php?cid=5&cp=%s&id=%s&s1=%s&s2=%s' % (cp_encoded, fid, s1, s2)
    
    print('使用agent-browser获取同赔数据...')
    print('URL: %s' % url)
    
    # 打开页面
    subprocess.run(['agent-browser', 'open', url], capture_output=True, text=True, timeout=30)
    time.sleep(3)
    
    # 获取快照
    result = subprocess.run(['agent-browser', 'snapshot', '-i', '--json'], capture_output=True, text=True, timeout=20)
    data = json.loads(result.stdout)
    refs = data['data']['refs']
    
    # 从snapshot提取同赔表格数据
    matches = []
    current_match = {}
    
    for ref, info in sorted(refs.items(), key=lambda x: x[0]):
        name = info.get('name', '')
        role = info.get('role', '')
        
        if role == 'cell':
            # 联赛
            if any(lv in name for lv in KNOWN_LEAGUES if len(lv) <= 4):
                current_match['league'] = name
            # 日期
            elif re.match(r'\d{4}-\d{2}-\d{2}', name):
                current_match['date'] = name
            # 对阵
            elif re.search(r'\d+:\d+', name) and 'vs' not in name.lower():
                parts = re.split(r'\s+', name)
                if len(parts) >= 3:
                    home = parts[0]
                    score = parts[1]
                    away = parts[2]
                    current_match['home'] = home
                    current_match['away'] = away
                    current_match['score'] = score
                    if ':' in score:
                        p = score.split(':')
                        try:
                            hs, aw = int(p[0]), int(p[1])
                            current_match['result'] = '胜' if hs > aw else ('平' if hs == aw else '负')
                        except:
                            current_match['result'] = ''
                    else:
                        current_match['result'] = ''
            # 盘路
            elif name in ['赢盘', '输盘', '走盘']:
                current_match['panlu_result'] = name
            # 初盘水位
            elif re.match(r'\d+\.\d{3}$', name):
                if 'init_w' not in current_match:
                    current_match['init_w'] = name
                else:
                    current_match['init_w2'] = name
            # 初盘盘口
            elif '平手' in name or '半球' in name or '一球' in name or '球半' in name or '两球' in name:
                if 'init_cp' not in current_match:
                    current_match['init_cp'] = name
            # 详细链接
            elif name == '详细':
                # 获取href
                attr_result = subprocess.run(['agent-browser', 'get', 'attr', '@' + ref, 'href', '--json'], 
                    capture_output=True, text=True, timeout=10)
                attr_data = json.loads(attr_result.stdout)
                href = attr_data.get('data', {}).get('attribute', '')
                fid_match = re.search(r'yazhi-(\d+)', href)
                if fid_match:
                    current_match['fid'] = fid_match.group(1)
                
                # 保存这场比赛
                if 'home' in current_match and 'fid' in current_match:
                    matches.append(current_match.copy())
                    current_match = {}
    
    return matches

# ===== 主流程 =====

print('=' * 70)
print('第七步：亚盘・澳门 相同盘口')
print('=' * 70)
print()

# 获取本场比赛澳门初盘
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

# 用agent-browser获取同赔数据
same_matches = fetch_same_odds_with_browser(FID, macau_cp, s1, s2)

if not same_matches:
    print('未解析到同赔数据')
    sys.exit(0)

print('解析到 %d 场同赔' % len(same_matches))
print()

# 逐场获取澳门亚盘数据
print('正在逐场获取澳门亚盘数据（%d场）...' % len(same_matches))
for i, r in enumerate(same_matches):
    fid = r.get('fid', '')
    if not fid:
        r['init_str'] = '-'; r['live_str'] = '-'; r['panlu'] = '-'; r['match_level'] = '-'
        continue
    data = fetch_macau_yazhi(fid)
    if data:
        r['init_str'] = data['init_str']; r['live_str'] = data['live_str']
        r['panlu'] = panlu_dir(data['init_cp'], data['init_w'], data['live_cp'], data['live_w'])
        r['match_level'] = match_level(macau_cp, s1, data['init_cp'], data['init_w'])
    else:
        r['init_str'] = '-'; r['live_str'] = '-'; r['panlu'] = '-'; r['match_level'] = '-'
    if (i + 1) % 5 == 0:
        print('  已处理 %d/%d' % (i+1, len(same_matches)))
    time.sleep(0.3)

# 统计
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
