# -*- coding: utf-8 -*-
"""Step 24: 盘路完全匹配汇总
用法1: python step24_extractor.py <home_id> <away_id> <league> <fid> <output_path>
用法2: python step24_extractor.py <match_dir>  (自动从 meta.json 读取参数)
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
        HOME_ID = meta.get('home_id', '2465')
        AWAY_ID = meta.get('away_id', '848')
        LEAGUE = meta.get('league', '瑞典超')
        FID = meta.get('fid', '1362643')
    else:
        HOME_ID = '2465'
        AWAY_ID = '848'
        LEAGUE = '瑞典超'
        FID = '1362643'
    OUTPUT_PATH = os.path.join(MATCH_DIR, 'step24_panlu_match.json')
else:
    HOME_ID = sys.argv[1] if len(sys.argv) > 1 else '2465'
    AWAY_ID = sys.argv[2] if len(sys.argv) > 2 else '848'
    LEAGUE = sys.argv[3] if len(sys.argv) > 3 else '瑞典超'
    FID = sys.argv[4] if len(sys.argv) > 4 else '1362643'
    OUTPUT_PATH = sys.argv[5] if len(sys.argv) > 5 else 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-04-27/step24_002.txt'


from _log_util import setup_logger
LOG_DIR = None
if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    LOG_DIR = os.path.join(os.path.dirname(os.path.normpath(sys.argv[1])), 'logs')
log = setup_logger('step24', LOG_DIR)
import requests, re, json, time
from bs4 import BeautifulSoup
from datetime import datetime

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

now = datetime.now().strftime('%Y-%m-%d %H:%M')

def gd(a, b):
    """获取盘路变化方向"""
    try:
        fa, fb = float(a), float(b)
        if fb < fa - 0.01: return '\u2b07'  # ↓
        elif fb > fa + 0.01: return '\u2b06'  # ↑
    except: pass
    return '\u27a1'  # →

def dir_str3(iw, id_, il, lw, ld, ll):
    return gd(iw, lw) + gd(id_, ld) + gd(il, ll)

def clean_text(s):
    return s.replace('\xa0', '').replace('\u2193', '').replace('\u2191', '').replace('\u2192', '').strip()

def handicap_match(src_hcp, target_hcp):
    if not src_hcp or not target_hcp:
        return False
    return src_hcp.strip() == target_hcp.strip()

def gd_for_match(bench, hist):
    '''2/3精度匹配'''
    try:
        match_count = 0
        for idx in [0, 1, 2]:
            bv = float(bench[idx])
            hv = float(hist[idx])
            b_int = int(bv)
            b_dec = int((bv - b_int) * 10)
            h_int = int(hv)
            h_dec = int((hv - h_int) * 10)
            if b_int == h_int and b_dec == h_dec:
                match_count += 1
        return match_count >= 2
    except:
        return False

def match_level(bench, hist):
    if len(bench) != 3 or len(hist) != 3: return '-'
    same = sum(1 for a, b in zip(bench, hist) if a == b)
    if same == 3: return '高'
    elif same >= 2: return '中'
    return '低'

def asian_water_change(live_wh, init_wh):
    '''计算水位变化差'''
    try:
        l = float(live_wh)
        i = float(init_wh)
        return '{:+.3f}'.format(l - i)
    except:
        return '-'

def gen_step8_output(now, league, macau_line, match_data):
    '''从step24已爬数据生成step8格式：同联赛亚盘统计'''
    out = []
    out.append('# 第八步：同联赛相同盘口统计')
    out.append('')
    out.append('📅 数据获取时间: ' + now)
    out.append('📋 联赛: ' + league)
    out.append('🎯 澳门即时盘: ' + macau_line)
    out.append('')
    
    # 筛选有asian数据且盘口匹配的比赛（最多15场）
    hcp_matches = []
    for m in match_data:
        a = m.get('asian')
        if not a or not a.get('live_pan'):
            continue
        if macau_line and not handicap_match(macau_line.replace('球','').replace('速','').strip(), a['live_pan'].replace('球','').replace('速','').strip()):
            continue
        hcp_matches.append(m)
        if len(hcp_matches) >= 15:
            break
    
    out.append('### 表A — 盘口统计明细')
    out.append('')
    out.append('| 序号 | 比赛时间 | 主队 | 比分 | 初盘 | 即时盘 | 主队水 | 客队水 | 盘路 | 主水变化 | 客水变化 |')
    out.append('|------|---------|------|------|------|------|---------|---------|------|----------|----------|')
    for i, m in enumerate(hcp_matches, 1):
        a = m.get('asian', {})
        if not a:
            continue
        live_pan = a.get('live_pan', '-')
        init_pan = a.get('init_pan', '-')
        wh_change = asian_water_change(a.get('live_wh', '0'), a.get('init_wh', '0'))
        wa_change = asian_water_change(a.get('live_wa', '0'), a.get('init_wa', '0'))
        out.append('| {} | {} | {} vs {} | {} | {} | {} | {}/{} | {}/{} | ？ | {} | {} |'.format(
            i, m['date'], m['home'], m['away'], m['score'],
            init_pan, live_pan,
            a.get('init_wh', '-'), a.get('init_wa', '-'),
            a.get('live_wh', '-'), a.get('live_wa', '-'),
            wh_change, wa_change))
    if not hcp_matches:
        out.append('| - | - | - | - | - | - | - | - | - | - |')
    out.append('')
    
    # 统计
    out.append('### 盘口统计汇总')
    total = len(hcp_matches)
    out.append('- 总场次: {}场'.format(total) if total > 0 else '- 总场次: 0场')
    
    # 表B：欧赔细节（同赔匹配分析）
    out.append('')
    out.append('### 表B — 欧赔细节（官方）')
    out.append('')
    out.append('| 序号 | 公司 | 比赛日期 | 对阵 | 赛果 | 初盘胜平负 | 即时胜平负 | 盘路变化 | 盘路匹配度 |')
    out.append('|------|------|---------|------|------|-----------|-----------|---------|-----------|')
    for i, m in enumerate(hcp_matches[:10], 1):
        jc = m.get('jc')
        if not jc:
            continue
        jc_init = '{:.2f}/{:.2f}/{:.2f}'.format(jc[0], jc[1], jc[2])
        jc_live = '{:.2f}/{:.2f}/{:.2f}'.format(jc[3], jc[4], jc[5])
        direction = dir_str3(*jc)
        out.append('| {} | 官方 | {} | {} vs {} | {} | {} | {} | {} | - |'.format(
            i, m['date'], m['home'], m['away'], m['result'],
            jc_init, jc_live, direction))
    if not hcp_matches:
        out.append('| - | - | - | - | - | - | - | - | - |')
    
    return out

def gen_step19_output(now, league, match_data, cur_jc, cur_iw, cur_av,
                       bench_jc_dir, bench_iw_dir, bench_av_dir):
    '''从step24已爬数据生成step19-23格式：百家对比'''
    out = []
    
    # Step 19: 竞彩同赔分析
    out.append('')
    out.append('📅 数据获取时间: ' + now)
    out.append('📋 联赛: ' + league)
    out.append('🎯 匹配规则: 比赛即时赔率 vs 历史竞彩赔率（整数+小数点后一位胜平负任二匹配）')
    out.append('')
    
    out.append('## 第十九步：竞彩欧赔同赔分析')
    out.append('')
    out.append('| 联赛 | 比赛日期 | 对阵 | 赛果 | 竞彩即时赔率 | 竞彩初始赔率 | 盘路变化 | 盘路匹配度 |')
    out.append('|------|---------|------|------|---------------|---------------|---------|-----------|')
    
    jc_matches = []
    for m in match_data:
        jc = m.get('jc')
        if not jc or not cur_jc:
            continue
        if gd_for_match(cur_jc, jc):
            direction = dir_str3(*jc)
            level = match_level(bench_jc_dir, list(direction))
            jc_live = '{:.2f}/{:.2f}/{:.2f}'.format(jc[3], jc[4], jc[5])
            jc_init = '{:.2f}/{:.2f}/{:.2f}'.format(jc[0], jc[1], jc[2])
            out.append('| {} | {} | {} vs {} | {} | {} | {} | {} | {} |'.format(
                league, m['date'], m['home'], m['away'], m['result'],
                jc_live, jc_init, direction, level))
            jc_matches.append(m)
    if not jc_matches:
        out.append('| - | - | - | - | - | - | - | - |')
    
    # 统计
    out.append('')
    out.append('### 盘路匹配统计')
    stats = {}
    for m in match_data:
        jc = m.get('jc')
        if not jc or not cur_jc or not gd_for_match(cur_jc, jc):
            continue
        direction = dir_str3(*jc)
        if direction not in stats:
            stats[direction] = {'胜': 0, '平': 0, '负': 0}
        result_map = {'3': '胜', '1': '平', '0': '负', '-': '-'}
        res = result_map.get(m['result'], '-')
        if res in stats[direction]:
            stats[direction][res] += 1
    for d, s in stats.items():
        total_s = sum(s.values())
        out.append('{}盘路: 胜{} 平{} 负{} (共{}场)'.format(d, s.get('胜',0), s.get('平',0), s.get('负',0), total_s))
    out.append('')
    
    # Step 20: 欧赔官方同赔（用官方/竞彩数据）
    out.append('## 第二十步：欧赔官方同赔分析')
    out.append('')
    out.append('🎯 匹配规则: 比赛即时赔率 vs 历史官方赔率（整数+小数点后一位胜平负任二匹配）')
    out.append('')
    out.append('| 联赛 | 比赛日期 | 对阵 | 赛果 | 即时赔率 | 初始赔率 | 盘路变化 | 盘路匹配度 |')
    out.append('|------|---------|------|------|---------------|---------------|---------|-----------|')
    for m in jc_matches[:15]:
        jc = m.get('jc')
        if not jc:
            continue
        direction = dir_str3(*jc)
        level = match_level(bench_jc_dir, list(direction))
        jc_live = '{:.2f}/{:.2f}/{:.2f}'.format(jc[3], jc[4], jc[5])
        jc_init = '{:.2f}/{:.2f}/{:.2f}'.format(jc[0], jc[1], jc[2])
        out.append('| {} | {} | {} vs {} | {} | {} | {} | {} | {} |'.format(
            league, m['date'], m['home'], m['away'], m['result'],
            jc_live, jc_init, direction, level))
    if not jc_matches:
        out.append('| - | - | - | - | - | - | - | - |')
    out.append('')
    
    # Step 21: Interwetten同赔
    out.append('## 第二十一步：Interwetten同赔分析')
    out.append('')
    out.append('🎯 匹配规则: 比赛IW即时赔率 vs 历史IW赔率（整数+小数点后一位胜平负任二匹配）')
    out.append('')
    out.append('| 联赛 | 比赛日期 | 对阵 | 赛果 | IW即时赔率 | IW初始赔率 | 盘路变化 | 盘路匹配度 |')
    out.append('|------|---------|------|------|---------------|---------------|---------|-----------|')
    iw_matches = []
    for m in match_data:
        iw = m.get('iw')
        if not iw or not cur_iw:
            continue
        if gd_for_match(cur_iw, iw):
            direction = dir_str3(*iw)
            iw_live = '{:.2f}/{:.2f}/{:.2f}'.format(iw[3], iw[4], iw[5])
            iw_init = '{:.2f}/{:.2f}/{:.2f}'.format(iw[0], iw[1], iw[2])
            level = match_level(bench_iw_dir, list(direction))
            out.append('| {} | {} | {} vs {} | {} | {} | {} | {} | {} |'.format(
                league, m['date'], m['home'], m['away'], m['result'],
                iw_live, iw_init, direction, level))
            iw_matches.append(m)
    if not iw_matches:
        out.append('| - | - | - | - | - | - | - | - |')
    out.append('')
    
    # Step 22: 百家平均同赔
    out.append('## 第二十二步：百家平均同赔分析')
    out.append('')
    out.append('🎯 匹配规则: 比赛百家即时赔率 vs 历史百家赔率（整数+小数点后一位胜平负任二匹配）')
    out.append('')
    out.append('| 联赛 | 比赛日期 | 对阵 | 赛果 | 百家即时赔率 | 百家初始赔率 | 盘路变化 | 盘路匹配度 |')
    out.append('|------|---------|------|------|---------------|---------------|---------|-----------|')
    av_matches = []
    for m in match_data:
        av = m.get('av')
        if not av or not cur_av:
            continue
        if gd_for_match(cur_av, av):
            direction = dir_str3(*av)
            av_live = '{:.2f}/{:.2f}/{:.2f}'.format(av[3], av[4], av[5])
            av_init = '{:.2f}/{:.2f}/{:.2f}'.format(av[0], av[1], av[2])
            level = match_level(bench_av_dir, list(direction))
            out.append('| {} | {} | {} vs {} | {} | {} | {} | {} | {} |'.format(
                league, m['date'], m['home'], m['away'], m['result'],
                av_live, av_init, direction, level))
            av_matches.append(m)
    if not av_matches:
        out.append('| - | - | - | - | - | - | - | - |')
    out.append('')
    
    # Step 23: 综合分析汇总
    out.append('## 第二十三步：综合分析汇总')
    out.append('')
    out.append('🎯 至少有一个公司盘路匹配的历史比赛')
    out.append('')
    out.append('| 比赛日期 | 对阵 | 赛果 | 竞彩欧赔 | IW | 百家平均 | 匹配数 |')
    out.append('|---------|------|------|---------|-----|---------|--------|')
    for m in match_data:
        jc_d = dir_str3(*m['jc']) if m.get('jc') else ''
        iw_d = dir_str3(*m['iw']) if m.get('iw') else ''
        av_d = dir_str3(*m['av']) if m.get('av') else ''
        
        matches = []
        if jc_d and bench_jc_dir and jc_d == bench_jc_dir: matches.append('竞彩')
        if iw_d and bench_iw_dir and iw_d == bench_iw_dir: matches.append('IW')
        if av_d and bench_av_dir and av_d == bench_av_dir: matches.append('百家')
        
        if len(matches) > 0:
            out.append('| {} | {} vs {} | {} | {} | {} | {} | {} |'.format(
                m['date'], m['home'], m['away'], m['result'],
                jc_d or '-', iw_d or '-', av_d or '-', len(matches)))
    if not match_data:
        out.append('| - | - | - | - | - | - | - | - |')
    
    return out

# ============ 获取当前比赛基准盘路 ============
log.info('获取当前比赛基准盘路...')
cur_jc = cur_iw = cur_av = cur_rq = None
try:
    r = sess.get('https://odds.500.com/fenxi/ouzhi-{}.shtml'.format(FID), timeout=10)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, 'html.parser')
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
            if td0 == '1':
                cur_jc = nums
            elif td0 == '6':
                cur_iw = nums
            elif '\u767e' in td1 or '\u5e73' in td1:
                cur_av = nums
    if cur_jc: print('  竞彩欧赔盘路: {}'.format(dir_str3(*cur_jc)))
    if cur_iw: print('  IWC盘路: {}'.format(dir_str3(*cur_iw)))
    if cur_av: print('  百家盘路: {}'.format(dir_str3(*cur_av)))
except Exception as e:
    log.info('  欧赔错误: {}'.format(e))

# 获取让球盘路
try:
    r = sess.get('https://odds.500.com/fenxi/rangqiu-{}.shtml'.format(FID), timeout=10)
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
                cur_rq = nums
                break
        if cur_rq: break
    if cur_rq: print('  让球盘路: {}'.format(dir_str3(*cur_rq)))
except: pass

# 本场盘路基准
bench_jc_dir = dir_str3(*cur_jc) if cur_jc else ''
bench_iw_dir = dir_str3(*cur_iw) if cur_iw else ''
bench_av_dir = dir_str3(*cur_av) if cur_av else ''
bench_rq_dir = dir_str3(*cur_rq) if cur_rq else ''

# ============ 获取整个联赛所有比赛 ============
log.info()
log.info('获取整个联赛比赛...')

# 获取联赛名称和球队列表
league_name = None
team_ids = set()
try:
    r = sess.get('https://liansai.500.com/team/{}/teamfixture/'.format(HOME_ID), timeout=15)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, 'html.parser')
    for tr in soup.find_all('tr', attrs={'data': True}):
        try:
            d = json.loads(tr.get('data', '{}'))
            gbname = d.get('SIMPLEGBNAME', '')
            if not league_name and gbname:
                league_name = gbname
                log.info('  联赛名称: {}'.format(league_name))
            # Get ALL team IDs from first page (not filtered by league)
            team_ids.add(str(d.get('HOMETEAMID', '')))
            team_ids.add(str(d.get('AWAYTEAMID', '')))
        except: pass
except: pass
team_ids.discard('')
team_ids = sorted(list(team_ids))
log.info('  联赛球队: {} 支'.format(len(team_ids)))

# 获取所有比赛 - use team_ids filtering (not league name comparison)
all_matches = []
seen_fid = set()

for i, team_id in enumerate(team_ids, 1):
    if i % 4 == 0: print('  已获取 {}/{} 支球队...'.format(i, len(team_ids)))
    try:
        r = sess.get('https://liansai.500.com/team/{}/teamfixture/'.format(team_id), timeout=15)
        r.encoding = 'gbk'
        soup = BeautifulSoup(r.text, 'html.parser')
        for tr in soup.find_all('tr', attrs={'data': True}):
            try:
                d = json.loads(tr.get('data', '{}'))
                # Use team_ids filtering (both teams must be in league team set)
                htid = str(d.get('HOMETEAMID', ''))
                atid = str(d.get('AWAYTEAMID', ''))
                if htid not in team_ids or atid not in team_ids: continue
                fid = str(d.get('FIXTUREID', ''))
                if fid in seen_fid: continue
                seen_fid.add(fid)
                all_matches.append({
                    'fid': fid,
                    'date': d.get('MATCHDATE', ''),
                    'home': d.get('HOMETEAMSXNAME', ''),
                    'away': d.get('AWAYTEAMSXNAME', ''),
                    'score': '{}:{}'.format(d.get('HOMESCORE', 0), d.get('AWAYSCORE', 0)),
                    'result': d.get('lpl_on', '-'),
                })
            except: pass
    except: pass
    time.sleep(0.2)

log.info('  同联赛: {} 场 (去重后)'.format(len(all_matches)))

# ============ 获取每场比赛的欧赔+让球数据 ============
log.info()
log.info('获取欧赔+让球数据...')

match_data = []
for i, m in enumerate(all_matches, 1):
    fid = m.get('fid', '')
    if not fid: continue
    try:
        # 获取欧赔
        r = sess.get('https://odds.500.com/fenxi/ouzhi-{}.shtml'.format(fid), timeout=10)
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
                    val = clean_text(tds[idx].get_text())
                    try: nums.append(float(val))
                    except: pass
                if len(nums) < 6: continue
                if td0 == '1': jc = nums
                elif td0 == '6': iw = nums
                elif '\u767e' in td1 or '\u5e73' in td1: av = nums
        
        # 获取让球
        rq = None
        try:
            r2 = sess.get('https://odds.500.com/fenxi/rangqiu-{}.shtml'.format(fid), timeout=10)
            r2.encoding = 'gbk'
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            for table in soup2.find_all('table'):
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
                        rq = nums
                        break
                if rq: break
        except: pass
        
        # 获取亚盘（yazhi）- 用于step8输出
        asian_data = None
        try:
            r3 = sess.get('https://odds.500.com/fenxi/yazhi-{}.shtml'.format(fid), timeout=10)
            r3.encoding = 'gbk'
            soup3 = BeautifulSoup(r3.text, 'html.parser')
            for table in soup3.find_all('table'):
                for tr in table.find_all('tr'):
                    tds = tr.find_all('td')
                    if len(tds) < 12: continue
                    name = tds[1].get_text().strip()
                    if '澳' not in name and '澳' not in name: continue
                    asian_data = {
                        'live_pan': clean_text(tds[4].get_text()),
                        'live_wh': clean_text(tds[3].get_text()),
                        'live_wa': clean_text(tds[5].get_text()),
                        'init_pan': clean_text(tds[10].get_text()),
                        'init_wh': clean_text(tds[9].get_text()),
                        'init_wa': clean_text(tds[11].get_text()),
                    }
                    break
                if asian_data: break
        except: pass

        match_data.append({
            **m,
            'jc': jc,
            'iw': iw,
            'av': av,
            'rq': rq,
            'asian': asian_data,
        })
        if i % 20 == 0: print('  已获取 {}/{} 场...'.format(i, len(all_matches)))
    except: pass
    time.sleep(0.2)

log.info('  有效数据: {} 场'.format(len(match_data)))

# ============ 盘路完全匹配分析 ============
log.info()
log.info('盘路完全匹配分析...')
log.info('  竞彩欧赔基准: {}'.format(bench_jc_dir))
log.info('  IWC基准: {}'.format(bench_iw_dir))
log.info('  百家基准: {}'.format(bench_av_dir))
log.info('  让球基准: {}'.format(bench_rq_dir))

# 统计
jc_match = []
iw_match = []
av_match = []
rq_match = []
all_match = []

for m in match_data:
    jc = m.get('jc')
    iw = m.get('iw')
    av = m.get('av')
    rq = m.get('rq')
    
    jc_d = dir_str3(*jc) if jc else ''
    iw_d = dir_str3(*iw) if iw else ''
    av_d = dir_str3(*av) if av else ''
    rq_d = dir_str3(*rq) if rq else ''
    
    matched_companies = []
    if jc_d and jc_d == bench_jc_dir: matched_companies.append('竞彩欧赔')
    if iw_d and iw_d == bench_iw_dir: matched_companies.append('Interwetten')
    if av_d and av_d == bench_av_dir: matched_companies.append('百家平均')
    if rq_d and rq_d == bench_rq_dir: matched_companies.append('让球指数')
    
    if '竞彩欧赔' in matched_companies: jc_match.append({**m, 'dir': jc_d})
    if 'Interwetten' in matched_companies: iw_match.append({**m, 'dir': iw_d})
    if '百家平均' in matched_companies: av_match.append({**m, 'dir': av_d})
    if '让球指数' in matched_companies: rq_match.append({**m, 'dir': rq_d})
    if matched_companies:
        all_match.append({**m, 'companies': matched_companies})

# 获取macau_line（从meta.json）
MACAU_LINE = ''
if 'MATCH_DIR' in dir() and os.path.isfile(os.path.join(MATCH_DIR, 'meta.json')):
    try:
        with open(os.path.join(MATCH_DIR, 'meta.json'), encoding='utf-8') as f:
            m_meta = json.load(f)
        MACAU_LINE = m_meta.get('macau_line', '')
    except:
        pass

log.info('  竞彩欧赔匹配: {} 场'.format(len(jc_match)))
log.info('  IWC匹配: {} 场'.format(len(iw_match)))
log.info('  百家匹配: {} 场'.format(len(av_match)))
log.info('  让球匹配: {} 场'.format(len(rq_match)))
log.info('  至少1项匹配: {} 场'.format(len(all_match)))

# ============ 输出 ============
out = []
out.append('# 第二十四步：盘路完全匹配汇总')
out.append('')
out.append('\U0001f4c5 数据获取时间: ' + now)
out.append('')
out.append('## 本场盘路基准')
out.append('')
out.append('| 公司 | 盘路变化 |')
out.append('|------|---------|')
out.append('| 竞彩欧赔 | {} |'.format(bench_jc_dir))
out.append('| Interwetten | {} |'.format(bench_iw_dir))
out.append('| 百家平均 | {} |'.format(bench_av_dir))
out.append('| 让球指数 | {} |'.format(bench_rq_dir))
out.append('')

# 竞彩欧赔匹配
out.append('## 竞彩欧赔完全匹配 ({} 场)'.format(len(jc_match)))
out.append('')
out.append('| 比赛日期 | 对阵 | 赛果 | 盘路变化 |')
out.append('|---------|------|------|---------|')
for m in jc_match:
    out.append('| {} | {} vs {} | {} | {} |'.format(m['date'], m['home'], m['away'], m['result'], m['dir']))
if not jc_match:
    out.append('| - | - | - | - |')
out.append('')

# IWC匹配
out.append('## Interwetten完全匹配 ({} 场)'.format(len(iw_match)))
out.append('')
out.append('| 比赛日期 | 对阵 | 赛果 | 盘路变化 |')
out.append('|---------|------|------|---------|')
for m in iw_match:
    out.append('| {} | {} vs {} | {} | {} |'.format(m['date'], m['home'], m['away'], m['result'], m['dir']))
if not iw_match:
    out.append('| - | - | - | - |')
out.append('')

# 百家匹配
out.append('## 百家平均完全匹配 ({} 场)'.format(len(av_match)))
out.append('')
out.append('| 比赛日期 | 对阵 | 赛果 | 盘路变化 |')
out.append('|---------|------|------|---------|')
for m in av_match:
    out.append('| {} | {} vs {} | {} | {} |'.format(m['date'], m['home'], m['away'], m['result'], m['dir']))
if not av_match:
    out.append('| - | - | - | - |')
out.append('')

# 让球匹配
out.append('## 让球指数完全匹配 ({} 场)'.format(len(rq_match)))
out.append('')
out.append('| 比赛日期 | 对阵 | 赛果 | 盘路变化 |')
out.append('|---------|------|------|---------|')
for m in rq_match:
    out.append('| {} | {} vs {} | {} | {} |'.format(m['date'], m['home'], m['away'], m['result'], m['dir']))
if not rq_match:
    out.append('| - | - | - | - |')
out.append('')

# 至少1项匹配汇总
out.append('## 任意公司盘路匹配汇总 ({} 场)'.format(len(all_match)))
out.append('')
out.append('| 比赛日期 | 对阵 | 赛果 | 匹配的公司 |')
out.append('|---------|------|------|-----------|')
for m in all_match:
    out.append('| {} | {} vs {} | {} | {} |'.format(m['date'], m['home'], m['away'], m['result'], ', '.join(m['companies'])))
if not all_match:
    out.append('| - | - | - | - |')
out.append('')

# ============ Write ============
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

# ============ 合并输出：step8格式（同联赛亚盘统计）============
# 用match_data中已有的asian数据生成step8
step8_lines = gen_step8_output(now, LEAGUE, MACAU_LINE, match_data)
if 'MATCH_DIR' in dir():
    G3 = os.path.join(MATCH_DIR, 'group03_asian')
    os.makedirs(G3, exist_ok=True)
    STEP8_OUT = os.path.join(G3, 'step8_same_league.txt')
    with open(STEP8_OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(step8_lines))

# ============ 合并输出：step19-23格式（百家对比）============
step19_lines = gen_step19_output(now, LEAGUE, match_data, cur_jc, cur_iw, cur_av,
                                  bench_jc_dir, bench_iw_dir, bench_av_dir)
if 'MATCH_DIR' in dir():
    G6 = os.path.join(MATCH_DIR, 'group06_baijia')
    os.makedirs(G6, exist_ok=True)
    STEP19_OUT = os.path.join(G6, 'step19_baijia_compare.txt')
    with open(STEP19_OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(step19_lines))

# ============ 缓存所有FID的赔率数据（供step9-18使用）============
fid_cache = {}
for md in match_data:
    fid = md.get('fid', '')
    if not fid: continue
    entry = {}
    for key in ['jc', 'iw', 'av', 'rq']:
        val = md.get(key)
        if val:
            entry[key] = list(val)
    asian = md.get('asian')
    if asian:
        entry['asian'] = asian
    if entry:
        fid_cache[fid] = entry

if 'MATCH_DIR' in dir():
    CACHE_PATH = os.path.join(MATCH_DIR, 'fid_odds_cache.json')
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(fid_cache, f, ensure_ascii=False, indent=2)

log.info()
log.info('='*60)
log.info('完成！')
log.info('输出: ' + OUTPUT_PATH)
if 'STEP8_OUT' in dir():
    log.info('同步输出(Step8): ' + STEP8_OUT)
    log.info('同步输出(Step19-23): ' + STEP19_OUT)
if 'CACHE_PATH' in dir():
    log.info('赔率缓存(FID Cache): ' + CACHE_PATH)
