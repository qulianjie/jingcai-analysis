# -*- coding: utf-8 -*-
"""Step 8 + Step 19-23 合并提取器 - 同联赛亚盘/欧赔对比
用法: python step8_1923_extractor.py <home_id> <away_id> <league> <fid> <macau_line> [output_path]
"""
import sys, os
import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOME_ID = sys.argv[1] if len(sys.argv) > 1 else ''
AWAY_ID = sys.argv[2] if len(sys.argv) > 2 else ''
LEAGUE = sys.argv[3] if len(sys.argv) > 3 else ''
FID = sys.argv[4] if len(sys.argv) > 4 else ''
MACAU_LINE = sys.argv[5] if len(sys.argv) > 5 else ''
OUTPUT_PATH = sys.argv[6] if len(sys.argv) > 6 else ''
OUTPUT_PATH_1923 = sys.argv[7] if len(sys.argv) > 7 else ''

import requests, re, json, time
from bs4 import BeautifulSoup
from datetime import datetime

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

now = datetime.now().strftime('%Y-%m-%d %H:%M')

def gd(a, b):
    try:
        fa, fb = float(a), float(b)
        if fb < fa - 0.01: return '\u2b07'
        elif fb > fa + 0.01: return '\u2b06'
    except: pass
    return '\u27a1'

def dir_str3(iw, id_, il, lw, ld, ll):
    return gd(iw, lw) + gd(id_, ld) + gd(il, ll)

def match_level(bench, hist):
    if len(bench) != 3 or len(hist) != 3: return '-'
    same = sum(1 for a, b in zip(bench, hist) if a == b)
    if same == 3: return '高'
    elif same >= 2: return '中'
    return '低'

def init_stats():
    return {'高': {'胜':0,'平':0,'负':0}, '中': {'胜':0,'平':0,'负':0}, '低': {'胜':0,'平':0,'负':0}}

def stats_summary(s):
    lines = []
    for lv in ['高', '中', '低']:
        x = s.get(lv, {})
        t = sum(x.values())
        if t > 0:
            lines.append('{}盘路: 胜{} 平{} 负{} (共{}场)'.format(lv, x.get('胜',0), x.get('平',0), x.get('负',0), t))
    return '\n'.join(lines)

def clean_text(s):
    """Clean text from page, remove arrows and special chars"""
    return s.replace('\u00a0', '').replace('\u2193', '').replace('\u2191', '').replace('\u2b07', '').replace('\u2b06', '').replace(' ', '').strip()

def match_odds_prefix(bench, hist):
    """Match odds: compare all three (home win, draw, away win) - integer + first decimal digit
    Rule: any 2 out of 3 match => True"""
    try:
        match_count = 0
        for idx in [0, 1, 2]:  # compare all three
            bv = float(bench[idx])
            hv = float(hist[idx])
            b_int = int(bv)
            b_dec = int((bv - b_int) * 10)
            h_int = int(hv)
            h_dec = int((hv - h_int) * 10)
            if b_int == h_int and b_dec == h_dec:
                match_count += 1
        return match_count >= 2  # at least 2 out of 3 match
    except:
        return False

# ============ 获取历史比赛（整个联赛） ============
print('获取整个联赛比赛...')

# ============ 联赛ID映射（联赛名称 -> liansai.500.com 联赛ID） ============
LEAGUE_ID_MAP = {
    '日职': '19524',
    '日职乙': '9069',
    '瑞典超': '19501',
    '英超': '19495',
    '西甲': '19496',
    '德甲': '19497',
    '意甲': '19498',
    '法甲': '19499',
    '中超': '19500',
    '荷甲': '19502',
    '葡超': '19503',
    '俄超': '19504',
    '比甲': '19505',
    '土超': '19506',
    '苏超': '19507',
    '丹超': '19508',
    '挪超': '19509',
    '芬超': '19510',
    '瑞士超': '19511',
    '奥超': '19512',
    '波兰超': '19513',
    '克罗甲': '19514',
    '罗甲': '19515',
    '希腊超': '19516',
    '捷克甲': '19517',
    '塞尔超': '19518',
    '乌克兰超': '19519',
    '匈牙利甲': '19520',
    '斯洛伐克超': '19521',
    '斯洛文甲': '19522',
    '波黑超': '19523',
    '日职丙': '19525',
    '韩K1': '19526',
    'K1联赛': '19526',
    '韩K2': '19527',
    'K2联赛': '19527',
    '澳超': '19528',
    '墨超': '19529',
    '美职联': '19530',
    '巴甲': '19531',
    '阿甲': '19532',
    '智甲': '19533',
    '哥甲': '19534',
    '秘鲁甲': '19535',
    '厄甲': '19536',
    '委内超': '19537',
    '乌拉超': '19538',
    '巴拉联': '19539',
    '哥伦甲': '19540',
}

# 获取联赛球队列表
team_ids = set()
league_id = LEAGUE_ID_MAP.get(LEAGUE, '')
if not league_id:
    print('  ⚠️ 联赛 "{}" 未在映射表中，尝试从球队赛程推断...'.format(LEAGUE))
    # 回退：从主队赛程中获取联赛球队
    try:
        url = 'https://liansai.500.com/team/{}/teamfixture/'.format(HOME_ID)
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            m = re.search(r'/zuqiu-(\d+)/', href)
            if m:
                league_id = m.group(1)
                LEAGUE_ID_MAP[LEAGUE] = league_id
                print('  从球队赛程推断联赛ID: {} = {}'.format(LEAGUE, league_id))
                break
    except Exception as e:
        print('  推断失败: {}'.format(e))

if league_id:
    league_url = 'https://liansai.500.com/zuqiu-{}/'.format(league_id)
    print('  联赛ID: {} -> {}'.format(LEAGUE, league_id))
    try:
        resp = sess.get(league_url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            m = re.search(r'/team/(\d+)', href)
            if m and '/teamfixture/' not in href:
                team_ids.add(m.group(1))
    except Exception as e:
        print('  获取联赛球队失败: {}'.format(e))
        # 回退到主队+客队
        team_ids = {HOME_ID, AWAY_ID}
else:
    print('  ⚠️ 无法获取联赛ID，回退到主队+客队')
    team_ids = {HOME_ID, AWAY_ID}

print('  联赛球队: {} 支'.format(len(team_ids)))

# 获取所有球队赛程
all_matches = []
for i, team_id in enumerate(sorted(team_ids), 1):
    url = 'https://liansai.500.com/team/{}/teamfixture/'.format(team_id)
    try:
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tr in soup.find_all('tr', attrs={'data': True}):
            try: data = json.loads(tr.get('data', '{}'))
            except: continue
            all_matches.append(data)
    except: pass
    time.sleep(0.2)
    if i % 4 == 0:
        print('  已获取 {}/{} 支球队...'.format(i, len(team_ids)))

print('  总记录: {} 条'.format(len(all_matches)))

# 筛选相同联赛（去重）
league_matches = []
seen_fid = set()
for d in all_matches:
    if d.get('SIMPLEGBNAME','') != LEAGUE: continue
    fid_check = str(d.get('FIXTUREID',''))
    if fid_check in seen_fid: continue
    seen_fid.add(fid_check)
    # 排除当前比赛
    if fid_check == str(FID): continue
    league_matches.append({
        'date': d.get('MATCHDATE',''),
        'home': d.get('HOMETEAMSXNAME',''),
        'away': d.get('AWAYTEAMSXNAME',''),
        'score': '{}:{}'.format(d.get('HOMESCORE',''), d.get('AWAYSCORE','')),
        'half': '{}:{}'.format(d.get('FIRSTHOMESCORE',''), d.get('FIRSTAWAYSCORE','')),
        'result': d.get('lpl_on',''),
        'pan': d.get('PAN',''),
        'bs': d.get('BS',''),
        'handicap': d.get('HANDICAPLINENAME',''),
        'fid': fid_check,
        'round': d.get('ROUND',''),
        'home_id': str(d.get('HOMETEAMID','')),
        'away_id': str(d.get('AWAYTEAMID','')),
    })
print('  同联赛: {} 场 (去重后)'.format(len(league_matches)))

# ============ Step 8: 筛选相同盘口 ============
print()
print('='*60)
print('第八步：相同联赛相同亚盘统计')
print('='*60)
print('澳门即时盘: {}'.format(MACAU_LINE))
print()

handicap_matches = []
seen_fid = set()
# 清洗MACAU_LINE：去掉"升""降"等后缀
macau_clean = MACAU_LINE.replace('升','').replace('降','').strip()
for m in league_matches:
    fid_check = m.get('fid', '')
    if fid_check in seen_fid:
        continue
    seen_fid.add(fid_check)
    # 匹配盘口：去掉"升""降"等后缀后精确比较
    h = (m.get('handicap') or '').replace('升','').replace('降','').strip()
    if h == macau_clean:
        handicap_matches.append(m)

print('  盘口匹配: {} 场'.format(len(handicap_matches)))

# ============ 逐场获取Step 8数据 ============
print()
print('逐场获取亚盘+欧赔数据...')
print()

step8_data = []
for i, m in enumerate(handicap_matches[:15], 1):
    fid = m.get('fid', '')
    if not fid: continue
    
    asian = ouzhi = None
    
    # Get yazhi
    try:
        r = sess.get('https://odds.500.com/fenxi/yazhi-{}.shtml'.format(fid), timeout=10)
        r.encoding = 'gbk'
        soup = BeautifulSoup(r.text, 'html.parser')
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                name = tds[1].get_text().strip()
                if '门' not in name and '澳' not in name: continue
                asian = {
                    'live_pan': clean_text(tds[4].get_text()),
                    'live_wh': clean_text(tds[3].get_text()),
                    'live_wa': clean_text(tds[5].get_text()),
                    'init_pan': clean_text(tds[10].get_text()),
                    'init_wh': clean_text(tds[9].get_text()),
                    'init_wa': clean_text(tds[11].get_text()),
                }
                break
            if asian: break
    except: pass
    
    # Get ouzhi
    try:
        r = sess.get('https://odds.500.com/fenxi/ouzhi-{}.shtml'.format(fid), timeout=10)
        r.encoding = 'gbk'
        soup = BeautifulSoup(r.text, 'html.parser')
        jc = iw = av = None
        all_companies = []
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
                company = {
                    'row': td0, 'name': td1,
                    'iw': '{:.2f}'.format(nums[0]), 'id': '{:.2f}'.format(nums[1]), 'il': '{:.2f}'.format(nums[2]),
                    'lw': '{:.2f}'.format(nums[3]), 'ld': '{:.2f}'.format(nums[4]), 'll': '{:.2f}'.format(nums[5]),
                }
                all_companies.append(company)
                if td0 == '1': jc = company
                elif td0 == '6': iw = company
                elif '\u767e' in td1 or '\u5e73' in td1: av = company
        ouzhi = {'jc': jc, 'iw': iw, 'av': av, 'all': all_companies}
    except: pass
    
    if asian or ouzhi:
        step8_data.append({**m, 'asian': asian, 'ouzhi': ouzhi})
        print('  #{} fid={}: {} vs {} {} 亚盘={}({}/{}) 欧赔={}'.format(
            i, fid, m['home'], m['away'], m['score'],
            asian['live_pan'] if asian else '-', asian['live_wh'] if asian else '-', asian['live_wa'] if asian else '-',
            '有' if ouzhi else '无'))
    time.sleep(0.3)

# ============ 获取百家欧赔数据（Step 19-23） ============
print()
print('获取百家欧赔数据 ({} 场)...'.format(len(league_matches)))
step19_data = []
for i, m in enumerate(league_matches, 1):
    fid = m.get('fid', '')
    if not fid: continue
    try:
        r = sess.get('https://odds.500.com/fenxi/ouzhi-{}.shtml'.format(fid), timeout=10)
        r.encoding = 'gbk'
        soup = BeautifulSoup(r.text, 'html.parser')
        jc = iw = av = None
        all_companies = []
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
                company = {
                    'row': td0, 'name': td1,
                    'iw': '{:.2f}'.format(nums[0]), 'id': '{:.2f}'.format(nums[1]), 'il': '{:.2f}'.format(nums[2]),
                    'lw': '{:.2f}'.format(nums[3]), 'ld': '{:.2f}'.format(nums[4]), 'll': '{:.2f}'.format(nums[5]),
                }
                all_companies.append(company)
                if td0 == '1': jc = company
                elif td0 == '6': iw = company
                elif '\u767e' in td1 or '\u5e73' in td1: av = company
        step19_data.append({**m, 'ouzhi': {'jc': jc, 'iw': iw, 'av': av, 'all': all_companies}})
        print('  #{} fid={}: {} vs {} {} 公司数={}'.format(i, fid, m['home'], m['away'], m['score'], len(all_companies)))
    except:
        print('  #{} fid={}: 获取失败'.format(i, fid))
    time.sleep(0.3)

# 当前比赛基准
print()
print('获取当前比赛基准...')
cur_ouzhi = None
cur_jc = cur_iw = cur_av = None
try:
    r = sess.get('https://odds.500.com/fenxi/ouzhi-{}.shtml'.format(FID), timeout=10)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, 'html.parser')
    jc = iw = av = None
    all_companies = []
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
            company = {
                'row': td0, 'name': td1,
                'iw': '{:.2f}'.format(nums[0]), 'id': '{:.2f}'.format(nums[1]), 'il': '{:.2f}'.format(nums[2]),
                'lw': '{:.2f}'.format(nums[3]), 'ld': '{:.2f}'.format(nums[4]), 'll': '{:.2f}'.format(nums[5]),
            }
            all_companies.append(company)
            if td0 == '1': jc = company
            elif td0 == '6': iw = company
            elif '\u767e' in td1 or '\u5e73' in td1: av = company
    cur_ouzhi = {'jc': jc, 'iw': iw, 'av': av, 'all': all_companies}
    cur_jc = jc
    cur_iw = iw
    cur_av = av
    if jc: print('  竞彩: {}/{}/{} -> {}/{}/{}'.format(jc['iw'],jc['id'],jc['il'],jc['lw'],jc['ld'],jc['ll']))
    if iw: print('  IWC: {}/{}/{} -> {}/{}/{}'.format(iw['iw'],iw['id'],iw['il'],iw['lw'],iw['ld'],iw['ll']))
    if av: print('  百家: {}/{}/{} -> {}/{}/{}'.format(av['iw'],av['id'],av['il'],av['lw'],av['ld'],av['ll']))
    print('  公司数: {}'.format(len(all_companies)))
except Exception as e:
    print('  错误: {}'.format(e))

# ============ 输出 ============
out = []

# ---------- Step 8: 亚盘统计明细 ----------
out.append('# 第八步：相同联赛相同亚盘统计')
out.append('')
out.append('\U0001f4c5 数据获取时间: ' + now)
out.append('\U0001f517 联赛: ' + LEAGUE)
out.append('\U0001f517 澳门即时盘: ' + MACAU_LINE)
out.append('')
out.append('### 输出A — 亚盘统计明细')
out.append('')
out.append('| 序号 | 比赛时间 | 对阵 | 赛果 | 初盘 | 终盘 | 初盘水位 | 终盘水位 | 盘路 | 主场水位差 | 客场水位差 |')
out.append('|------|---------|------|------|------|------|---------|---------|------|----------|----------|')

win_cover = lose_cover = push = 0
for i, m in enumerate(step8_data, 1):
    asian = m.get('asian')
    if not asian:
        out.append('| {} | {} | {} vs {} | {} | - | - | - | - | - | - | - |'.format(i, m['date'], m['home'], m['away'], m['score']))
        continue
    try:
        wh_diff = float(asian['live_wh']) - float(asian['init_wh'])
        wa_diff = float(asian['live_wa']) - float(asian['init_wa'])
    except:
        wh_diff = wa_diff = 0
    wh_s = '{:+.3f}'.format(wh_diff)
    wa_s = '{:+.3f}'.format(wa_diff)
    out.append('| {} | {} | {} vs {} | {} | {} | {} | {}/{} | {}/{} | {} | {} | {} |'.format(
        i, m['date'], m['home'], m['away'], m['score'], asian['init_pan'], asian['live_pan'],
        asian['init_wh'], asian['init_wa'], asian['live_wh'], asian['live_wa'], m['pan'], wh_s, wa_s))
    p = m.get('pan', '')
    if p == '赢': win_cover += 1
    elif p == '输': lose_cover += 1
    elif p in ['输半', '走']: push += 0.5
    elif p == '赢半': win_cover += 0.5
    elif p == '走半': push += 0.25
    else: push += 1

total = len(step8_data)
if total > 0:
    out.append('')
    out.append('### 亚盘统计汇总')
    out.append('- 总场次: {}场'.format(total))
    out.append('- 主队赢盘率: {:.1f}% ({}场)'.format(win_cover/total*100, win_cover))
    out.append('- 走盘率: {:.1f}% ({}场)'.format(push/total*100, push))
    out.append('- 客队赢盘率: {:.1f}% ({}场)'.format((total-win_cover-push)/total*100, int(total-win_cover-push)))

# ---------- Step 8: 欧赔明细（竞彩） ----------
out.append('')
out.append('### 输出B — 欧赔明细（竞彩官方）')
out.append('')
out.append('| 序号 | 公司 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负 | 终盘胜平负 | 盘路变化 | 盘路匹配度 |')
out.append('|------|------|---------|------|------|-----------|-----------|---------|-----------|')

jc_stats_8 = init_stats()
bench_jc_dir = dir_str3(cur_jc['iw'],cur_jc['id'],cur_jc['il'],cur_jc['lw'],cur_jc['ld'],cur_jc['ll']) if cur_jc else ''

for i, m in enumerate(step8_data, 1):
    ouzhi = m.get('ouzhi')
    res = m['result']
    if not ouzhi or not ouzhi.get('jc'):
        out.append('| {} | 竞彩官方 | {} | {} vs {} | {} | - | - | - | - |'.format(i, m['date'], m['home'], m['away'], res))
        continue
    jc = ouzhi['jc']
    hd = dir_str3(jc['iw'],jc['id'],jc['il'],jc['lw'],jc['ld'],jc['ll'])
    ml = match_level(bench_jc_dir, hd) if bench_jc_dir else '-'
    out.append('| {} | 竞彩官方 | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(
        i, m['date'], m['home'], m['away'], res, jc['iw'],jc['id'],jc['il'], jc['lw'],jc['ld'],jc['ll'], hd, ml))
    if ml != '-' and ml in jc_stats_8: jc_stats_8[ml][res] += 1

out.append('')
out.append('### 盘路匹配度统计')
out.append(stats_summary(jc_stats_8))

# ---------- Step 8: 让球指数 ----------
out.append('')
out.append('### 输出C — 让球指数·竞彩')
out.append('')
out.append('| 序号 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负 | 终盘胜平负 | 盘路变化 | 盘路匹配度 |')
out.append('|------|---------|------|------|-----------|-----------|---------|-----------|')

rq_stats_8 = init_stats()
for i, m in enumerate(step8_data, 1):
    fid = m.get('fid', '')
    res = m['result']
    if not fid:
        out.append('| {} | {} | {} vs {} | {} | - | - | - | - |'.format(i, m['date'], m['home'], m['away'], res))
        continue
    try:
        r = sess.get('https://odds.500.com/fenxi/rangqiu-{}.shtml'.format(fid), timeout=10)
        r.encoding = 'gbk'
        soup = BeautifulSoup(r.text, 'html.parser')
        jc_rq = None
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
                    jc_rq = {'iw': '{:.2f}'.format(nums[0]), 'id': '{:.2f}'.format(nums[1]), 'il': '{:.2f}'.format(nums[2]),
                             'lw': '{:.2f}'.format(nums[3]), 'ld': '{:.2f}'.format(nums[4]), 'll': '{:.2f}'.format(nums[5])}
                    break
            if jc_rq: break
        if jc_rq:
            hd = dir_str3(jc_rq['iw'],jc_rq['id'],jc_rq['il'],jc_rq['lw'],jc_rq['ld'],jc_rq['ll'])
            ml = match_level(bench_jc_dir, hd) if bench_jc_dir else '-'
            out.append('| {} | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(
                i, m['date'], m['home'], m['away'], res, jc_rq['iw'],jc_rq['id'],jc_rq['il'], jc_rq['lw'],jc_rq['ld'],jc_rq['ll'], hd, ml))
            if ml != '-' and ml in rq_stats_8: rq_stats_8[ml][res] += 1
        else:
            out.append('| {} | {} | {} vs {} | {} | - | - | - | - |'.format(i, m['date'], m['home'], m['away'], res))
    except:
        out.append('| {} | {} | {} vs {} | {} | - | - | - | - |'.format(i, m['date'], m['home'], m['away'], res))
    time.sleep(0.2)

out.append('')
out.append('### 盘路匹配度统计')
out.append(stats_summary(rq_stats_8))

# ---------- Step 8: 欧赔明细（Interwetten） ----------
out.append('')
out.append('### 输出D — 欧赔明细（Interwetten）')
out.append('')
out.append('| 序号 | 公司 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负 | 终盘胜平负 | 盘路变化 | 盘路匹配度 |')
out.append('|------|------|---------|------|------|-----------|-----------|---------|-----------|')

iw_stats_8 = init_stats()
bench_iw_dir = dir_str3(cur_iw['iw'],cur_iw['id'],cur_iw['il'],cur_iw['lw'],cur_iw['ld'],cur_iw['ll']) if cur_iw else ''

for i, m in enumerate(step8_data, 1):
    ouzhi = m.get('ouzhi')
    res = m['result']
    if not ouzhi or not ouzhi.get('iw'):
        out.append('| {} | Interwetten | {} | {} vs {} | {} | - | - | - | - |'.format(i, m['date'], m['home'], m['away'], res))
        continue
    iw = ouzhi['iw']
    hd = dir_str3(iw['iw'],iw['id'],iw['il'],iw['lw'],iw['ld'],iw['ll'])
    ml = match_level(bench_iw_dir, hd) if bench_iw_dir else '-'
    out.append('| {} | Interwetten | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(
        i, m['date'], m['home'], m['away'], res, iw['iw'],iw['id'],iw['il'], iw['lw'],iw['ld'],iw['ll'], hd, ml))
    if ml != '-' and ml in iw_stats_8: iw_stats_8[ml][res] += 1

out.append('')
out.append('### 盘路匹配度统计')
out.append(stats_summary(iw_stats_8))

# ============ Step 19-23: 百家对比 ============
# 基准：百家平均即时盘（整数+小数点第一位）
bench_av_live = None
if cur_av:
    bench_av_live = [cur_av['lw'], cur_av['ld'], cur_av['ll']]
    print()
    print('百家基准即时盘: {}/{}'.format(bench_av_live[0], bench_av_live[1]), bench_av_live[2])

# ---------- Step 19: 百家欧赔对比 ----------
out.append('')
out.append('# 第十九步：比赛C・百家欧赔对比')
out.append('')
out.append('\U0001f4c5 数据获取时间: ' + now)
out.append('\U0001f517 联赛: ' + LEAGUE)
out.append('\U0001f517 匹配规则: 本场百家即时盘 vs 历史百家终盘（整数+小数点第一位，胜平负任两项一致即匹配）')
out.append('')
out.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负赔率 | 终盘胜平负赔率 | 盘路变化 | 盘路匹配度 |')
out.append('|------|---------|------|------|---------------|---------------|---------|-----------|')

# 筛选与百家基准匹配的比赛
step19_filtered = []
for m in step19_data:
    ouzhi = m.get('ouzhi')
    if not ouzhi or not ouzhi.get('av'): continue
    av = ouzhi['av']
    # 比较即时盘（本场即时 vs 历史终盘）
    if match_odds_prefix(bench_av_live, [av['lw'], av['ld'], av['ll']]):
        step19_filtered.append(m)

print('  百家匹配: {} 场'.format(len(step19_filtered)))

av_stats_19 = init_stats()
bench_av_dir = dir_str3(cur_av['iw'],cur_av['id'],cur_av['il'],cur_av['lw'],cur_av['ld'],cur_av['ll']) if cur_av else ''

for i, m in enumerate(step19_filtered, 1):
    ouzhi = m.get('ouzhi')
    av = ouzhi['av']
    hd = dir_str3(av['iw'],av['id'],av['il'],av['lw'],av['ld'],av['ll'])
    ml = match_level(bench_av_dir, hd) if bench_av_dir else '-'
    out.append('| {} | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(
        LEAGUE, m['date'], m['home'], m['away'], m['result'],
        av['iw'],av['id'],av['il'], av['lw'],av['ld'],av['ll'], hd, ml))
    if ml != '-' and ml in av_stats_19: av_stats_19[ml][m['result']] += 1

out.append('')
out.append('### 盘路匹配度统计')
out.append(stats_summary(av_stats_19))

# ---------- Step 20: 竞彩官网 ----------
out.append('')
out.append('## 第二十步：比赛C・欧赔・竞彩官网')
out.append('')
out.append('🔗 匹配规则: 本场竞彩即时盘 vs 历史竞彩终盘（整数+小数点第一位，胜平负任两项一致即匹配）')
out.append('')
out.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负赔率 | 终盘胜平负赔率 | 盘路变化 | 盘路匹配度 |')
out.append('|------|---------|------|------|---------------|---------------|---------|-----------|')

# 独立筛选：竞彩即时盘 vs 历史竞彩终盘
bench_jc_live = None
if cur_jc:
    bench_jc_live = [cur_jc['lw'], cur_jc['ld'], cur_jc['ll']]
    print('  竞彩基准即时盘: {}/{} {}'.format(bench_jc_live[0], bench_jc_live[1], bench_jc_live[2]))

jc_filtered_20 = []
for m in step19_data:
    ouzhi = m.get('ouzhi')
    if not ouzhi or not ouzhi.get('jc'): continue
    jc = ouzhi['jc']
    if match_odds_prefix(bench_jc_live, [jc['lw'], jc['ld'], jc['ll']]):
        jc_filtered_20.append(m)

print('  竞彩匹配: {} 场'.format(len(jc_filtered_20)))

jc_stats_20 = init_stats()
bench_jc_dir = dir_str3(cur_jc['iw'],cur_jc['id'],cur_jc['il'],cur_jc['lw'],cur_jc['ld'],cur_jc['ll']) if cur_jc else ''

for i, m in enumerate(jc_filtered_20, 1):
    ouzhi = m.get('ouzhi')
    jc = ouzhi['jc']
    hd = dir_str3(jc['iw'],jc['id'],jc['il'],jc['lw'],jc['ld'],jc['ll'])
    ml = match_level(bench_jc_dir, hd) if bench_jc_dir else '-'
    out.append('| {} | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(
        LEAGUE, m['date'], m['home'], m['away'], m['result'],
        jc['iw'],jc['id'],jc['il'], jc['lw'],jc['ld'],jc['ll'], hd, ml))
    if ml != '-' and ml in jc_stats_20: jc_stats_20[ml][m['result']] += 1

out.append('')
out.append('### 盘路匹配度统计')
out.append(stats_summary(jc_stats_20))

# ---------- Step 21: Interwetten ----------
out.append('')
out.append('## 第二十一步：比赛C・欧赔・Interwetten')
out.append('')
out.append('🔗 匹配规则: 本场IW即时盘 vs 历史IW终盘（整数+小数点第一位，胜平负任两项一致即匹配）')
out.append('')
out.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负赔率 | 终盘胜平负赔率 | 盘路变化 | 盘路匹配度 |')
out.append('|------|---------|------|------|---------------|---------------|---------|-----------|')

# 独立筛选：IW即时盘 vs 历史IW终盘
bench_iw_live = None
if cur_iw:
    bench_iw_live = [cur_iw['lw'], cur_iw['ld'], cur_iw['ll']]
    print('  IW基准即时盘: {}/{} {}'.format(bench_iw_live[0], bench_iw_live[1], bench_iw_live[2]))

iw_filtered_21 = []
for m in step19_data:
    ouzhi = m.get('ouzhi')
    if not ouzhi or not ouzhi.get('iw'): continue
    iw = ouzhi['iw']
    if match_odds_prefix(bench_iw_live, [iw['lw'], iw['ld'], iw['ll']]):
        iw_filtered_21.append(m)

print('  IW匹配: {} 场'.format(len(iw_filtered_21)))

iw_stats_21 = init_stats()
bench_iw_dir = dir_str3(cur_iw['iw'],cur_iw['id'],cur_iw['il'],cur_iw['lw'],cur_iw['ld'],cur_iw['ll']) if cur_iw else ''

for i, m in enumerate(iw_filtered_21, 1):
    ouzhi = m.get('ouzhi')
    iw = ouzhi['iw']
    hd = dir_str3(iw['iw'],iw['id'],iw['il'],iw['lw'],iw['ld'],iw['ll'])
    ml = match_level(bench_iw_dir, hd) if bench_iw_dir else '-'
    out.append('| {} | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(
        LEAGUE, m['date'], m['home'], m['away'], m['result'],
        iw['iw'],iw['id'],iw['il'], iw['lw'],iw['ld'],iw['ll'], hd, ml))
    if ml != '-' and ml in iw_stats_21: iw_stats_21[ml][m['result']] += 1

out.append('')
out.append('### 盘路匹配度统计')
out.append(stats_summary(iw_stats_21))

# ---------- Step 23: 让球指数・竞彩 ----------
out.append('')
out.append('## 第二十三步：比赛C・让球指数・竞彩')
out.append('')
out.append('🔗 匹配规则: 本场让球即时盘 vs 历史让球终盘（整数+小数点第一位，胜平负任两项一致即匹配）')
out.append('')
out.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负赔率 | 终盘胜平负赔率 | 盘路变化 | 盘路匹配度 |')
out.append('|------|---------|------|------|---------------|---------------|---------|-----------|')

# 获取当前比赛让球指数基准
bench_jc_rq_live = None
if cur_jc:
    bench_jc_rq_live = [cur_jc['lw'], cur_jc['ld'], cur_jc['ll']]
    print('  让球基准即时盘: {}/{} {}'.format(bench_jc_rq_live[0], bench_jc_rq_live[1], bench_jc_rq_live[2]))

# 先为所有历史比赛抓取让球数据
print('  抓取历史让球数据 ({} 场)...'.format(len(step19_data)))
step19_with_rq = []
for i, m in enumerate(step19_data, 1):
    fid = m.get('fid', '')
    ouzhi = m.get('ouzhi')
    jc_rq = None
    if fid:
        try:
            r = sess.get('https://odds.500.com/fenxi/rangqiu-{}.shtml'.format(fid), timeout=10)
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
                        jc_rq = {'iw': '{:.2f}'.format(nums[0]), 'id': '{:.2f}'.format(nums[1]), 'il': '{:.2f}'.format(nums[2]),
                                 'lw': '{:.2f}'.format(nums[3]), 'ld': '{:.2f}'.format(nums[4]), 'll': '{:.2f}'.format(nums[5])}
                        break
                if jc_rq: break
        except: pass
    if jc_rq:
        step19_with_rq.append({**m, 'jc_rq': jc_rq})
    time.sleep(0.2)
    if i % 30 == 0:
        print('  已抓取 {}/{} 场...'.format(i, len(step19_data)))

print('  有让球数据: {} 场'.format(len(step19_with_rq)))

# 独立筛选：让球即时盘 vs 历史让球终盘
rq_filtered_23 = []
for m in step19_with_rq:
    jc_rq = m['jc_rq']
    if match_odds_prefix(bench_jc_rq_live, [jc_rq['lw'], jc_rq['ld'], jc_rq['ll']]):
        rq_filtered_23.append(m)

print('  让球匹配: {} 场'.format(len(rq_filtered_23)))

rq_stats_23 = init_stats()
bench_jc_dir = dir_str3(cur_jc['iw'],cur_jc['id'],cur_jc['il'],cur_jc['lw'],cur_jc['ld'],cur_jc['ll']) if cur_jc else ''

for i, m in enumerate(rq_filtered_23, 1):
    jc_rq = m['jc_rq']
    res = m['result']
    hd = dir_str3(jc_rq['iw'],jc_rq['id'],jc_rq['il'],jc_rq['lw'],jc_rq['ld'],jc_rq['ll'])
    ml = match_level(bench_jc_dir, hd) if bench_jc_dir else '-'
    out.append('| {} | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(
        LEAGUE, m['date'], m['home'], m['away'], res, jc_rq['iw'],jc_rq['id'],jc_rq['il'], jc_rq['lw'],jc_rq['ld'],jc_rq['ll'], hd, ml))
    if ml != '-' and ml in rq_stats_23: rq_stats_23[ml][res] += 1

out.append('')
out.append('### 盘路匹配度统计')
out.append(stats_summary(rq_stats_23))

# ============ Write ============
# Split into two files: step8 and step19-23
step8_lines = []
step19_23_lines = []
split_found = False
for line in out:
    if not split_found:
        if line.startswith('# 第十九步'):
            split_found = True
        else:
            step8_lines.append(line)
    else:
        step19_23_lines.append(line)

# Write step8 file
if OUTPUT_PATH:
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(step8_lines))
    print('输出(Step8): ' + OUTPUT_PATH)

# Write step19-23 file
if OUTPUT_PATH_1923:
    os.makedirs(os.path.dirname(OUTPUT_PATH_1923), exist_ok=True)
    with open(OUTPUT_PATH_1923, 'w', encoding='utf-8') as f:
        f.write('\n'.join(step19_23_lines))
    print('输出(Step19-23): ' + OUTPUT_PATH_1923)

print()
print('='*60)
print('完成！')
print('  Step 8: {} 场'.format(len(step8_data)))
print('  Step 19(百家): {} 场'.format(len(step19_filtered)))
print('  Step 20(竞彩): {} 场'.format(len(jc_filtered_20)))
print('  Step 21(IW):   {} 场'.format(len(iw_filtered_21)))
print('  Step 23(让球): {} 场'.format(len(rq_filtered_23)))
