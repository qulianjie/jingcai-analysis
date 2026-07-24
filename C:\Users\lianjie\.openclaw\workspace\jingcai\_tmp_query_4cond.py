# -*- coding: utf-8 -*-
"""4条件查询：联赛一致 + 澳门亚盘受让一致 + 竞彩欧赔盘路一致 + IW欧赔盘路一致"""
import json, sys, os, re, time, math
from datetime import datetime
from collections import Counter

SD = os.path.dirname(os.path.abspath(__file__))
TD = os.path.join(SD, 'tasks')
CD = os.path.join(SD, 'data', 'league_cache')

import requests
sess = requests.Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0'})

def dr(iv, lv):
    d = ''
    for a, b in zip(iv, lv):
        if b > a + 0.01: d += '⬆'
        elif b < a - 0.01: d += '⬇'
        else: d += '➡'
    return d

def get_ms(ds=None):
    if ds is None: ds = datetime.now().strftime('%Y-%m-%d')
    for base in [TD, os.path.join(SD, 'data', 'tasks')]:
        p = os.path.join(base, ds, 'matches_data.json')
        if os.path.exists(p):
            with open(p, 'r') as f: d = json.load(f)
            ml = []
            for gd in d.get('groups', {}).values(): ml.extend(gd.get('matches', []))
            return ml, ds
    return [], ds

def fo(fid):
    """获取赔率，同odds_consistency.fo()"""
    r = {'jc': {}, 'av': {}, 'hc': {}, 'as': {}}
    try:
        for src, key in [('ouzhi', 'jc'), ('ouzhi', 'av'), ('rangqiu', 'hc')]:
            url = f'https://odds.500.com/fenxi/{src}-{fid}.shtml'
            x = sess.get(url, timeout=10); x.encoding = 'gbk'
            s = BeautifulSoup(x.text, 'html.parser')
            for t in s.find_all('table'):
                for tr in t.find_all('tr'):
                    td = tr.find_all('td')
                    if len(td) < 12: continue
                    t0 = td[0].get_text().strip()
                    if src == 'ouzhi':
                        if key == 'jc' and t0 != '1': continue
                        if key == 'av':
                            if '平均' not in td[1].get_text() and '百家' not in td[1].get_text(): continue
                    elif src == 'rangqiu' and t0 != '1': continue
                    n = []
                    for idx in [3, 4, 5, 6, 7, 8] if src == 'ouzhi' else [4, 5, 6, 7, 8, 9]:
                        try: n.append(float(td[idx].get_text().strip().replace(chr(160), '')))
                        except: pass
                    if len(n) < 6: continue
                    r[key] = {'iw': n[0], 'id': n[1], 'il': n[2], 'lw': n[3], 'ld': n[4], 'll': n[5], 'dir': dr(n[:3], n[3:6])}
                    break
    except: pass
    try:
        url = f'https://odds.500.com/fenxi/yazhi-{fid}.shtml'
        x = sess.get(url, timeout=10); x.encoding = 'gbk'
        s = BeautifulSoup(x.text, 'html.parser')
        for t in s.find_all('table'):
            for tr in t.find_all('tr'):
                td = tr.find_all('td')
                if len(td) < 12: continue
                t0 = td[0].get_text().strip()
                if not t0.isdigit(): continue
                n = int(t0)
                if n not in (1, 2, 3): continue
                nm = td[1].get_text().strip()
                try:
                    ih = float(re.search(r'([\d.]+)', td[3].get_text()).group(1))
                    il = float(re.search(r'([\d.]+)', td[5].get_text()).group(1))
                    lh = float(re.search(r'([\d.]+)', td[9].get_text()).group(1))
                    ll = float(re.search(r'([\d.]+)', td[11].get_text()).group(1))
                except: ih = il = lh = ll = ''
                ip = td[4].get_text().strip().replace(chr(160), '')
                lp = td[10].get_text().strip().replace(chr(160), '')
                e = {'name': nm, 'ip': ip, 'ih': ih, 'il': il, 'lp': lp, 'lh': lh, 'll': ll}
                if '澳门' in nm or n == 1:
                    if not r['as'] or '澳门' in nm: r['as'] = e
    except: pass
    return r

def ld(league):
    """找联赛缓存"""
    cp = None; best = 0
    if not os.path.exists(CD): return None
    for fn in os.listdir(CD):
        if not fn.endswith('.json'): continue
        lk = fn.replace('.json', '')
        if lk == league: score = 100
        elif lk.startswith(league) or league.startswith(lk): score = 50
        elif league in lk or lk in league: score = 10
        else: continue
        if score > best: best = score; cp = os.path.join(CD, fn)
    if not cp or not os.path.exists(cp): return None
    with open(cp, 'r') as f: d = json.load(f)
    ml = d.get('all_matches', [])
    if not ml: return None
    return {'league': d.get('league', league), 'matches': ml, 'total': len(ml)}

def get_iw_dir(companies):
    """从companies列表找Interwetten的方向"""
    if not companies: return ''
    for c in companies:
        name = c.get('name', '')
        if 'Interwetten' in name or 'interwetten' in name.lower():
            init = c.get('init', [])
            live = c.get('live', [])
            if init and live:
                try:
                    fi = [float(x) for x in init[:3]]
                    fl = [float(x) for x in live[:3]]
                    return dr(fi, fl)
                except: pass
    return ''

def search_4cond(hist, today_odds, today_league):
    """4条件搜索：联赛一致+澳门亚盘受让一致+竞彩欧赔盘路一致+IW欧赔盘路一致"""
    if not hist: return None
    
    # 当天的4条件值
    jc = today_odds.get('jc', {})
    asn = today_odds.get('as', {})
    
    # 当天澳门亚盘方向（受 vs 非受）
    today_as_lp = asn.get('lp', '')
    today_is_shou = today_as_lp.startswith('受')
    
    # 当天竞彩欧赔盘路
    today_jc_dir = jc.get('dir', '')
    
    # 当天IW欧赔盘路 - 从百家companies中找IW
    av = today_odds.get('av', {})
    today_iw_dir = ''
    try:
        url = f'https://odds.500.com/fenxi/ouzhi-{today_fid}.shtml'
        # We need to get companies for IW - already in 'av' data
    except: pass
    
    # 重新获取companies以提取IW
    today_iw_dir = _get_today_iw_dir(today_odds)
    
    if not today_jc_dir or not today_iw_dir:
        return None
    
    ml = hist['matches']
    results = []
    
    for hm in ml:
        oe = hm.get('odds_europe', {})
        oh = hm.get('odds_handicap', {})
        oa = hm.get('odds_asian', [])
        
        # 条件1：联赛一致（隐含，已按联赛缓存加载）
        
        # 条件2：澳门亚盘受让方向一致
        macau_asian = None
        if oa:
            for item in oa:
                if '澳门' in item.get('name', ''):
                    macau_asian = item
                    break
        if not macau_asian:
            continue
        hist_lp = macau_asian.get('live_pan', macau_asian.get('ip', ''))
        hist_is_shou = hist_lp.startswith('受')
        if hist_is_shou != today_is_shou:
            continue
        
        # 条件3：竞彩欧赔盘路一致
        jc_data = oe.get('jc', {}) if oe else {}
        if not jc_data:
            continue
        try:
            parts = []
            for init_k, live_k in [('iw','lw'), ('id','ld'), ('il','ll')]:
                fi = float(jc_data[init_k])
                fl = float(jc_data[live_k])
                if fl < fi - 0.01: parts.append('⬇')
                elif fl > fi + 0.01: parts.append('⬆')
                else: parts.append('➡')
            hist_jc_dir = ''.join(parts)
        except:
            continue
        if hist_jc_dir != today_jc_dir:
            continue
        
        # 条件4：IW欧赔盘路一致
        companies = oe.get('companies', []) if oe else []
        hist_iw_dir = _get_iw_dir_from_companies(companies)
        if not hist_iw_dir or hist_iw_dir != today_iw_dir:
            continue
        
        # 全部4条件匹配！
        home = hm.get('HOMETEAMSXNAME', '?')
        away = hm.get('AWAYTEAMSXNAME', '?')
        hdate = hm.get('MATCHDATE', '')
        hs = hm.get('HOMESCORE') or hm.get('homeScore')
        aws = hm.get('AWAYSCORE') or hm.get('awayScore')
        score = f'{hs}:{aws}' if hs is not None else '未赛'
        result = hm.get('lpl_on', '?')
        
        # 赔率详情
        jc_iw = jc_data.get('iw', '?'); jc_id = jc_data.get('id', '?'); jc_il = jc_data.get('il', '?')
        jc_lw = jc_data.get('lw', '?'); jc_ld = jc_data.get('ld', '?'); jc_ll = jc_data.get('ll', '?')
        
        results.append({
            'date': hdate, 'home': home, 'away': away, 'score': score,
            'result': result, 'jc_init': f'{jc_iw}/{jc_id}/{jc_il}',
            'jc_live': f'{jc_lw}/{jc_ld}/{jc_ll}',
            'macau_pan': hist_lp,
        })
    
    results.sort(key=lambda x: x['date'])
    return {'matches': results, 'total': len(results), 'hist': len(ml),
            'today_as': today_as_lp, 'today_jc_dir': today_jc_dir,
            'today_iw_dir': today_iw_dir}

def _get_today_iw_dir(odds):
    """获取当天IW方向"""
    try:
        url = f'https://odds.500.com/fenxi/ouzhi-{today_fid}.shtml'
        x = sess.get(url, timeout=10); x.encoding = 'gbk'
        s = BeautifulSoup(x.text, 'html.parser')
        for t in s.find_all('table'):
            for tr in t.find_all('tr'):
                td = tr.find_all('td')
                if len(td) < 12: continue
                t0 = td[0].get_text().strip()
                if t0 != '2': continue  # IW is usually row 2
                name = td[1].get_text().strip()
                if 'Interwetten' not in name and 'interwetten' not in name.lower():
                    continue
                init = [] 
                live = []
                for idx in [3, 4, 5]:
                    try: init.append(float(td[idx].get_text().strip().replace(chr(160), '')))
                    except: break
                for idx in [6, 7, 8]:
                    try: live.append(float(td[idx].get_text().strip().replace(chr(160), '')))
                    except: break
                if len(init) == 3 and len(live) == 3:
                    return dr(init, live)
    except: pass
    return ''

def _get_iw_dir_from_companies(companies):
    """从companies列表找IW方向"""
    if not companies: return ''
    for c in companies:
        name = c.get('name', '')
        if 'Interwetten' in name or 'interwetten' in name.lower():
            init = c.get('init', [])
            live = c.get('live', [])
            if init and live:
                try:
                    fi = [float(x) for x in init[:3]]
                    fl = [float(x) for x in live[:3]]
                    return dr(fi, fl)
                except: pass
    return ''

from bs4 import BeautifulSoup

if __name__ == '__main__':
    ds = sys.argv[1] if len(sys.argv) > 1 else None
    ml, dt = get_ms(ds)
    if not ml:
        print('无比赛数据')
        sys.exit(1)
    
    print(f'# 4条件查询：联赛一致+澳门亚盘受让一致+竞彩欧赔盘路一致+IW欧赔盘路一致')
    print(f'{dt} 共{len(ml)}场比赛\n')
    
    for m in ml:
        fid = m.get('fid', '')
        if not fid: continue
        global today_fid
        today_fid = fid
        
        league = m.get('league', '')
        print(f'## {m["matchnum"]} {m["home"]}vs{m["away"]} | {league}')
        print()
        
        # 取赔率
        print(f'  [采集]...', end=' ')
        sys.stdout.flush()
        odds = fo(fid)
        print('OK')
        time.sleep(0.3)
        
        # 找联赛缓存
        hist = ld(league)
        if not hist:
            print(f'  无联赛缓存\n')
            continue
        print(f'  缓存:{hist["league"]}({hist["total"]}场)')
        
        # 4条件搜索
        res = search_4cond(hist, odds, league)
        if not res:
            print(f'  无匹配\n')
            continue
        
        print(f'  当天: 澳门{res["today_as"]} | 竞彩{res["today_jc_dir"]} | IW{res["today_iw_dir"]}')
        print(f'  匹配: {res["total"]}场 (共{res["hist"]}场历史)\n')
        
        if res['matches']:
            for hm in res['matches'][:15]:
                ri = {'主胜': '✅', '平局': '➖', '客胜': '❌'}.get(hm.get('result', ''), '')
                print(f'  {hm["home"]}vs{hm["away"]} {hm["score"]}{ri} ({hm["date"]})')
                print(f'    竞彩: {hm["jc_init"]} → {hm["jc_live"]} | 澳门: {hm["macau_pan"]}')
        if len(res['matches']) > 15:
            print(f'  ...还有{len(res["matches"])-15}场')
        print()
