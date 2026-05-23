# -*- coding: utf-8 -*-
"""Step 9-18 通用提取器 - 主队主场/客队客场分析
用法1: python step918_extractor.py <home_id> <away_id> <league> <fid> <macau_line> <output_dir>
用法2: python step918_extractor.py <match_dir>  (自动从 meta.json 读取参数)
"""
import sys, os, json
import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 支持两种调用方式
if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    MATCH_DIR = sys.argv[1]
    meta_path = os.path.join(MATCH_DIR, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        HOME_ID = meta.get('home_id', '')
        AWAY_ID = meta.get('away_id', '')
        LEAGUE = meta.get('league', '')
        FID = meta.get('fid', '')
        MACAU_LINE = meta.get('macau_line', '')
    else:
        HOME_ID = '2465'
        AWAY_ID = '848'
        LEAGUE = '瑞典超'
        FID = '1362643'
        MACAU_LINE = '一球/球半'
    OUTPUT_DIR = MATCH_DIR
    STEP9_OUT = os.path.join(MATCH_DIR, 'group04_teamA', 'step9_home_history.txt')
    STEP14_OUT = os.path.join(MATCH_DIR, 'group05_teamB', 'step14_away_history.txt')
else:
    HOME_ID = sys.argv[1] if len(sys.argv) > 1 else '2465'
    AWAY_ID = sys.argv[2] if len(sys.argv) > 2 else '848'
    LEAGUE = sys.argv[3] if len(sys.argv) > 3 else '瑞典超'
    FID = sys.argv[4] if len(sys.argv) > 4 else '1362643'
    MACAU_LINE = sys.argv[5] if len(sys.argv) > 5 else '一球/球半'
    OUTPUT_DIR = sys.argv[6] if len(sys.argv) > 6 else 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-04-27'
    STEP9_OUT = sys.argv[7] if len(sys.argv) > 7 else None
    STEP14_OUT = sys.argv[8] if len(sys.argv) > 8 else None

import requests, re, time, json
from bs4 import BeautifulSoup
from datetime import datetime

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
})
now = datetime.now().strftime('%Y-%m-%d %H:%M')

def gd(a, b):
    try:
        fa, fb = float(a), float(b)
        if fb < fa - 0.01: return '\u2b07'
        elif fb > fa + 0.01: return '\u2b06'
    except:

        pass
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


# ============ FID赔率缓存（由step24生成）============
_FID_CACHE = None

def _load_fid_cache():
    """加载step24生成的fid_odds_cache.json"""
    global _FID_CACHE
    if _FID_CACHE is not None:
        return True
    cache_path = os.path.join(MATCH_DIR, 'fid_odds_cache.json')
    if os.path.isfile(cache_path):
        try:
            with open(cache_path, encoding='utf-8') as f:
                _FID_CACHE = json.load(f)
            return True
        except:

            pass
    return False

def _from_cache(fid, data_type):
    """从缓存获取指定FID的赔率。data_type: 'jc','iw','av','rq'"""
    if not _load_fid_cache():
        return None
    entry = _FID_CACHE.get(str(fid), {})
    raw = entry.get(data_type)
    if not raw or not isinstance(raw, list) or len(raw) < 6:
        return None
    return {k: '{:.2f}'.format(v) for k, v in zip(['iw','id','il','lw','ld','ll'], raw)}

def fetch_odds(fid, use_cache=True):
    """Fetch ouzhi odds for fid, return {jc, iw, av}. use_cache=True时优先查缓存"""
    if use_cache:
        c_jc = _from_cache(fid, 'jc')
        c_iw = _from_cache(fid, 'iw')
        c_av = _from_cache(fid, 'av')
        if c_jc and c_iw and c_av:
            return {'jc': c_jc, 'iw': c_iw, 'av': c_av}
    try:
        url = 'https://odds.500.com/fenxi/ouzhi-{}.shtml'.format(fid)
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        jc = iw = av = None
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                td0 = tds[0].get_text().strip()
                td1 = tds[1].get_text().strip()
                nums = []
                for idx in [3,4,5,6,7,8]:
                    val = tds[idx].get_text().strip().replace('\u00a0','').replace(' ','')
                    try: nums.append(float(val))
                    except:

                        pass
                if len(nums) < 6: continue
                if td0 == '1':
                    jc = {k: '{:.2f}'.format(v) for k, v in zip(['iw','id','il','lw','ld','ll'], nums)}
                elif td0 == '6':
                    iw = {k: '{:.2f}'.format(v) for k, v in zip(['iw','id','il','lw','ld','ll'], nums)}
                elif '\u767e' in td1 or '\u5e73' in td1:
                    av = {k: '{:.2f}'.format(v) for k, v in zip(['iw','id','il','lw','ld','ll'], nums)}
        return {'jc': jc, 'iw': iw, 'av': av}
    except: return {'jc': None, 'iw': None, 'av': None}

def fetch_rangqiu(fid, use_cache=True):
    """Fetch rangqiu odds for fid, return jc or None. use_cache=True时优先查缓存"""
    if use_cache:
        cached = _from_cache(fid, 'rq')
        if cached:
            return cached
    try:
        url = 'https://odds.500.com/fenxi/rangqiu-{}.shtml'.format(fid)
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                if tds[0].get_text().strip() != '1': continue
                nums = []
                for idx in [4,5,6,7,8,9]:
                    val = tds[idx].get_text().strip().replace('\u00a0','').replace(' ','')
                    try: nums.append(float(val))
                    except:

                        pass
                if len(nums) >= 6:
                    return {k: '{:.2f}'.format(v) for k, v in zip(['iw','id','il','lw','ld','ll'], nums)}
        return None
    except: return None

def fetch_team(team_id):
    """Fetch all match data for team from liansai"""
    url = 'https://liansai.500.com/team/{}/teamfixture/'.format(team_id)
    try:
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        data_list = []
        for tr in soup.find_all('tr', attrs={'data': True}):
            try: data_list.append(json.loads(tr.get('data', '{}')))
            except: continue
        return data_list
    except: return []

def _handicap_match(src_hcp, target_hcp):
    """盘口精确匹配，处理格式差异（受让球半 vs 受球半）
    不做模糊映射，相同盘口才匹配"""
    if not src_hcp or not target_hcp:
        return False
    if src_hcp == target_hcp:
        return True
    def norm(s):
        s = s.replace(' ', '').replace('\u00a0', '')
        s = s.replace('/', '').replace('\uff0f', '')
        s = s.replace('\u8ba9\u53d7', '\u53d7')
        return s
    return norm(src_hcp) == norm(target_hcp)

def filter3(all_data, team_id, ha_type, league_name, macau_line):
    """3-layer filter: 主客场 + 联赛 + 澳门盘口
    联赛名做模糊匹配（韩职 vs K1联赛，日职 vs J1联赛等）
    盘口做模糊匹配（受球半 vs 受让球半，半/一 vs 半球/一球）
    采用 fallback 机制：3层过滤为空 → 2层 → 1层
    """
    pure_macau = ''
    if macau_line:
        pure_macau = macau_line.replace(' 降', '').replace(' 升', '').strip()
    
    def apply_filters(data, layer):
        """Apply filters up to specified layer (1, 2, or 3)"""
        results = []
        for d in data:
            # Layer 1: 主客场 (always required)
            if ha_type == 'home':
                if str(d.get('HOMETEAMID','')) != str(team_id): continue
            else:
                if str(d.get('AWAYTEAMID','')) != str(team_id): continue
            # Layer 2: 联赛（模糊匹配）
            if layer >= 2:
                src_lg = d.get('SIMPLEGBNAME','')
                if not _league_match(src_lg, league_name): continue
            # Layer 3: 澳门盘口（模糊匹配）
            if layer >= 3 and pure_macau:
                hcp = d.get('HANDICAPLINENAME') or ''
                if not _handicap_match(pure_macau, hcp): continue
            results.append(d)
        return results
    
    # Fallback: try 3 layers, then 2, then 1
    for layer in [3, 2, 1]:
        filtered = apply_filters(all_data, layer)
        if filtered:
            return [{
                'date': d.get('MATCHDATE',''),
                'home': d.get('HOMETEAMSXNAME',''),
                'away': d.get('AWAYTEAMSXNAME',''),
                'score': '{}:{}'.format(d.get('HOMESCORE',''), d.get('AWAYSCORE','')),
                'half': '{}:{}'.format(d.get('HOMEHTSCORE',''), d.get('AWAYHTSCORE','')),
                'result': d.get('lpl_on',''),
                'pan': d.get('PAN',''),
                'bs': d.get('BS',''),
                'handicap': d.get('HANDICAPLINENAME') or '',
                'fid': d.get('FIXTUREID',''),
                'src_league': d.get('SIMPLEGBNAME',''),
            } for d in filtered]
    return []

from _league_util import _league_match

# ======================== MAIN ========================

# --- Current match benchmark ---
print('当前比赛基准赔率:')
cur = fetch_odds(FID, use_cache=False)
b_jc = dir_str3(cur['jc']['iw'],cur['jc']['id'],cur['jc']['il'],cur['jc']['lw'],cur['jc']['ld'],cur['jc']['ll']) if cur['jc'] else ''
b_iw = dir_str3(cur['iw']['iw'],cur['iw']['id'],cur['iw']['il'],cur['iw']['lw'],cur['iw']['ld'],cur['iw']['ll']) if cur['iw'] else ''
b_av = dir_str3(cur['av']['iw'],cur['av']['id'],cur['av']['il'],cur['av']['lw'],cur['av']['ld'],cur['av']['ll']) if cur['av'] else ''
if cur['jc']: print('  竞彩 {} -> {} ({})'.format(cur['jc']['iw']+'/'+cur['jc']['id']+'/'+cur['jc']['il'], cur['jc']['lw']+'/'+cur['jc']['ld']+'/'+cur['jc']['ll'], b_jc))
if cur['iw']: print('  IWC  {} -> {} ({})'.format(cur['iw']['iw']+'/'+cur['iw']['id']+'/'+cur['iw']['il'], cur['iw']['lw']+'/'+cur['iw']['ld']+'/'+cur['iw']['ll'], b_iw))
if cur['av']: print('  百家 {} -> {} ({})'.format(cur['av']['iw']+'/'+cur['av']['id']+'/'+cur['av']['il'], cur['av']['lw']+'/'+cur['av']['ld']+'/'+cur['av']['ll'], b_av))

# --- Fetch all team data ---
print()
print('获取主队数据...')
all_home = fetch_team(HOME_ID)
print('  主队总记录: {} 条'.format(len(all_home)))

print('获取客队数据...')
all_away = fetch_team(AWAY_ID)
print('  客队总记录: {} 条'.format(len(all_away)))

# --- Step 9: 主队主场 ---
home_f = filter3(all_home, HOME_ID, 'home', LEAGUE, MACAU_LINE)
print()
print('='*60)
print('第九步：主队主场·相同联赛·澳门亚盘同赔')
print('='*60)
print('筛选: 主场(HOMETEAMID={}) + 联赛({}) + 盘口({})'.format(HOME_ID, LEAGUE, MACAU_LINE))
print('过滤后: {} 场'.format(len(home_f)))

w = sum(1 for m in home_f if m['result']=='胜')
dr = sum(1 for m in home_f if m['result']=='平')
lo = sum(1 for m in home_f if m['result']=='负')
tt = len(home_f)
wp = sum(1 for m in home_f if m['pan'] in ['赢','赢半'])
tg = sum(int(m['score'].split(':')[0]) for m in home_f if ':' in m['score'] and m['score'].split(':')[0].isdigit())
tc = sum(int(m['score'].split(':')[1]) for m in home_f if ':' in m['score'] and m['score'].split(':')[1].isdigit())

out = []
out.append('# 第九步：主队主场·相同联赛·澳门亚盘同赔')
out.append('')
out.append('\U0001f4c5 数据获取时间: ' + now)
out.append('\U0001f517 主队: Team ID ' + HOME_ID)
out.append('\U0001f517 联赛: ' + LEAGUE)
out.append('\U0001f517 澳门盘口: ' + MACAU_LINE)
out.append('')
out.append('### 筛选结果 (共{} 场)'.format(tt))
out.append('')
out.append('| 序号 | 日期 | 对阵 | 比分 | 半场 | 赛果 | 盘口 | 盘路 | 大小 |')
out.append('|------|------|------|------|------|------|------|------|------|')
for i, m in enumerate(home_f[:30], 1):
    out.append('| {} | {} | {} vs {} | {} | {} | {} | {} | {} | {} |'.format(
        i, m['date'], m['home'], m['away'], m['score'], m['half'], m['result'], m['handicap'], m['pan'], m['bs']))
out.append('')
out.append('### 统计: 共{} 场 | 胜率{}% | 赢盘率{}% | 场均进球{} | 场均失球{}'.format(
    tt, round(w/max(tt,1)*100,1), round(wp/max(tt,1)*100,1), round(tg/max(tt,1),1), round(tc/max(tt,1),1)))

# --- Step 10-13: 主队欧赔/让球 ---
print()
print('='*60)
print('第十-十二步：主队比赛欧赔分析')
print('='*60)

# Collect all odds data first
all_odds_home = []
for i, m in enumerate(home_f[:15], 1):
    fid = m.get('fid', '')
    if not fid:
        all_odds_home.append((i, m, None, None))
        continue
    time.sleep(0.5)
    odds = fetch_odds(fid, use_cache=True)
    rq = fetch_rangqiu(fid, use_cache=True)
    all_odds_home.append((i, m, odds, rq))

# Step 10: JC
out.append('')
out.append('## 第十步：竞彩官方欧赔')
out.append('')
out.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负 | 终盘胜平负 | 盘路变化 | 盘路匹配度 |')
out.append('|------|------|------|------|--------------|--------------|----------|------------|')
jc_s = init_stats()
for i, m, odds, rq in all_odds_home:
    res = m['result']
    if not odds or not odds['jc']:
        out.append('| {} | {} | {} vs {} | {} | - | - | - | - |'.format(i, m['date'], m['home'], m['away'], res))
        continue
    d = odds['jc']
    hd = dir_str3(d['iw'],d['id'],d['il'],d['lw'],d['ld'],d['ll'])
    ml = match_level(b_jc, hd) if b_jc else '-'
    out.append('| {} | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(i, m['date'], m['home'], m['away'], res, d['iw'],d['id'],d['il'], d['lw'],d['ld'],d['ll'], hd, ml))
    if ml != '-' and ml in jc_s: jc_s[ml][res] += 1

# Step 11: IWC
out.append('')
out.append('## 第十一步：Interwetten欧赔')
out.append('')
out.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负 | 终盘胜平负 | 盘路变化 | 盘路匹配度 |')
out.append('|------|------|------|------|--------------|--------------|----------|------------|')
iw_s = init_stats()
for i, m, odds, rq in all_odds_home:
    res = m['result']
    if not odds or not odds['iw']:
        out.append('| {} | {} | {} vs {} | {} | - | - | - | - |'.format(i, m['date'], m['home'], m['away'], res))
        continue
    d = odds['iw']
    hd = dir_str3(d['iw'],d['id'],d['il'],d['lw'],d['ld'],d['ll'])
    ml = match_level(b_iw, hd) if b_iw else '-'
    out.append('| {} | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(i, m['date'], m['home'], m['away'], res, d['iw'],d['id'],d['il'], d['lw'],d['ld'],d['ll'], hd, ml))
    if ml != '-' and ml in iw_s: iw_s[ml][res] += 1

# Step 12: 百家
out.append('')
out.append('## 第十二步：百家平均欧赔')
out.append('')
out.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负 | 终盘胜平负 | 盘路变化 | 盘路匹配度 |')
out.append('|------|------|------|------|--------------|--------------|----------|------------|')
av_s = init_stats()
for i, m, odds, rq in all_odds_home:
    res = m['result']
    if not odds or not odds['av']:
        out.append('| {} | {} | {} vs {} | {} | - | - | - | - |'.format(i, m['date'], m['home'], m['away'], res))
        continue
    d = odds['av']
    hd = dir_str3(d['iw'],d['id'],d['il'],d['lw'],d['ld'],d['ll'])
    ml = match_level(b_av, hd) if b_av else '-'
    out.append('| {} | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(i, m['date'], m['home'], m['away'], res, d['iw'],d['id'],d['il'], d['lw'],d['ld'],d['ll'], hd, ml))
    if ml != '-' and ml in av_s: av_s[ml][res] += 1

# Step 13: 让球
out.append('')
out.append('## 第十三步：竞彩让球指数')
out.append('')
out.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负 | 终盘胜平负 | 盘路变化 | 盘路匹配度 |')
out.append('|------|------|------|------|--------------|--------------|----------|------------|')
rq_s = init_stats()
for i, m, odds, rq in all_odds_home:
    res = m['result']
    if not rq:
        out.append('| {} | {} | {} vs {} | {} | - | - | - | - |'.format(i, m['date'], m['home'], m['away'], res))
        continue
    hd = dir_str3(rq['iw'],rq['id'],rq['il'],rq['lw'],rq['ld'],rq['ll'])
    ml = match_level(b_jc, hd) if b_jc else '-'
    out.append('| {} | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(i, m['date'], m['home'], m['away'], res, rq['iw'],rq['id'],rq['il'], rq['lw'],rq['ld'],rq['ll'], hd, ml))
    if ml != '-' and ml in rq_s: rq_s[ml][res] += 1

out.append('')
out.append('### 盘路匹配度统计')
out.append('')
out.append('**竞彩**')
out.append(stats_summary(jc_s))
out.append('')
out.append('**Interwetten**')
out.append(stats_summary(iw_s))
out.append('')
out.append('**百家平均**')
out.append(stats_summary(av_s))
out.append('')
out.append('**让球指数**')
out.append(stats_summary(rq_s))

# --- Step 14: 客队客场 ---
away_f = filter3(all_away, AWAY_ID, 'away', LEAGUE, MACAU_LINE)
print()
print('='*60)
print('第十四步：客队客场·相同联赛·澳门亚盘同赔')
print('='*60)
print('筛选: 客场(AWAYTEAMID={}) + 联赛({}) + 盘口({})'.format(AWAY_ID, LEAGUE, MACAU_LINE))
print('过滤后: {} 场'.format(len(away_f)))

w2 = sum(1 for m in away_f if m['result']=='胜')
dr2 = sum(1 for m in away_f if m['result']=='平')
lo2 = sum(1 for m in away_f if m['result']=='负')
tt2 = len(away_f)
wp2 = sum(1 for m in away_f if m['pan'] in ['赢','赢半'])
tg2 = sum(int(m['score'].split(':')[0]) for m in away_f if ':' in m['score'] and len(m['score'].split(':'))==2 and m['score'].split(':')[0].isdigit())
tc2 = sum(int(m['score'].split(':')[1]) for m in away_f if ':' in m['score'] and len(m['score'].split(':'))==2 and m['score'].split(':')[1].isdigit())

out.append('')
out.append('# 第十四步：客队客场·相同联赛·澳门亚盘同赔')
out.append('')
out.append('\U0001f4c5 数据获取时间: ' + now)
out.append('\U0001f517 客队: Team ID ' + AWAY_ID)
out.append('\U0001f517 联赛: ' + LEAGUE)
out.append('\U0001f517 澳门盘口: ' + MACAU_LINE)
out.append('')
out.append('### 筛选结果 (共{} 场)'.format(tt2))
out.append('')
out.append('| 序号 | 日期 | 对阵 | 比分 | 半场 | 赛果 | 盘口 | 盘路 | 大小 |')
out.append('|------|------|------|------|------|------|------|------|------|')
for i, m in enumerate(away_f[:30], 1):
    out.append('| {} | {} | {} vs {} | {} | {} | {} | {} | {} | {} |'.format(
        i, m['date'], m['home'], m['away'], m['score'], m['half'], m['result'], m['handicap'], m['pan'], m['bs']))
out.append('')
out.append('### 统计: 共{} 场 | 胜率{}% | 赢盘率{}% | 场均进球{} | 场均失球{}'.format(
    tt2, round(w2/max(tt2,1)*100,1), round(wp2/max(tt2,1)*100,1), round(tg2/max(tt2,1),1), round(tc2/max(tt2,1),1)))

# --- Step 15-18: 客队欧赔/让球 ---
print()
print('='*60)
print('第十五-十八步：客队比赛欧赔分析')
print('='*60)

# Collect all odds data first
all_odds_away = []
for i, m in enumerate(away_f[:15], 1):
    fid = m.get('fid', '')
    if not fid:
        all_odds_away.append((i, m, None, None))
        continue
    time.sleep(0.5)
    odds = fetch_odds(fid, use_cache=True)
    rq = fetch_rangqiu(fid, use_cache=True)
    all_odds_away.append((i, m, odds, rq))

# Step 15: JC
out.append('')
out.append('## 第十五步：竞彩官方欧赔')
out.append('')
out.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负 | 终盘胜平负 | 盘路变化 | 盘路匹配度 |')
out.append('|------|------|------|------|--------------|--------------|----------|------------|')
jc_s2 = init_stats()
for i, m, odds, rq in all_odds_away:
    res = m['result']
    if not odds or not odds['jc']:
        out.append('| {} | {} | {} vs {} | {} | - | - | - | - |'.format(i, m['date'], m['home'], m['away'], res))
        continue
    d = odds['jc']
    hd = dir_str3(d['iw'],d['id'],d['il'],d['lw'],d['ld'],d['ll'])
    ml = match_level(b_jc, hd) if b_jc else '-'
    out.append('| {} | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(i, m['date'], m['home'], m['away'], res, d['iw'],d['id'],d['il'], d['lw'],d['ld'],d['ll'], hd, ml))
    if ml != '-' and ml in jc_s2: jc_s2[ml][res] += 1

# Step 16: IWC
out.append('')
out.append('## 第十六步：Interwetten欧赔')
out.append('')
out.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负 | 终盘胜平负 | 盘路变化 | 盘路匹配度 |')
out.append('|------|------|------|------|--------------|--------------|----------|------------|')
iw_s2 = init_stats()
for i, m, odds, rq in all_odds_away:
    res = m['result']
    if not odds or not odds['iw']:
        out.append('| {} | {} | {} vs {} | {} | - | - | - | - |'.format(i, m['date'], m['home'], m['away'], res))
        continue
    d = odds['iw']
    hd = dir_str3(d['iw'],d['id'],d['il'],d['lw'],d['ld'],d['ll'])
    ml = match_level(b_iw, hd) if b_iw else '-'
    out.append('| {} | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(i, m['date'], m['home'], m['away'], res, d['iw'],d['id'],d['il'], d['lw'],d['ld'],d['ll'], hd, ml))
    if ml != '-' and ml in iw_s2: iw_s2[ml][res] += 1

# Step 17: 百家
out.append('')
out.append('## 第十七步：百家平均欧赔')
out.append('')
out.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负 | 终盘胜平负 | 盘路变化 | 盘路匹配度 |')
out.append('|------|------|------|------|--------------|--------------|----------|------------|')
av_s2 = init_stats()
for i, m, odds, rq in all_odds_away:
    res = m['result']
    if not odds or not odds['av']:
        out.append('| {} | {} | {} vs {} | {} | - | - | - | - |'.format(i, m['date'], m['home'], m['away'], res))
        continue
    d = odds['av']
    hd = dir_str3(d['iw'],d['id'],d['il'],d['lw'],d['ld'],d['ll'])
    ml = match_level(b_av, hd) if b_av else '-'
    out.append('| {} | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(i, m['date'], m['home'], m['away'], res, d['iw'],d['id'],d['il'], d['lw'],d['ld'],d['ll'], hd, ml))
    if ml != '-' and ml in av_s2: av_s2[ml][res] += 1

# Step 18: 让球
out.append('')
out.append('## 第十八步：竞彩让球指数')
out.append('')
out.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负 | 终盘胜平负 | 盘路变化 | 盘路匹配度 |')
out.append('|------|------|------|------|--------------|--------------|----------|------------|')
rq_s2 = init_stats()
for i, m, odds, rq in all_odds_away:
    res = m['result']
    if not rq:
        out.append('| {} | {} | {} vs {} | {} | - | - | - | - |'.format(i, m['date'], m['home'], m['away'], res))
        continue
    hd = dir_str3(rq['iw'],rq['id'],rq['il'],rq['lw'],rq['ld'],rq['ll'])
    ml = match_level(b_jc, hd) if b_jc else '-'
    out.append('| {} | {} | {} vs {} | {} | {}/{}/{} | {}/{}/{} | {} | {} |'.format(i, m['date'], m['home'], m['away'], res, rq['iw'],rq['id'],rq['il'], rq['lw'],rq['ld'],rq['ll'], hd, ml))
    if ml != '-' and ml in rq_s2: rq_s2[ml][res] += 1

out.append('')
out.append('### 盘路匹配度统计')
out.append('')
out.append('**竞彩**')
out.append(stats_summary(jc_s2))
out.append('')
out.append('**Interwetten**')
out.append(stats_summary(iw_s2))
out.append('')
out.append('**百家平均**')
out.append(stats_summary(av_s2))
out.append('')
out.append('**让球指数**')
out.append(stats_summary(rq_s2))

# --- Write output ---
# Split into two files: steps 9-13 (home) and steps 14-18 (away)
home_out = []
away_out = []

# Find the split point (step 14 heading)
split_idx = None
for i, line in enumerate(out):
    if '# 第十四步' in line:
        split_idx = i
        break

if split_idx is not None:
    home_out = out[:split_idx]
    away_out = out[split_idx:]
else:
    home_out = out

# Write home team file (steps 9-13)
if STEP9_OUT:
    home_path = STEP9_OUT
else:
    home_path = os.path.join(OUTPUT_DIR, 'group04_teamA', 'step09_13_teamA.md')
os.makedirs(os.path.dirname(home_path), exist_ok=True)
with open(home_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(home_out))
print('输出(主队): ' + home_path)

# Write away team file (steps 14-18)
if STEP14_OUT:
    away_path = STEP14_OUT
else:
    away_path = os.path.join(OUTPUT_DIR, 'group05_teamB', 'step14_18_teamB.md')
os.makedirs(os.path.dirname(away_path), exist_ok=True)
with open(away_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(away_out))
print('输出(客队): ' + away_path)
