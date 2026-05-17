# -*- coding: utf-8 -*-
"""
轻量补数：只补5月5号 第8步 + 第19-23步
按联赛分组，联赛赛程只抓一次，逐场匹配盘口+抓赔率
"""
import os, sys, re, json, time, requests
from bs4 import BeautifulSoup
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR = r'jingcai\tasks\2026-05-05\data'
sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
})

# 联赛ID映射（用修复后的）
LEAGUE_ID_MAP = {
    '韩职': '19554', '芬超': '19510', '芬兰超级联赛': '19510',
    '荷乙': '19502', '沙特职业联赛': '19506', '沙特': '19506',
    '欧冠': '19538', '解放者杯': '19546', '南美解放者杯': '19546',
    '英超': '19495', '西甲': '19496', '德甲': '19497', '意甲': '19498',
    '法甲': '19499', '荷甲': '19502', '葡超': '19503',
}

# 联赛名模糊匹配
def league_match(src, target):
    if src == target: return True
    if not src or not target: return False
    if len(target) >= 2 and target in src: return True
    if len(src) >= 2 and src in target: return True
    return False

# 盘口匹配（去掉升降水标记后比较）
def handicap_match(a, b):
    ca = (a or '').replace('升', '').replace('降', '').strip()
    cb = (b or '').replace('升', '').replace('降', '').strip()
    return ca == cb

def clean_text(s):
    return s.replace('\u00a0', '').replace('\u2193', '').replace('\u2191', '').replace('\u2b07', '').replace('\u2b06', '').replace(' ', '').strip()

def dir_str(a, b):
    try:
        fa, fb = float(a), float(b)
        if fb < fa - 0.01: return '\u2b07'
        elif fb > fa + 0.01: return '\u2b06'
    except: pass
    return '\u27a1'

def dir_str3(iw, id_, il, lw, ld, ll):
    return dir_str(iw, lw) + dir_str(id_, ld) + dir_str(il, ll)

def fetch_odds(fid):
    """获取欧赔"""
    try:
        r = sess.get(f'https://odds.500.com/fenxi/ouzhi-{fid}.shtml', timeout=15)
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
                    try: nums.append(float(tds[idx].get_text().strip().replace('\u00a0','')))
                    except: pass
                if len(nums) < 6: continue
                if td0 == '1':
                    jc = {k: '{:.2f}'.format(v) for k, v in zip(['iw','id','il','lw','ld','ll'], nums)}
                elif td0 == '6':
                    iw = {k: '{:.2f}'.format(v) for k, v in zip(['iw','id','il','lw','ld','ll'], nums)}
                elif '平均' in td1:
                    av = {k: '{:.2f}'.format(v) for k, v in zip(['iw','id','il','lw','ld','ll'], nums)}
        return {'jc': jc, 'iw': iw, 'av': av}
    except: return {'jc': None, 'iw': None, 'av': None}

def match_level(bench, hist):
    if not bench or not hist or len(bench) != 3 or len(hist) != 3: return '-'
    same = sum(1 for a, b in zip(bench, hist) if a == b)
    if same == 3: return '高'
    elif same >= 2: return '中'
    return '低'

# ============ MAIN ============

# 1. 读取所有meta.json，按联赛分组
matches_by_league = {}
all_matches = []
for d in sorted(os.listdir(DATA_DIR)):
    match_dir = os.path.join(DATA_DIR, d)
    if not os.path.isdir(match_dir): continue
    
    meta_file = os.path.join(match_dir, 'meta.json')
    if not os.path.isfile(meta_file): continue
    
    with open(meta_file, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    league = meta.get('league', '')
    macau = meta.get('macau_line', '').replace('升', '').replace('降', '').strip()
    fid = meta.get('fid', '')
    
    if not league or not macau:
        print(f"  SKIP {meta.get('matchnum','')} : 缺少league或macau_line")
        continue
    
    match_info = {
        'match_num': meta.get('matchnum', ''),
        'league': league,
        'macau': macau,
        'fid': fid,
        'home': meta.get('home', ''),
        'away': meta.get('away', ''),
        'dir': d,
        'match_dir': match_dir,
    }
    all_matches.append(match_info)
    
    if league not in matches_by_league:
        matches_by_league[league] = []
    matches_by_league[league].append(match_info)

print(f"\n共 {len(all_matches)} 场比赛，{len(matches_by_league)} 个联赛")

# 2. 按联赛获取赛程数据（只抓一次）
league_matches_cache = {}
for league, league_matches in matches_by_league.items():
    print(f"\n{'='*50}")
    print(f"联赛: {league}")
    
    league_id = LEAGUE_ID_MAP.get(league, '')
    if not league_id:
        print(f"  ⚠️ 联赛ID未知，跳过")
        continue
    
    # 获取联赛赛程
    try:
        url = f'https://liansai.500.com/zuqiu-{league_id}/'
        print(f"  获取联赛赛程: {url}")
        resp = sess.get(url, timeout=15)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        all_data = []
        for tr in soup.find_all('tr', attrs={'data': True}):
            try: all_data.append(json.loads(tr.get('data', '{}')))
            except: continue
        
        print(f"  总记录: {len(all_data)} 条")
        
        # 筛选同联赛（排除当前比赛）
        current_fids = {m['fid'] for m in league_matches}
        filtered = []
        for d in all_data:
            fid = str(d.get('FIXTUREID', ''))
            if fid in current_fids: continue
            if not league_match(d.get('SIMPLEGBNAME', ''), league): continue
            hcp = (d.get('HANDICAPLINENAME') or '').replace('升','').replace('降','').strip()
            filtered.append({
                'date': d.get('MATCHDATE', ''),
                'home': d.get('HOMETEAMSXNAME', ''),
                'away': d.get('AWAYTEAMSXNAME', ''),
                'score': f"{d.get('HOMESCORE','')}:{d.get('AWAYSCORE','')}",
                'result': d.get('lpl_on', ''),
                'handicap': hcp,
                'fid': fid,
                'pan': d.get('PAN', ''),
                'bs': d.get('BS', ''),
            })
        
        league_matches_cache[league] = filtered
        print(f"  同联赛(去当前): {len(filtered)} 场")
    except Exception as e:
        print(f"  ERROR: {e}")

# 3. 逐场匹配盘口 + 抓赔率
for league, league_matches in matches_by_league.items():
    print(f"\n{'='*50}")
    print(f"联赛: {league}")
    
    cached = league_matches_cache.get(league, [])
    
    for m in league_matches:
        print(f"\n  [{m['match_num']}] {m['home']}vs{m['away']} 澳门: {m['macau']}")
        
        # 匹配盘口
        matched = [c for c in cached if handicap_match(c['handicap'], m['macau'])]
        print(f"    盘口匹配: {len(matched)} 场")
        
        # 抓前15场的欧赔
        odds_data = []
        for i, hist in enumerate(matched[:15], 1):
            fid = hist.get('fid', '')
            if not fid:
                odds_data.append((i, hist, None))
                continue
            odds = fetch_odds(fid)
            odds_data.append((i, hist, odds))
            time.sleep(0.5)
        
        # 获取当前比赛基准赔率
        cur = fetch_odds(m['fid'])
        b_jc = dir_str3(cur['jc']['iw'], cur['jc']['id'], cur['jc']['il'],
                        cur['jc']['lw'], cur['jc']['ld'], cur['jc']['ll']) if cur['jc'] else ''
        
        # 生成 step8 输出
        out = []
        out.append('# 第八步：相同联赛相同亚盘统计')
        out.append('')
        out.append(f"📅 数据获取时间: {time.strftime('%Y-%m-%d %H:%M')}")
        out.append(f"🔗 联赛: {league}")
        out.append(f"🔗 澳门即时盘: {m['macau']}")
        out.append('')
        out.append('### 输出A — 亚盘统计明细')
        out.append('')
        out.append('| 序号 | 比赛时间 | 对阵 | 赛果 | 初盘 | 终盘 | 初盘水位 | 终盘水位 | 盘路 | 主场水位差 | 客场水位差 |')
        out.append('|------|---------|------|------|------|------|---------|---------|------|----------|----------|')
        
        for i, hist, odds in odds_data:
            out.append(f"| {i} | {hist['date']} | {hist['home']}vs{hist['away']} | {hist['score']} | {hist['handicap']} | {hist['handicap']} | - | - | {hist['result']} | - | - |")
        
        out.append('')
        out.append('### 输出B — 欧赔明细（竞彩官方）')
        out.append('')
        out.append('| 序号 | 公司 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负 | 终盘胜平负 | 盘路变化 | 盘路匹配度 |')
        out.append('|------|------|---------|------|------|-----------|-----------|---------|-----------|')
        
        jc_stats = {'高': {'胜':0,'平':0,'负':0}, '中': {'胜':0,'平':0,'负':0}, '低': {'胜':0,'平':0,'负':0}}
        iw_stats = {'高': {'胜':0,'平':0,'负':0}, '中': {'胜':0,'平':0,'负':0}, '低': {'胜':0,'平':0,'负':0}}
        av_stats = {'高': {'胜':0,'平':0,'负':0}, '中': {'胜':0,'平':0,'负':0}, '低': {'胜':0,'平':0,'负':0}}
        
        for i, hist, odds in odds_data:
            res = hist['result']
            if odds and odds['jc']:
                d = odds['jc']
                hd = dir_str3(d['iw'], d['id'], d['il'], d['lw'], d['ld'], d['ll'])
                ml = match_level(b_jc, hd) if b_jc else '-'
                out.append(f"| {i} | 竞彩官方 | {hist['date']} | {hist['home']}vs{hist['away']} | {res} | {d['iw']}/{d['id']}/{d['il']} | {d['lw']}/{d['ld']}/{d['ll']} | {hd} | {ml} |")
                if ml in jc_stats: jc_stats[ml][res] += 1
            else:
                out.append(f"| {i} | - | {hist['date']} | {hist['home']}vs{hist['away']} | {res} | - | - | - | - |")
            
            if odds and odds['iw']:
                d = odds['iw']
                hd = dir_str3(d['iw'], d['id'], d['il'], d['lw'], d['ld'], d['ll'])
                ml = match_level(b_jc, hd) if b_jc else '-'
                if ml in iw_stats: iw_stats[ml][res] += 1
            
            if odds and odds['av']:
                d = odds['av']
                hd = dir_str3(d['iw'], d['id'], d['il'], d['lw'], d['ld'], d['ll'])
                ml = match_level(b_jc, hd) if b_jc else '-'
                if ml in av_stats: av_stats[ml][res] += 1
        
        out.append('')
        out.append('### 盘路匹配度统计')
        out.append('')
        for label, stats in [('竞彩', jc_stats), ('Interwetten', iw_stats), ('百家平均', av_stats)]:
            out.append(f'**{label}**')
            for lv in ['高', '中', '低']:
                x = stats.get(lv, {})
                t = sum(x.values())
                if t > 0:
                    out.append(f"  {lv}盘路: 胜{x.get('胜',0)} 平{x.get('平',0)} 负{x.get('负',0)} (共{t}场)")
            if t == 0:
                out.append('  无数据')
            out.append('')
        
        # 生成 step19-23 输出（百家对比 + 竞彩 + IW）
        out1923 = []
        out1923.append('# 第十九步：比赛C·百家赔率·竞彩官网')
        out1923.append('')
        out1923.append(f"🔗 匹配规则: 本场百家即时盘 vs 历史百家终盘（整数+小数点第一位，胜平负任两项一致即匹配）")
        out1923.append('')
        out1923.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负赔率 | 终盘胜平负赔率 | 盘路变化 | 盘路匹配度 |')
        out1923.append('|------|---------|------|------|---------------|---------------|---------|-----------|')
        
        for i, hist, odds in odds_data:
            res = hist['result']
            if odds and odds['av']:
                d = odds['av']
                out1923.append(f"| {league} | {hist['date']} | {hist['home']}vs{hist['away']} | {res} | {d['iw']}/{d['id']}/{d['il']} | {d['lw']}/{d['ld']}/{d['ll']} | - | - |")
            else:
                out1923.append(f"| {league} | {hist['date']} | {hist['home']}vs{hist['away']} | {res} | - | - | - | - |")
        
        out1923.append('')
        out1923.append('### 盘路匹配度统计')
        out1923.append('')
        
        out1923.append('')
        out1923.append('## 第二十步：比赛C·欧赔·竞彩官网')
        out1923.append('')
        out1923.append('🔗 匹配规则: 本场竞彩即时盘 vs 历史竞彩终盘（整数+小数点第一位，胜平负任两项一致即匹配）')
        out1923.append('')
        out1923.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负赔率 | 终盘胜平负赔率 | 盘路变化 | 盘路匹配度 |')
        out1923.append('|------|---------|------|------|---------------|---------------|---------|-----------|')
        
        for i, hist, odds in odds_data:
            res = hist['result']
            if odds and odds['jc']:
                d = odds['jc']
                out1923.append(f"| {league} | {hist['date']} | {hist['home']}vs{hist['away']} | {res} | {d['iw']}/{d['id']}/{d['il']} | {d['lw']}/{d['ld']}/{d['ll']} | - | - |")
            else:
                out1923.append(f"| {league} | {hist['date']} | {hist['home']}vs{hist['away']} | {res} | - | - | - | - |")
        
        out1923.append('')
        out1923.append('### 盘路匹配度统计')
        out1923.append('')
        
        out1923.append('')
        out1923.append('## 第二十一步：比赛C·欧赔·Interwetten')
        out1923.append('')
        out1923.append('🔗 匹配规则: 本场IW即时盘 vs 历史IW终盘（整数+小数点第一位，胜平负任两项一致即匹配）')
        out1923.append('')
        out1923.append('| 赛事 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负赔率 | 终盘胜平负赔率 | 盘路变化 | 盘路匹配度 |')
        out1923.append('|------|---------|------|------|---------------|---------------|---------|-----------|')
        
        for i, hist, odds in odds_data:
            res = hist['result']
            if odds and odds['iw']:
                d = odds['iw']
                out1923.append(f"| {league} | {hist['date']} | {hist['home']}vs{hist['away']} | {res} | {d['iw']}/{d['id']}/{d['il']} | {d['lw']}/{d['ld']}/{d['ll']} | - | - |")
            else:
                out1923.append(f"| {league} | {hist['date']} | {hist['home']}vs{hist['away']} | {res} | - | - | - | - |")
        
        out1923.append('')
        out1923.append('### 盘路匹配度统计')
        
        # 写文件
        step8_path = os.path.join(m['match_dir'], 'group03_asian', 'step8_same_league.txt')
        os.makedirs(os.path.dirname(step8_path), exist_ok=True)
        with open(step8_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(out))
        print(f"    ✅ step8 written: {step8_path}")
        
        step19_path = os.path.join(m['match_dir'], 'group06_baijia', 'step19_baijia_compare.txt')
        os.makedirs(os.path.dirname(step19_path), exist_ok=True)
        with open(step19_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(out1923))
        print(f"    ✅ step19-23 written: {step19_path}")
        
        time.sleep(0.3)

print(f"\n{'='*50}")
print("全部完成！")
print(f"{'='*50}")
