# -*- coding: utf-8 -*-
"""
轻量补数 V4：只补5月5号 第8步 + 第19-23步
核心改进：不依赖联赛页，直接从meta.json中的home_id/away_id获取球队，
然后从这些球队的赛程中提取同联赛记录，再扩展更多同联赛球队
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

# 硬编码球队ID - 韩职12队
K1_TEAM_IDS = ['1603','1606','1608','1609','1611','1612','1615','3410','4544','5739','6477','7075']

def league_match(src, target):
    if src == target: return True
    if not src or not target: return False
    alias_map = {
        '韩职': ['K1联赛', 'K联赛', '韩K1'], 'K1联赛': ['韩职', 'K联赛', '韩K1'],
        'K联赛': ['韩职', 'K1联赛', '韩K1'], '韩K1': ['韩职', 'K1联赛', 'K联赛'],
        '芬超': ['芬超', '芬兰超级联赛'], '芬兰超级联赛': ['芬超'],
        '沙特': ['沙特职业联赛'], '沙特职业联赛': ['沙特'],
        '欧冠': ['欧冠', '欧洲冠军联赛'], '解放者杯': ['解放者杯', '南美解放者杯'],
        '荷乙': ['荷乙', '荷兰乙级联赛'],
    }
    if target in alias_map and src in alias_map[target]: return True
    if src in alias_map and target in alias_map[src]: return True
    if len(target) >= 2 and target in src: return True
    if len(src) >= 2 and src in target: return True
    return False

def handicap_match(a, b):
    ca = (a or '').replace('升', '').replace('降', '').strip()
    cb = (b or '').replace('升', '').replace('降', '').strip()
    return ca == cb

def dir_str(a, b):
    try:
        fa, fb = float(a), float(b)
        if fb < fa - 0.01: return '\u2b07'
        elif fb > fa + 0.01: return '\u2b06'
    except: pass
    return '\u27a1'

def dir_str3(iw, id_, il, lw, ld, ll):
    return dir_str(iw, lw) + dir_str(id_, ld) + dir_str(il, ll)

def match_level(bench, hist):
    if not bench or not hist or len(bench) != 3 or len(hist) != 3: return '-'
    same = sum(1 for a, b in zip(bench, hist) if a == b)
    if same == 3: return '高'
    elif same >= 2: return '中'
    return '低'

def fetch_odds(fid):
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

def fetch_team_fixtures(team_id):
    url = f'https://liansai.500.com/team/{team_id}/teamfixture/'
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
        'home_id': meta.get('home_id', ''),
        'away_id': meta.get('away_id', ''),
        'dir': d,
        'match_dir': match_dir,
    }
    all_matches.append(match_info)
    if league not in matches_by_league:
        matches_by_league[league] = []
    matches_by_league[league].append(match_info)

print(f"共 {len(all_matches)} 场比赛，{len(matches_by_league)} 个联赛")
for league, ms in matches_by_league.items():
    macaus = [m['macau'] for m in ms]
    print(f"  {league}: {len(ms)}场, 盘口={macaus}")

# 2. 按联赛获取赛程数据
league_matches_cache = {}
for league, league_matches in matches_by_league.items():
    print(f"\n{'='*50}")
    print(f"联赛: {league}")
    
    # 韩职用硬编码12队
    if league == '韩职':
        team_ids = K1_TEAM_IDS
    else:
        # 其他联赛：从meta中的home_id/away_id获取球队
        team_ids = set()
        for m in league_matches:
            if m.get('home_id'): team_ids.add(m['home_id'])
            if m.get('away_id'): team_ids.add(m['away_id'])
        team_ids = list(team_ids)
    
    print(f"  初始球队ID: {team_ids}")
    
    # 逐队获取赛程
    all_data = []
    seen_fids = set()
    for i, tid in enumerate(team_ids, 1):
        fixtures = fetch_team_fixtures(tid)
        for f in fixtures:
            fid = str(f.get('FIXTUREID', ''))
            if fid and fid not in seen_fids:
                seen_fids.add(fid)
                all_data.append(f)
        if i % 4 == 0:
            print(f"  已获取 {i}/{len(team_ids)} 支球队... ({len(all_data)} 条记录)")
        time.sleep(0.2)
    
    print(f"  总记录: {len(all_data)} 条")
    
    # 检查实际SIMPLEGBNAME
    all_names = set()
    for d in all_data:
        all_names.add(d.get('SIMPLEGBNAME', ''))
    print(f"  SIMPLEGBNAME值: {all_names}")
    
    # 对于非韩职联赛，从这些球队的同联赛赛程中提取更多球队
    if league != '韩职':
        # 从已知球队的同联赛赛程中提取所有球队ID
        extra_teams = set()
        for d in all_data:
            if league_match(d.get('SIMPLEGBNAME', ''), league):
                # 提取主队和客队ID（从PAN或BS字段）
                pan = d.get('PAN', '')
                if pan:
                    extra_teams.add(str(pan))
                bs = d.get('BS', '')
                if bs:
                    extra_teams.add(str(bs))
        print(f"  从赛程提取额外球队: {len(extra_teams)} 支")
        
        # 获取额外球队的赛程
        if extra_teams:
            extra_list = list(extra_teams)
            for i, tid in enumerate(extra_list[:30], 1):  # 限制30支
                fixtures = fetch_team_fixtures(tid)
                for f in fixtures:
                    fid = str(f.get('FIXTUREID', ''))
                    if fid and fid not in seen_fids:
                        seen_fids.add(fid)
                        all_data.append(f)
                if i % 5 == 0:
                    print(f"  已获取额外 {i}/{min(len(extra_list),30)} 支球队... ({len(all_data)} 条记录)")
                time.sleep(0.2)
            print(f"  总记录(含额外): {len(all_data)} 条")
    
    # 筛选同联赛
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
            'half': f"{d.get('HOMEHTSCORE','')}:{d.get('AWAYHTSCORE','')}",
            'result': d.get('lpl_on', ''),
            'handicap': hcp,
            'fid': fid,
            'pan': d.get('PAN', ''),
            'bs': d.get('BS', ''),
        })
    
    league_matches_cache[league] = filtered
    print(f"  同联赛(去当前): {len(filtered)} 场")
    
    # 统计盘口分布
    hcp_dist = {}
    for c in filtered:
        h = c['handicap']
        hcp_dist[h] = hcp_dist.get(h, 0) + 1
    for h, c in sorted(hcp_dist.items(), key=lambda x: -x[1])[:10]:
        print(f"    {h}: {c}场")

# 3. 逐场匹配盘口 + 抓赔率 + 生成报告
for league, league_matches in matches_by_league.items():
    print(f"\n{'='*50}")
    print(f"联赛: {league}")
    
    cached = league_matches_cache.get(league, [])
    
    for m in league_matches:
        print(f"\n  [{m['match_num']}] {m['home']}vs{m['away']} 澳门: {m['macau']}")
        
        matched = [c for c in cached if handicap_match(c['handicap'], m['macau'])]
        print(f"    盘口匹配: {len(matched)} 场")
        
        odds_data = []
        for i, hist in enumerate(matched[:15], 1):
            fid = hist.get('fid', '')
            if not fid:
                odds_data.append((i, hist, None))
                continue
            odds = fetch_odds(fid)
            odds_data.append((i, hist, odds))
            time.sleep(0.5)
        
        cur = fetch_odds(m['fid'])
        b_jc = dir_str3(cur['jc']['iw'], cur['jc']['id'], cur['jc']['il'],
                        cur['jc']['lw'], cur['jc']['ld'], cur['jc']['ll']) if cur['jc'] else ''
        b_iw = dir_str3(cur['iw']['iw'], cur['iw']['id'], cur['iw']['il'],
                        cur['iw']['lw'], cur['iw']['ld'], cur['iw']['ll']) if cur['iw'] else ''
        b_av = dir_str3(cur['av']['iw'], cur['av']['id'], cur['av']['il'],
                        cur['av']['lw'], cur['av']['ld'], cur['av']['ll']) if cur['av'] else ''
        
        # 生成 step8
        out8 = []
        out8.append('# 第八步：相同联赛相同亚盘统计')
        out8.append('')
        out8.append(f"📅 数据获取时间: {time.strftime('%Y-%m-%d %H:%M')}")
        out8.append(f"🔗 联赛: {league}")
        out8.append(f"🔗 澳门即时盘: {m['macau']}")
        out8.append('')
        out8.append('### 输出A — 亚盘统计明细')
        out8.append('')
        out8.append('| 序号 | 比赛时间 | 对阵 | 赛果 | 初盘 | 终盘 | 初盘水位 | 终盘水位 | 盘路 | 主场水位差 | 客场水位差 |')
        out8.append('|------|---------|------|------|------|------|---------|---------|------|----------|----------|')
        
        for i, hist, odds in odds_data:
            out8.append(f"| {i} | {hist['date']} | {hist['home']}vs{hist['away']} | {hist['score']} | {hist['handicap']} | {hist['handicap']} | - | - | {hist['result']} | - | - |")
        
        out8.append('')
        out8.append('### 输出B — 欧赔明细（竞彩官方）')
        out8.append('')
        out8.append('| 序号 | 公司 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负 | 终盘胜平负 | 盘路变化 | 盘路匹配度 |')
        out8.append('|------|------|---------|------|------|-----------|-----------|---------|-----------|')
        
        jc_stats = {'高': {'胜':0,'平':0,'负':0}, '中': {'胜':0,'平':0,'负':0}, '低': {'胜':0,'平':0,'负':0}}
        iw_stats = {'高': {'胜':0,'平':0,'负':0}, '中': {'胜':0,'平':0,'负':0}, '低': {'胜':0,'平':0,'负':0}}
        av_stats = {'高': {'胜':0,'平':0,'负':0}, '中': {'胜':0,'平':0,'负':0}, '低': {'胜':0,'平':0,'负':0}}
        
        for i, hist, odds in odds_data:
            res = hist['result']
            if odds and odds['jc']:
                d = odds['jc']
                hd = dir_str3(d['iw'], d['id'], d['il'], d['lw'], d['ld'], d['ll'])
                ml = match_level(b_jc, hd) if b_jc else '-'
                out8.append(f"| {i} | 竞彩官方 | {hist['date']} | {hist['home']}vs{hist['away']} | {res} | {d['iw']}/{d['id']}/{d['il']} | {d['lw']}/{d['ld']}/{d['ll']} | {hd} | {ml} |")
                if ml in jc_stats: jc_stats[ml][res] += 1
            else:
                out8.append(f"| {i} | - | {hist['date']} | {hist['home']}vs{hist['away']} | {res} | - | - | - | - |")
            
            if odds and odds['iw']:
                d = odds['iw']
                hd = dir_str3(d['iw'], d['id'], d['il'], d['lw'], d['ld'], d['ll'])
                ml = match_level(b_iw, hd) if b_iw else '-'
                if ml in iw_stats: iw_stats[ml][res] += 1
            
            if odds and odds['av']:
                d = odds['av']
                hd = dir_str3(d['iw'], d['id'], d['il'], d['lw'], d['ld'], d['ll'])
                ml = match_level(b_av, hd) if b_av else '-'
                if ml in av_stats: av_stats[ml][res] += 1
        
        out8.append('')
        out8.append('### 盘路匹配度统计')
        out8.append('')
        for label, stats in [('竞彩', jc_stats), ('Interwetten', iw_stats), ('百家平均', av_stats)]:
            out8.append(f'**{label}**')
            for lv in ['高', '中', '低']:
                x = stats.get(lv, {})
                t = sum(x.values())
                if t > 0:
                    out8.append(f"  {lv}盘路: 胜{x.get('胜',0)} 平{x.get('平',0)} 负{x.get('负',0)} (共{t}场)")
            if not any(sum(v.values()) > 0 for v in stats.values()):
                out8.append('  无数据')
            out8.append('')
        
        # 生成 step19-23
        out1923 = []
        out1923.append('# 第十九步：比赛C·百家赔率·竞彩官网')
        out1923.append('')
        out1923.append('🔗 匹配规则: 本场百家即时盘 vs 历史百家终盘（整数+小数点第一位，胜平负任两项一致即匹配）')
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
        
        step8_path = os.path.join(m['match_dir'], 'group03_asian', 'step8_same_league.txt')
        os.makedirs(os.path.dirname(step8_path), exist_ok=True)
        with open(step8_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(out8))
        
        step19_path = os.path.join(m['match_dir'], 'group06_baijia', 'step19_baijia_compare.txt')
        os.makedirs(os.path.dirname(step19_path), exist_ok=True)
        with open(step19_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(out1923))
        
        print(f"    ✅ step8 + step19-23 written")
        time.sleep(0.3)

print(f"\n{'='*50}")
print("全部完成！")
print(f"{'='*50}")
