#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
赔率最小值匹配——同联赛+同亚盘+百家/竞彩/IW 最小值范围匹配
"""
import json, os, sys, re, math, time
from datetime import datetime, date
from collections import Counter

SD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(SD, 'data', 'league_cache')
TASKS_DIR = os.path.join(SD, 'tasks')

# ── 盘口名→HANDICAPLINE ──────────────────────────
_HANDICAP_ITEMS = sorted([
    ('平手', 0.0), ('平手/半球', 0.25), ('平半', 0.25),
    ('半球', -0.5), ('半球/一球', -0.75), ('半一', -0.75),
    ('一球', -1.0), ('一球/球半', -1.25), ('球半', -1.5),
    ('球半/两球', -1.75), ('两球', -2.0), ('两球/两球半', -2.25),
    ('两球半', -2.5), ('两球半/三球', -2.75), ('三球', -3.0),
    ('受平手/半球', 0.25), ('受平半', 0.25),
    ('受半球', 0.5), ('受半球/一球', 0.75), ('受半一', 0.75),
    ('受一球', 1.0), ('受一球/球半', 1.25),
    ('受球半', 1.5), ('受球半/两球', 1.75),
    ('受两球', 2.0), ('受两球/两球半', 2.25),
    ('受两球半', 2.5),
], key=lambda x: -len(x[0]))


def match_hc_name(txt):
    txt = txt.replace('\xa0', '').replace('↑', '').replace('↓', '').strip()
    for name, val in _HANDICAP_ITEMS:
        if name in txt:
            return val
    try:
        return float(txt)
    except:
        return None


def x_range(v):
    """数值→X.x范围: 1.63→(1.60, 1.69)"""
    if v is None:
        return None
    lo = math.floor(v * 10) / 10
    hi = round(lo + 0.09, 2)
    return (lo, hi)


# ── 实时抓取 ──────────────────────────────────────

def fetch_today_odds(fid):
    """抓取当天百家初赔/终赔、竞彩初赔/终赔、IW初赔/终赔"""
    import requests
    from bs4 import BeautifulSoup
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
         'Accept-Language': 'zh-CN,zh;q=0.9', 'Referer': 'https://odds.500.com/'}
    r = requests.get(f'https://odds.500.com/fenxi/ouzhi-{fid}.shtml', headers=h, timeout=10)
    r.encoding = 'gbk'
    s = BeautifulSoup(r.text, 'html.parser')
    av_init = av_live = jc_init = jc_live = iw_init = iw_live = None
    for table in s.find_all('table'):
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 12:
                continue
            nm = tds[1].get_text().strip()
            try:
                init = [float(tds[i].get_text().strip().replace('\xa0', '')) for i in [3, 4, 5]]
                live = [float(tds[i].get_text().strip().replace('\xa0', '')) for i in [6, 7, 8]]
            except:
                continue
            if '平均' in nm or '百家' in nm:
                av_init, av_live = init, live
            if ('官' in nm or '(中国)' in nm) and jc_live is None:
                jc_init, jc_live = init, live
            if nm.startswith('I') and '塞浦路斯' in nm:
                iw_init, iw_live = init, live
    return (av_init, av_live), (jc_init, jc_live), (iw_init, iw_live)


def fetch_macau_hc(fid):
    """抓取当天澳门亚盘 HANDICAPLINE"""
    import requests
    from bs4 import BeautifulSoup
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'zh-CN,zh;q=0.9', 'Referer': 'https://odds.500.com/'}
    r = requests.get(f'https://odds.500.com/fenxi/yazhi-{fid}.shtml', headers=h, timeout=10)
    r.encoding = 'gbk'
    s = BeautifulSoup(r.text, 'html.parser')
    for table in s.find_all('table'):
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 12:
                continue
            nm = tds[1].get_text().strip()
            if '门' not in nm:
                continue
            refs = [i for i in range(len(tds)) if tds[i].get('ref') and re.match(r'^-?[\d.]+$', tds[i].get('ref', ''))]
            if len(refs) < 2:
                continue
            lp = tds[refs[0]].get_text().strip().replace('\xa0', '').replace('↑', '').replace('↓', '').strip()
            ip = tds[refs[1]].get_text().strip().replace('\xa0', '').replace('↑', '').replace('↓', '').strip()
            return match_hc_name(lp), ip, lp
    return None, '', ''


# ── 缓存读取 ──────────────────────────────────────

def find_cache(league):
    if not os.path.exists(CACHE_DIR):
        return None
    best = 0
    best_fp = None
    for fn in os.listdir(CACHE_DIR):
        if not fn.endswith('.json'):
            continue
        lk = fn.replace('.json', '')
        if lk == league:
            score = 100
        elif lk.startswith(league) or league.startswith(lk):
            score = 50
        elif league in lk or lk in league:
            score = 10
        else:
            continue
        fp = os.path.join(CACHE_DIR, fn)
        if score > best:
            best = score
            best_fp = fp
    return best_fp


def get_today_matches(td):
    """从tasks/读取当天比赛列表"""
    ds = td.strftime('%Y-%m-%d')
    for base in [TASKS_DIR, os.path.join(SD, 'data', 'tasks')]:
        p = os.path.join(base, ds, 'matches_data.json')
        if os.path.exists(p):
            with open(p) as f:
                d = json.load(f)
            ml = []
            for g in d.get('groups', {}).values():
                for m in g.get('matches', []):
                    ml.append({
                        'home': m.get('home', '?'),
                        'away': m.get('away', '?'),
                        'fid': m.get('fid', ''),
                        'league': m.get('league', ''),
                        'matchnum': m.get('matchnum', '?'),
                    })
            return ml
    # 从500.com实时抓当天
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'zh-CN,zh;q=0.9'}
    r = requests.get(f'https://odds.500.com/jc/zhizun/index.php?c=one&cl=1&d={ds}', headers=h, timeout=10)
    r.encoding = 'gbk'
    import re
    # 简单解析
    ml = []
    for m in re.finditer(r'FID=(\d+).*?([^\s]+)\s*vs\s*([^\s<]+)', r.text):
        ml.append({'home': m.group(2), 'away': m.group(3), 'fid': m.group(1), 'league': '?', 'matchnum': '?'})
    return ml


# ── 历史匹配 ──────────────────────────────────────

def get_hist_odds(m):
    """从缓存中提取历史比赛的终赔"""
    oe = m.get('odds_europe', {})
    if not isinstance(oe, dict):
        return None, None, None
    # 百家
    av = oe.get('av')
    av_live = None
    if isinstance(av, dict) and av.get('lw') is not None:
        av_live = (float(av['lw']), float(av['ld']), float(av['ll']))
    # 竞彩
    jc = oe.get('jc')
    jc_live = None
    if isinstance(jc, dict) and jc.get('lw') is not None:
        jc_live = (float(jc['lw']), float(jc['ld']), float(jc['ll']))
    # IW
    iw_live = None
    for c in oe.get('companies', []):
        if '塞浦路斯' in c.get('name', ''):
            live = c.get('live', [])
            if live and len(live) >= 3:
                try:
                    iw_live = (float(live[0]), float(live[1]), float(live[2]))
                except:
                    pass
            break
    return av_live, jc_live, iw_live


def get_hist_macau(m):
    """从缓存中获取历史澳门亚盘终盘值"""
    oa = m.get('odds_asian')
    if not isinstance(oa, list):
        return None
    for item in oa:
        if '门' in item.get('name', ''):
            lp = item.get('live_pan', '').replace('↑', '').replace('↓', '').replace(' ', '').strip()
            return match_hc_name(lp)
    if oa:
        lp = oa[0].get('live_pan', '').replace('↑', '').replace('↓', '').replace(' ', '').strip()
        return match_hc_name(lp)
    return None


def get_hist_hc(m):
    """从缓存提取让球数据"""
    oh = m.get('odds_handicap', {})
    if not isinstance(oh, dict):
        return '-', '-', '-'
    for k in ['jc', 'iw']:
        hd = oh.get(k, {})
        if isinstance(hd, dict) and hd.get('dir'):
            d = hd['dir']
            init_a = hd.get('init', [])
            live_a = hd.get('live', [])
            if init_a and len(init_a) >= 3:
                return d, f'{init_a[0]:.2f}/{init_a[1]:.2f}/{init_a[2]:.2f}', f'{live_a[0]:.2f}/{live_a[1]:.2f}/{live_a[2]:.2f}'
            # 格式B
            iw_v = hd.get('iw')
            if iw_v is not None:
                return d, f'{iw_v}/{hd.get("id","?")}/{hd.get("il","?")}', f'{hd.get("lw","?")}/{hd.get("ld","?")}/{hd.get("ll","?")}'
    return '-', '-', '-'


def get_hist_asian(m):
    """从缓存提取澳门亚盘初终盘名"""
    oa = m.get('odds_asian')
    if not isinstance(oa, list):
        return '-', '-'
    for item in oa:
        if '门' in item.get('name', ''):
            ip = item.get('init_pan', '-').replace('↑', '').replace('↓', '').replace(' ', '').strip()
            lp = item.get('live_pan', '-').replace('↑', '').replace('↓', '').replace(' ', '').strip()
            return ip, lp
    if oa:
        ip = oa[0].get('init_pan', '-').replace('↑', '').replace('↓', '').replace(' ', '').strip()
        lp = oa[0].get('live_pan', '-').replace('↑', '').replace('↓', '').replace(' ', '').strip()
        return ip, lp
    return '-', '-'


def get_hist_init_odds(m):
    """提取初赔（用于展示）"""
    oe = m.get('odds_europe', {})
    if not isinstance(oe, dict):
        return None, None, None
    av = oe.get('av')
    av_init = None
    if isinstance(av, dict) and av.get('iw') is not None:
        av_init = (float(av['iw']), float(av['id']), float(av['il']))
    jc = oe.get('jc')
    jc_init = None
    if isinstance(jc, dict) and jc.get('iw') is not None:
        jc_init = (float(jc['iw']), float(jc['id']), float(jc['il']))
    iw_init = None
    for c in oe.get('companies', []):
        if '塞浦路斯' in c.get('name', ''):
            init = c.get('init', [])
            if init and len(init) >= 3:
                try:
                    iw_init = (float(init[0]), float(init[1]), float(init[2]))
                except:
                    pass
            break
    return av_init, jc_init, iw_init


# ── 输出 ──────────────────────────────────────────

def fmt_odds(t):
    if t is None:
        return '-/-/-'
    return f'{t[0]:.2f}/{t[1]:.2f}/{t[2]:.2f}'


def main():
    from argparse import ArgumentParser
    p = ArgumentParser(description='赔率最小值匹配')
    p.add_argument('--date', type=str, required=True)
    a = p.parse_args()

    td = datetime.strptime(a.date, '%Y-%m-%d').date()
    ds = td.strftime('%Y-%m-%d')
    print(f'📅 {ds}\n')

    ms = get_today_matches(td)
    if not ms:
        print('⚠️ 无比赛')
        sys.exit(1)
    print(f'📋 {len(ms)} 场\n')

    total_hits = 0
    for i, tm in enumerate(ms):
        fid = tm.get('fid', '')
        home = tm.get('home', '?')
        away = tm.get('away', '?')
        league = tm.get('league', '?')

        print(f'[{i + 1}/{len(ms)}] {home} vs {away} FID={fid}...', end=' ')
        sys.stdout.flush()

        # 实时抓取当天数据
        (av_init, av_live), (jc_init, jc_live), (iw_init, iw_live) = fetch_today_odds(fid)
        macau_val, macau_ip, macau_lp = fetch_macau_hc(fid)
        time.sleep(0.3)

        if not av_live or macau_val is None:
            print('⚠️ 缺数据')
            print()
            continue

        av_min = min(av_live)
        av_min_idx = av_live.index(av_min)  # 0=主胜, 1=平, 2=客胜
        jc_min = min(jc_live) if jc_live else None
        jc_min_idx = jc_live.index(jc_min) if jc_live else None
        iw_min = min(iw_live) if iw_live else None
        iw_min_idx = iw_live.index(iw_min) if iw_live else None
        av_r = x_range(av_min)
        jc_r = x_range(jc_min)
        iw_r = x_range(iw_min)

        LAB = ['胜', '平', '负']

        def rlabel2(r, idx):
            if r is None or idx is None:
                return '缺'
            return f'{LAB[idx]}{r[0]:.1f}x'

        def full_odds_label(init, live, r, idx):
            """格式：⬇⬇⬆ 初2.91/3.59/2.12→终2.84/3.59/2.22(负2.2x)"""
            if not init or not live:
                return '缺'
            d = ''
            for i in range(3):
                if live[i] > init[i] + 0.01: d += '⬆'
                elif live[i] < init[i] - 0.01: d += '⬇'
                else: d += '➡'
            return f'{d} 初{init[0]:.2f}/{init[1]:.2f}/{init[2]:.2f}→终{live[0]:.2f}/{live[1]:.2f}/{live[2]:.2f}({rlabel2(r, idx)})'
        av_label = full_odds_label(av_init, av_live, av_r, av_min_idx)
        jc_label = full_odds_label(jc_init, jc_live, jc_r, jc_min_idx) if jc_live and jc_init else '缺'
        iw_label = full_odds_label(iw_init, iw_live, iw_r, iw_min_idx) if iw_live and iw_init else '缺'
        print(f'澳门:{macau_ip}→{macau_lp}({macau_val})')
        print(f'  百 {av_label}')
        print(f'  竞 {jc_label}')
        print(f'  IW {iw_label}')

        # 加载缓存
        fp = find_cache(league)
        if not fp:
            print('  无缓存\n')
            continue
        with open(fp, encoding='utf-8') as f:
            cd = json.load(f)
        ml = cd.get('all_matches', [])
        print(f'  缓存: {os.path.basename(fp)}({len(ml)}场)')

        # 匹配历史
        target = round(macau_val, 2)
        hits = []
        for m in ml:
            # 亚盘
            hist_macau = get_hist_macau(m)
            if hist_macau is None or abs(hist_macau - target) > 0.01:
                continue

            # 百家min范围
            ha, hj, hi = get_hist_odds(m)
            if ha is None:
                continue
            hm = min(ha)
            if av_r and not (av_r[0] <= hm <= av_r[1]):
                continue

            # 竞彩min范围（有竞彩数据才过滤）
            if jc_r and hj is not None:
                jm = min(hj)
                if not (jc_r[0] <= jm <= jc_r[1]):
                    continue

            # IWmin范围（有IW数据才过滤）
            if iw_r and hi is not None:
                im = min(hi)
                if not (iw_r[0] <= im <= iw_r[1]):
                    continue

            # 方向一致性：三公司最小值必须在同一列（与今天比赛一致）
            ha_min_idx = ha.index(hm) if len(ha) == 3 else -1
            if ha_min_idx != av_min_idx:
                continue
            if hj is not None and jc_min_idx is not None and len(hj) == 3:
                hjm = min(hj)
                if hj.index(hjm) != jc_min_idx:
                    continue
            if hi is not None and iw_min_idx is not None and len(hi) == 3:
                him = min(hi)
                if hi.index(him) != iw_min_idx:
                    continue

            # 收集展示数据
            ha_i, hj_i, hi_i = get_hist_init_odds(m)
            hc_d, hc_i, hc_l = get_hist_hc(m)
            as_ip, as_lp = get_hist_asian(m)
            sc_h = m.get('HOMESCORE', '')
            sc_a = m.get('AWAYSCORE', '')
            score = f'{sc_h}:{sc_a}' if sc_h != '' else ''
            result = m.get('_computed', {}).get('match_result', '') if m.get('_computed') else ''
            hits.append({
                'date': m.get('MATCHDATE', ''),
                'home': m.get('HOMETEAMSXNAME', ''),
                'away': m.get('AWAYTEAMSXNAME', ''),
                'score': score,
                'result': result,
                'av_i': ha_i, 'av_l': ha,
                'jc_i': hj_i, 'jc_l': hj,
                'iw_i': hi_i, 'iw_l': hi,
                'hc_d': hc_d, 'hc_i': hc_i, 'hc_l': hc_l,
                'as_ip': as_ip, 'as_lp': as_lp,
            })

        hits.sort(key=lambda x: x['date'])
        # 统计汇总
        cnt = Counter()
        for h in hits:
            r = h.get('result', '')
            if '主胜' in r: cnt['主胜'] += 1
            elif '客胜' in r: cnt['客胜'] += 1
            elif '平' in r: cnt['平局'] += 1
            else: cnt['其他'] += 1
        total = len(hits)
        stats = '|'.join(f'{res}:{c}({c*100//total}%)' for res, c in sorted(cnt.items()))
        print(f'  📊 {total}场（{stats}）')
        for h in hits:
            ri = {'主胜': '✅', '平局': '➖', '客胜': '❌'}.get(h.get('result', ''), '')
            # 计算每家公司最小值标签
            def min_label(odds):
                if not odds or len(odds) < 3: return '缺'
                idx = odds.index(min(odds))
                return f'{["胜","平","负"][idx]}{min(odds):.2f}'
            # 计算方向变化
            def dir_change(init, live):
                if not init or not live: return ''
                d = []
                for i in range(3):
                    if live[i] > init[i] + 0.01: d.append('⬆')
                    elif live[i] < init[i] - 0.01: d.append('⬇')
                    else: d.append('➡')
                return ''.join(d)
            print(f'  [{h["date"]}] {h["home"]} vs {h["away"]}  {h["score"]} {ri}')
            av_dir = dir_change(h['av_i'], h['av_l'])
            print(f'    百家 {av_dir} 初:{fmt_odds(h["av_i"])} → 终:{fmt_odds(h["av_l"])}  ←最小值{min_label(h["av_l"])}')
            if h['jc_l']:
                jc_dir = dir_change(h['jc_i'], h['jc_l'])
                print(f'    竞彩 {jc_dir} 初:{fmt_odds(h["jc_i"])} → 终:{fmt_odds(h["jc_l"])}  ←最小值{min_label(h["jc_l"])}')
            if h['iw_l']:
                iw_dir = dir_change(h['iw_i'], h['iw_l'])
                print(f'    IW   {iw_dir} 初:{fmt_odds(h["iw_i"])} → 终:{fmt_odds(h["iw_l"])}  ←最小值{min_label(h["iw_l"])}')
            if h['hc_d'] != '-':
                print(f'    让球方向:{h["hc_d"]}  初:{h["hc_i"]} → 终:{h["hc_l"]}')
            print(f'    亚盘 {h["as_ip"]} → {h["as_lp"]}')
            print()

        if hits:
            total_hits += 1
        print()

    print(f'📊 汇总: {total_hits}/{len(ms)} 场找到匹配')


if __name__ == '__main__':
    main()
