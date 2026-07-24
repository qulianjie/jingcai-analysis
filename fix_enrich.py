#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复核心联赛缓存的百家欧赔、让球指数和亚盘"""

import json, os, sys, traceback, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import requests
from bs4 import BeautifulSoup

SD = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SD, 'data', 'league_cache')
FIX_LOG = os.path.join(SD, 'fix_enrich.log')

def log(msg):
    print(msg, flush=True)
    try:
        with open(FIX_LOG, 'a', encoding='utf-8') as lf:
            lf.write(msg + '\n')
    except:
        pass

CORE_LEAGUES = [
    'K1联赛.json',
    '英超Premier League.json', '英超夏季赛.json',
    '西甲La Liga.json', '德甲Bundesliga.json', '意甲Serie A.json',
    '法甲.json',
    '欧冠Champions League.json',
    '欧罗巴UEFA Europa League.json', '欧协联.json',
    '巴甲.json', '日职.json', '日联杯.json',
    '澳超.json', '瑞超.json', '挪超.json',
    '俄超.json',
    '亚冠.json', '解放者杯.json',
    '芬兰超级联赛.json',
    '美职联.json',
]

sess = requests.Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def _odds_direction(init, live):
    d = ''
    for a, b in zip(init, live):
        if b > a + 0.01: d += '⬆'
        elif b < a - 0.01: d += '⬇'
        else: d += '➡'
    return d

def _parse_odds_row(tds):
    """从td列表解析赔率行"""
    nums = []
    for idx in [3, 4, 5, 6, 7, 8]:
        val = tds[idx].get_text().strip().replace(chr(160), '')
        try: nums.append(float(val))
        except: break
    if len(nums) >= 6:
        return {
            'iw': nums[0], 'id': nums[1], 'il': nums[2],
            'lw': nums[3], 'ld': nums[4], 'll': nums[5],
            'dir': _odds_direction(nums[:3], nums[3:6])
        }
    return None

def fix_match(fid):
    """重新抓取并修复单场比赛（含百家欧赔 + 各公司 + IW让球 + 亚盘）"""
    result = {}
    # 1. 欧赔页：百家欧赔 + 各公司赔率
    try:
        url = f'https://odds.500.com/fenxi/ouzhi-{fid}.shtml'
        resp = sess.get(url, timeout=10)
        resp.encoding = 'gbk'
        soup = BeautifulSoup(resp.text, 'html.parser')
        companies = []
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                td1 = tds[1].get_text().strip()
                parsed = _parse_odds_row(tds)
                if parsed is None: continue
                if '平均' in td1 or '百家' in td1:
                    result['av'] = parsed
                else:
                    companies.append({'name': td1, **parsed})
        if companies:
            result['companies'] = companies
    except:
        pass
    # 2. 让球页：IW让球 + 竞彩让球
    try:
        url_rq = f'https://odds.500.com/fenxi/rangqiu-{fid}.shtml'
        resp2 = sess.get(url_rq, timeout=10)
        resp2.encoding = 'gbk'
        soup2 = BeautifulSoup(resp2.text, 'html.parser')
        iw_hc = None
        jc_hc = None
        for table in soup2.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                td0 = tds[0].get_text().strip()
                td1 = tds[1].get_text().strip()
                td2 = tds[2].get_text().strip().replace(chr(160), '')
                # 竞彩让球：公司名含"官"或"中国"
                if '官' in td1 or '中国' in td1:
                    nums = []
                    for idx in [4, 5, 6, 7, 8, 9]:
                        val = tds[idx].get_text().strip().replace(chr(160), '')
                        try: nums.append(float(val))
                        except: break
                    if len(nums) >= 6:
                        jc_hc = {
                            'handicap': td2,
                            'iw': nums[0], 'id': nums[1], 'il': nums[2],
                            'lw': nums[3], 'ld': nums[4], 'll': nums[5],
                            'dir': _odds_direction(nums[:3], nums[3:6])
                        }
                        continue  # 继续找IW
                # IW让球：td0=='6'
                if td0 != '6': continue
                td2_rq = tds[2].get_text().strip().replace(chr(160), '')
                nums = []
                for idx in [4, 5, 6, 7, 8, 9]:
                    val = tds[idx].get_text().strip().replace(chr(160), '')
                    try: nums.append(float(val))
                    except: break
                if len(nums) >= 6:
                    iw_hc = {
                        'handicap': td2_rq,
                        'iw': nums[0], 'id': nums[1], 'il': nums[2],
                        'lw': nums[3], 'ld': nums[4], 'll': nums[5],
                        'dir': _odds_direction(nums[:3], nums[3:6])
                    }
        if jc_hc:
            result['jc_hc'] = jc_hc
        if iw_hc:
            result['iw_hc'] = iw_hc
    except:
        pass
    # 3. 亚盘页：澳门亚盘（前3家公司盘口）
    try:
        url_yz = f'https://odds.500.com/fenxi/yazhi-{fid}.shtml'
        resp3 = sess.get(url_yz, timeout=10)
        resp3.encoding = 'gbk'
        soup3 = BeautifulSoup(resp3.text, 'html.parser')
        yz_list = []
        for table in soup3.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                td0 = tds[0].get_text().strip()
                if td0.isdigit() and int(td0) in (1, 2, 3):
                    name = tds[1].get_text().strip()
                    # 动态找盘口列：通过关键字识别"半球""一球""平手"等，第一个是即时盘，第二个是初始盘
                    def _cln(t): return t.replace(chr(160), '').replace('↑','').replace('↓','').replace('升','').replace('降','').replace(' ','').strip()
                    live_pan = init_pan = None
                    li = ii = -1
                    for i in range(2, len(tds)):
                        txt = _cln(tds[i].get_text())
                        if not txt or re.match(r'^[\d.]+', txt): continue
                        if any(k in txt for k in ('半球','一球','平手','球半','两球','三球','平半','半一')):
                            if live_pan is None:
                                live_pan = txt; li = i
                            elif init_pan is None:
                                init_pan = txt; ii = i; break
                    if not live_pan or not init_pan: continue
                    try:
                        ih = float(re.search(r'([\d.]+)', tds[li-1].get_text()).group(1))
                        il = float(re.search(r'([\d.]+)', tds[li+1].get_text()).group(1))
                        lh = float(re.search(r'([\d.]+)', tds[ii-1].get_text()).group(1))
                        ll = float(re.search(r'([\d.]+)', tds[ii+1].get_text()).group(1))
                    except:
                        ih = il = lh = ll = ''
                    yz_list.append({
                        'name': name,
                        'init_pan': init_pan, 'init_water_high': ih, 'init_water_low': il,
                        'live_pan': live_pan, 'live_water_high': lh, 'live_water_low': ll,
                    })
                    if len(yz_list) >= 3: break
                if len(yz_list) >= 3: break
            if len(yz_list) >= 3: break
        if yz_list:
            result['asian_list'] = yz_list
    except:
        pass
    return result

def fix_cache_file(cache_path, max_workers=10):
    if not os.path.exists(cache_path):
        log(f'[SKIP] 不存在: {cache_path}')
        return
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    league = cache.get('league', os.path.basename(cache_path))
    matches = cache.get('all_matches', [])
    total = len(matches)
    to_fix = []
    for m in matches:
        fid = str(m.get('FIXTUREID', ''))
        if not fid: continue
        oe = m.get('odds_europe') or {}
        oh = m.get('odds_handicap') or {}
        oa = m.get('odds_asian')
        needs_av = not (isinstance(oe, dict) and oe.get('av'))
        needs_companies = not (isinstance(oe, dict) and isinstance(oe.get('companies'), list) and len(oe['companies']) > 0)
        needs_iw_hc = not (isinstance(oh, dict) and oh.get('iw'))
        needs_jc_hc = not (isinstance(oh, dict) and oh.get('jc'))
        needs_asian = not (isinstance(oa, list) and len(oa) > 0)
        if needs_av or needs_companies or needs_iw_hc or needs_jc_hc or needs_asian:
            to_fix.append((fid, needs_av, needs_companies, needs_iw_hc, needs_jc_hc, needs_asian))
    if not to_fix:
        log(f'[✓] {league}: 全部完整，无需修复')
        return
    av_m = sum(1 for _, a, _, _, _, _ in to_fix if a)
    co_m = sum(1 for _, _, c, _, _, _ in to_fix if c)
    iw_m = sum(1 for _, _, _, i, _, _ in to_fix if i)
    jc_hc_m = sum(1 for _, _, _, _, j, _ in to_fix if j)
    as_m = sum(1 for _, _, _, _, _, a in to_fix if a)
    log(f'[ENRICH] {league}: 需修复 {len(to_fix)}/{total} (百家{av_m}, companies{co_m}, IW让球{iw_m}, 竞彩让球{jc_hc_m}, 亚盘{as_m})')
    
    fixed = {}
    errors = 0
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        fut_map = {executor.submit(fix_match, fid): (fid, na, nc, ni, nj, na2) for fid, na, nc, ni, nj, na2 in to_fix}
        for fut in as_completed(fut_map):
            fid, na, nc, ni, nj, na2 = fut_map[fut]
            try:
                fixed[fid] = fut.result()
                completed += 1
            except Exception as e:
                errors += 1
                if errors <= 3:
                    log(f'[WARN] FID={fid}: {type(e).__name__}: {str(e)[:100]}')
            if (completed + errors) % 20 == 0:
                log(f'  {league}: {completed+errors}/{len(to_fix)} (失败{errors})')
    
    updated = 0
    for m in matches:
        fid = str(m.get('FIXTUREID', ''))
        if fid not in fixed: continue
        r = fixed[fid]
        oe = m.get('odds_europe')
        if not isinstance(oe, dict):
            oe = {}
            m['odds_europe'] = oe
        if r.get('av') and not oe.get('av'):
            oe['av'] = r['av']
            updated += 1
        if r.get('companies') and not (isinstance(oe.get('companies'), list) and len(oe['companies']) > 0):
            oe['companies'] = r['companies']
            updated += 1
        oh = m.get('odds_handicap')
        if r.get('jc_hc') and not (isinstance(oh, dict) and oh.get('jc')):
            if not oh or not isinstance(oh, dict):
                oh = {}
                m['odds_handicap'] = oh
            oh['jc'] = r['jc_hc']
            updated += 1
        if r.get('iw_hc') and not (isinstance(oh, dict) and oh.get('iw')):
            if not oh or not isinstance(oh, dict):
                oh = {'jc': m.get('odds_handicap', {}).get('jc')} if m.get('odds_handicap') else {}
                m['odds_handicap'] = oh
            oh['iw'] = r['iw_hc']
            updated += 1
        # 亚盘
        oa = m.get('odds_asian')
        if r.get('asian_list') and not (isinstance(oa, list) and len(oa) > 0):
            m['odds_asian'] = r['asian_list']
            updated += 1
    
    cache['enriched_date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    log(f'[✓] {league}: 完成，{updated}个字段更新 (成功{completed}/失败{errors})')

if __name__ == '__main__':
    targets = []
    if '--core' in sys.argv:
        targets = [os.path.join(CACHE_DIR, fn) for fn in CORE_LEAGUES]
    else:
        for fn in sys.argv[1:]:
            if not fn.endswith('.json'): continue
            if os.path.exists(fn):
                targets.append(fn)
            else:
                p = os.path.join(CACHE_DIR, fn)
                if os.path.exists(p):
                    targets.append(p)
    if not targets:
        log('用法: python fix_enrich.py --core')
        log('  或: python fix_enrich.py 欧冠Champions League.json 韩职.json')
        sys.exit(1)
    log(f'待修复 {len(targets)} 个缓存文件...')
    for p in targets:
        fix_cache_file(p, max_workers=10)
