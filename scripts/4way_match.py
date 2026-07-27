#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞彩4条件历史匹配（jingcai-4way-match）
当天竞彩比赛 → 联赛一致 + 澳门亚盘受让球一致 + 竞彩欧赔盘路一致 + IW欧赔盘路一致 → 历史同场次

澳门亚盘（受让球）从 odds.500.com/fenxi/yazhi-{fid}.shtml 实时抓取
竞彩/IW盘路方向从 odds.500.com/fenxi/ouzhi-{fid}.shtml 实时抓取

用法:
    python scripts/4way_match.py [--date YYYY-MM-DD]
"""

import json, os, sys, re, math
from datetime import datetime, date
from collections import Counter

SD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(SD, 'data', 'league_cache')
TASKS_DIR = os.path.join(SD, 'tasks')

# 盘口名 → HANDICAPLINE 映射（按名称长度降序，避免"半球"提前匹配"半球/一球"）
_HANDICAP_ITEMS = sorted([
    ('平手', 0.0), ('平手/半球', -0.25), ('平半', -0.25),
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
], key=lambda x: -len(x[0]))  # 长度降序


def _match_hc_name(txt):
    """从文本中匹配盘口名，返回 HANDICAPLINE 值"""
    txt = txt.replace('\xa0', '').replace('↑', '').replace('↓', '').strip()
    for name, val in _HANDICAP_ITEMS:
        if name in txt:
            return val
    try:
        return float(txt)
    except:
        return None


# ── 方向计算 ──────────────────────────────────────

def dir_from_3(init, live):
    try:
        parts = []
        for i, l in zip(init, live):
            fi, fl = float(i), float(l)
            if fl <= fi - 0.01: parts.append('⬇')
            elif fl >= fi + 0.01: parts.append('⬆')
            else: parts.append('➡')
        return ''.join(parts)
    except:
        return None


def dir_6(wi, di, li, wl, dl, ll):
    return dir_from_3([wi, di, li], [wl, dl, ll])


# ── 实时抓取 ──────────────────────────────────────

def fetch_odds_dirs(fid):
    """从500.com欧赔页抓取 竞彩+IW 盘路方向"""
    if not fid:
        return None, None
    import requests
    from bs4 import BeautifulSoup
    url = f'https://odds.500.com/fenxi/ouzhi-{fid}.shtml'
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
         'Accept-Language': 'zh-CN,zh;q=0.9'}
    try:
        r = requests.get(url, headers=h, timeout=10)
        r.encoding = 'gbk'
        sp = BeautifulSoup(r.text, 'html.parser')
        jc = iw = None
        for t in sp.find_all('table'):
            for tr in t.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12:
                    continue
                nm = tds[1].get_text().strip()
                try:
                    init = [float(tds[i].get_text().strip().replace('\xa0', '')) for i in [3, 4, 5]]
                    live = [float(tds[i].get_text().strip().replace('\xa0', '')) for i in [6, 7, 8]]
                except:
                    continue
                d = dir_from_3(init, live)
                if not d:
                    continue
                if ('官' in nm or '(中国)' in nm) and not jc:
                    jc = d
                if nm.startswith('I') and not iw:
                    iw = d
        return jc, iw
    except:
        return None, None


def fetch_av_w(fid):
    """从500.com欧赔页抓取百家终赔主胜"""
    if not fid:
        return None
    import requests
    from bs4 import BeautifulSoup
    url = f'https://odds.500.com/fenxi/ouzhi-{fid}.shtml'
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'zh-CN,zh;q=0.9'}
    try:
        r = requests.get(url, headers=h, timeout=10)
        r.encoding = 'gbk'
        sp = BeautifulSoup(r.text, 'html.parser')
        for t in sp.find_all('table'):
            for tr in t.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12:
                    continue
                nm = tds[1].get_text().strip()
                if '平均' in nm or '百家' in nm:
                    try:
                        return float(tds[6].get_text().strip().replace('\xa0', ''))
                    except:
                        return None
        return None
    except:
        return None

def fetch_macau_handicap(fid):
    """从500.com亚盘页提取澳门亚盘 HANDICAPLINE 数值（ref属性，带正负号）"""
    if not fid:
        return None
    import requests
    from bs4 import BeautifulSoup
    url = f'https://odds.500.com/fenxi/yazhi-{fid}.shtml'
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
         'Accept-Language': 'zh-CN,zh;q=0.9'}
    try:
        r = requests.get(url, headers=h, timeout=10)
        r.encoding = 'gbk'
        sp = BeautifulSoup(r.text, 'html.parser')
        for t in sp.find_all('table'):
            for tr in t.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 6:
                    continue
                # 找澳门公司行
                nm = tds[0].get_text().strip()
                if '门' not in nm:
                    nm = tds[1].get_text().strip() if len(tds) > 1 else ''
                if '门' not in nm:
                    continue
                # 从内嵌 pl_table_data 中找带 ref 的单元格
                for idx in [2, 8]:  # 初盘/即时盘
                    if idx >= len(tds):
                        continue
                    inner = tds[idx].find('table', class_='pl_table_data') if tds[idx] else None
                    if not inner:
                        continue
                    for cell in inner.find_all('td'):
                        ref = cell.get('ref', '')
                        if ref:
                            try:
                                return float(ref)
                            except:
                                continue
                continue
    except:
        return None


# ── 从缓存获取 ──────────────────────────────────

def get_jc_dir(m):
    oe = m.get('odds_europe')
    if not oe:
        return None
    for c in oe.get('companies', []):
        if '官' in c.get('name', ''):
            d = c.get('dir')
            if d:
                return d
    return None


def get_iw_dir(m):
    oe = m.get('odds_europe')
    if not oe:
        return None
    for c in oe.get('companies', []):
        if c.get('name', '').startswith('I'):
            d = c.get('dir')
            if d:
                return d
    iw = oe.get('iw')
    if isinstance(iw, dict) and iw.get('iw'):
        return dir_6(iw['iw'], iw['id'], iw['il'], iw['lw'], iw['ld'], iw['ll'])
    return None


def get_hc(m):
    try:
        return float(m.get('HANDICAPLINE', 0)), m.get('HANDICAPLINENAME', '')
    except:
        return None, None


def get_score(m):
    hs, aw = m.get('HOMESCORE'), m.get('AWAYSCORE')
    r = m.get('_computed', {}).get('match_result') or m.get('RESULT', '')
    if hs is not None and aw is not None:
        return f'{int(hs)}:{int(aw)}', r
    return '-:-', r


# ── 获取当天比赛 ──────────────────────────────────

def get_today_matches(target_date):
    date_s = target_date.strftime('%Y-%m-%d')
    mf = os.path.join(TASKS_DIR, date_s, 'matches_data.json')
    if os.path.exists(mf):
        with open(mf, encoding='utf-8') as f:
            data = json.load(f)
        ms = data.get('matches', data.get('data', [])) if isinstance(data, dict) else data
        if not ms and isinstance(data, dict):
            # 处理 pipeline 格式: {groups: {周三: {matches: [...]}}}
            for g in data.get('groups', {}).values():
                ms.extend(g.get('matches', []))
        if ms:
            # 统一字段名
            out = []
            for m in ms:
                out.append({
                    'home_team': m.get('home_team') or m.get('home', '?'),
                    'away_team': m.get('away_team') or m.get('away', '?'),
                    'league_name': m.get('league_name') or m.get('league', '?'),
                    'fid': str(m.get('fid', '')),
                    'match_num': m.get('match_num') or m.get('matchnum', ''),
                })
            return out
    td = os.path.join(TASKS_DIR, date_s, 'data')
    if os.path.exists(td):
        ms = []
        for x in sorted(os.listdir(td)):
            mp = os.path.join(td, x, 'meta.json')
            if os.path.exists(mp):
                with open(mp, encoding='utf-8') as f:
                    ms.append(json.load(f))
        if ms:
            return ms
    return fetch_500_today()


def fetch_500_today():
    import requests
    from bs4 import BeautifulSoup
    url = 'http://trade.500.com/jczq/'
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
         'Accept-Language': 'zh-CN,zh;q=0.9'}
    try:
        r = requests.get(url, headers=h, timeout=15)
        r.encoding = 'gbk'
        sp = BeautifulSoup(r.text, 'html.parser')
        ms = []
        for tr in sp.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 8:
                continue
            try:
                mn = tds[0].get_text().strip()
                if not re.match(r'周[一二三四五六日]\d{3}', mn):
                    continue
                league = tds[1].get_text().strip()
                ht = tds[3].find('span', class_='team-l')
                at = tds[3].find('span', class_='team-r')
                home = ht.find('a').get_text().strip() if (ht and ht.find('a')) else ''
                away = at.find('a').get_text().strip() if (at and at.find('a')) else ''
                fid = ''
                for a in tds[6].find_all('a'):
                    m = re.search(r'shuju-(\d+)\.shtml', a.get('href', ''))
                    if m:
                        fid = m.group(1)
                        break
                ms.append({'home_team': home, 'away_team': away, 'league_name': league,
                           'fid': fid, 'match_num': mn})
            except:
                continue
        return ms
    except:
        return []


def find_cache(league):
    """找联赛缓存：优先已富集、场数多的"""
    if not league:
        return None
    # 联赛名别名映射（500.com名 → 缓存文件名）
    ALIAS = {
        '韩职': 'K1联赛',
        'K1联赛': '韩职',
        '美职足': '美职联',
        '美职联': '美职足',
    }
    league = ALIAS.get(league, league)
    fs = [f for f in os.listdir(CACHE_DIR) if f.endswith('.json')]
    # 先找精确匹配
    exact = []
    for fn in fs:
        b = fn[:-5]
        if b == league or b in league or league in b:
            exact.append((fn, b))
    if not exact:
        # 模糊匹配
        cl = re.sub(r'\s+', '', league)
        for fn in fs:
            b = re.sub(r'\s+', '', fn[:-5])
            if cl in b or b in cl:
                exact.append((fn, fn[:-5]))
    if not exact:
        return None
    # 多个匹配：选已富集(场数多的)
    best_fn = None
    best_score = -1
    for fn, _ in exact:
        try:
            with open(os.path.join(CACHE_DIR, fn), encoding='utf-8') as f:
                d = json.load(f)
            cnt = len(d.get('all_matches', []))
            enriched = 1 if d.get('enriched') else 0
            score = cnt * 10 + (1000 if enriched else 0)
            if score > best_score:
                best_score = score
                best_fn = fn
        except:
            pass
    if best_fn:
        return os.path.join(CACHE_DIR, best_fn)
    return None


def get_hc_dir(m):
    """从缓存中获取让球方向"""
    oh = m.get('odds_handicap', {})
    if not isinstance(oh, dict):
        return None
    for k in ['jc', 'iw']:
        d = oh.get(k, {})
        if isinstance(d, dict):
            hd = d.get('dir')
            if hd:
                return hd
    return None


def fetch_handicap_dir(fid):
    """从500.com让球页抓取今日让球方向（竞彩官方行）"""
    if not fid:
        return None
    import requests
    from bs4 import BeautifulSoup
    url = f'https://odds.500.com/fenxi/rangqiu-{fid}.shtml'
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=h, timeout=10)
        r.encoding = 'gbk'
        sp = BeautifulSoup(r.text, 'html.parser')
        for table in sp.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                td1 = tds[1].get_text().strip()
                if '官' in td1 or '中国' in td1:
                    nums = []
                    for idx in [4, 5, 6, 7, 8, 9]:
                        val = tds[idx].get_text().strip().replace(chr(160), '')
                        try: nums.append(float(val))
                        except: break
                    if len(nums) >= 6:
                        d = ''
                        for a, b in zip(nums[:3], nums[3:6]):
                            if b > a + 0.01: d += '⬆'
                            elif b < a - 0.01: d += '⬇'
                            else: d += '➡'
                        return d
        return None
    except:
        return None

def get_iw_hc_dir(m):
    """从缓存中获取IW让球方向"""
    oh = m.get('odds_handicap')
    if not isinstance(oh, dict):
        return None
    iw = oh.get('iw')
    if isinstance(iw, dict):
        d = iw.get('dir')
        if d:
            return d
    return None


def get_iw_hc_dir_from_today(cache, fid):
    """从缓存中查找今天比赛FID的IW让球方向"""
    if not cache or not fid:
        return None
    for m in cache.get('all_matches', []):
        if str(m.get('FIXTUREID', '')) == str(fid):
            return get_iw_hc_dir(m)
    return None


def fetch_iw_handicap_dir(fid):
    """从500.com让球页抓取IW让球方向（td0=='6'行）"""
    if not fid:
        return None
    import requests
    from bs4 import BeautifulSoup
    url = f'https://odds.500.com/fenxi/rangqiu-{fid}.shtml'
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=h, timeout=10)
        r.encoding = 'gbk'
        sp = BeautifulSoup(r.text, 'html.parser')
        for table in sp.find_all('table'):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                td0 = tds[0].get_text().strip()
                if td0 != '6': continue
                nums = []
                for idx in [4, 5, 6, 7, 8, 9]:
                    val = tds[idx].get_text().strip().replace(chr(160), '')
                    try: nums.append(float(val))
                    except: break
                if len(nums) >= 6:
                    d = ''
                    for a, b in zip(nums[:3], nums[3:6]):
                        if b > a + 0.01: d += '⬆'
                        elif b < a - 0.01: d += '⬇'
                        else: d += '➡'
                    return d
        return None
    except:
        return None


def count_jc_matches(cache):
    """统计缓存中有竞彩官方方向的比赛场次"""
    if not cache:
        return 0
    cnt = 0
    for m in cache.get('all_matches', []):
        oe = m.get('odds_europe')
        if not isinstance(oe, dict):
            continue
        for c in oe.get('companies', []):
            if '官' in c.get('name', '') and c.get('dir'):
                cnt += 1
                break
    return cnt


def get_av_w(m):
    """从缓存中获取百家终赔主胜"""
    if not isinstance(m, dict):
        return None
    oe = m.get('odds_europe')
    if isinstance(oe, dict):
        av = oe.get('av')
        if isinstance(av, dict):
            try:
                return float(av['lw'])
            except:
                pass
    try:
        return float(m['WIN'])
    except:
        return None


def match_hist(cache, target_hc, jc_dir, iw_dir, iw_hc_dir=None, strict_jc=False, av_w_range=None):
    """匹配历史：缺失的数据维度自动降级（不跳过整场比赛）
    
    iw_hc_dir: IW让球方向。不为None时增加IW让球条件。
    strict_jc: 为True时竞彩条件严格匹配（历史无竞彩数据也跳过）
    """
    if not cache:
        return []
    target = round(target_hc, 2)
    res = []
    for m in cache.get('all_matches', []):
        if not isinstance(m, dict):
            continue
        # 统一使用odds_asian澳门亚盘终盘匹配（历史终盘 vs 当天亚盘）
        oa = m.get('odds_asian')
        live_val = None
        if isinstance(oa, list):
            for item in oa:
                if '门' in item.get('name', ''):
                    lp = item.get('live_pan', '').replace('↑','').replace('↓','').replace(' ','').strip()
                    live_val = _match_hc_name(lp)
                    break
                if item == oa[0]:
                    lp = item.get('live_pan', '').replace('↑','').replace('↓','').replace(' ','').strip()
                    live_val = _match_hc_name(lp)
        if live_val is None or abs(live_val - target) > 0.01:
            continue
        # 竞彩条件：有当日值且有历史值时才比较，否则降级跳过
        if jc_dir is not None:
            hist_jc = get_jc_dir(m)
            if strict_jc:
                # 严格模式：历史无数据或不匹配都跳过
                if hist_jc is None or hist_jc != jc_dir:
                    continue
            else:
                # 降级模式：只有历史有数据但不匹配才跳过
                if hist_jc is not None and hist_jc != jc_dir:
                    continue
        # IW条件：同上
        if iw_dir is not None:
            hist_iw = get_iw_dir(m)
            if hist_iw is not None and hist_iw != iw_dir:
                continue
        # IW让球条件（降级兜底时启用）
        if iw_hc_dir is not None:
            hist_iw_hc = get_iw_hc_dir(m)
            if hist_iw_hc is not None and hist_iw_hc != iw_hc_dir:
                continue
        # 百家主胜范围过滤（降级后结果太多时启用）
        if av_w_range is not None:
            hist_av_w = get_av_w(m)
            if hist_av_w is not None:
                lo, hi = av_w_range
                if not (lo <= hist_av_w <= hi):
                    continue
        sc, r = get_score(m)
        # 获取历史比赛的完整4条件值
        hist_h, hist_hn = get_hc(m)
        hist_jc = get_jc_dir(m) if jc_dir is not None else None
        hist_iw = get_iw_dir(m) if iw_dir is not None else None
        # 显示已匹配的条件（含降级原因）
        conds = []
        if jc_dir is not None:
            if hist_jc is not None:
                conds.append(f'竞{hist_jc}')
            else:
                conds.append('竞-缺(500.com无竞彩行)')
        if iw_dir is not None:
            if hist_iw is not None:
                conds.append(f'IW{hist_iw}')
            else:
                conds.append('IW-缺(500.com无IW行)')
        if hist_hn:
            conds.append(f'亚{hist_hn}')
        # 赔率明细（兼容两种缓存格式）
        def fmt_odds(c):
            if not c: return '-', '-'
            # 格式A: init=[w,d,l] live=[w,d,l]
            init_a = c.get('init', [])
            live_a = c.get('live', [])
            if init_a and live_a and len(init_a) >= 3 and len(live_a) >= 3:
                return (f'{init_a[0]:.2f}/{init_a[1]:.2f}/{init_a[2]:.2f}',
                        f'{live_a[0]:.2f}/{live_a[1]:.2f}/{live_a[2]:.2f}')
            # 格式B: iw/id/il lw/ld/ll
            iw, idv, il = c.get('iw'), c.get('id'), c.get('il')
            lw, ld, ll = c.get('lw'), c.get('ld'), c.get('ll')
            if iw is not None:
                return (f'{iw}/{idv}/{il}', f'{lw}/{ld}/{ll}')
            return '-', '-'
        jc_init, jc_live = '-', '-'
        iw_init, iw_live = '-', '-'
        oe = m.get('odds_europe', {})
        if isinstance(oe, dict):
            for c in oe.get('companies', []):
                nm = c.get('name', '')
                if '官' in nm:
                    jc_init, jc_live = fmt_odds(c)
                if nm.startswith('I') and '塞浦路斯' in nm:
                    iw_init, iw_live = fmt_odds(c)
        # 让球数据
        hc_dir = '-'
        hc_init = hc_live = '-'
        oh = m.get('odds_handicap', {})
        if isinstance(oh, dict):
            for hc_key in ['jc', 'iw']:
                hc_data = oh.get(hc_key)
                if hc_data and isinstance(hc_data, dict):
                    d = hc_data.get('dir', '')
                    if d:
                        hc_dir = d
                        init_a = hc_data.get('init', [])
                        live_a = hc_data.get('live', [])
                        if init_a and live_a and len(init_a) >= 3:
                            hc_init = f'{init_a[0]:.2f}/{init_a[1]:.2f}/{init_a[2]:.2f}'
                            hc_live = f'{live_a[0]:.2f}/{live_a[1]:.2f}/{live_a[2]:.2f}'
                        else:
                            iw_v = hc_data.get('iw')
                            if iw_v is not None:
                                hc_init = f'{iw_v}/{hc_data.get("id","?")}/{hc_data.get("il","?")}'
                                hc_live = f'{hc_data.get("lw","?")}/{hc_data.get("ld","?")}/{hc_data.get("ll","?")}'
                        break
        # 亚盘数据（澳门初终盘）
        as_init = as_live = '-'
        oa = m.get('odds_asian')
        if isinstance(oa, list):
            for item in oa:
                if '门' in item.get('name', ''):
                    as_init = item.get('init_pan', '-')
                    as_live = item.get('live_pan', '-')
                    break
                if item == oa[0]:
                    as_init = item.get('init_pan', '-')
                    as_live = item.get('live_pan', '-')
        # 百家初终盘
        av_init = av_live = '-'
        oe_av = oe.get('av') if isinstance(oe, dict) else None
        if isinstance(oe_av, dict):
            if oe_av.get('iw') is not None:
                av_init = f'{oe_av["iw"]}/{oe_av.get("id","?")}/{oe_av.get("il","?")}'
            if oe_av.get('lw') is not None:
                av_live = f'{oe_av["lw"]}/{oe_av.get("ld","?")}/{oe_av.get("ll","?")}'
        res.append({'date': m.get('MATCHDATE', ''), 'home': m.get('HOMETEAMSXNAME', ''),
                    'away': m.get('AWAYTEAMSXNAME', ''), 'score': sc, 'result': r,
                    'conds': '|'.join(conds),
                    'hist_jc': hist_jc or '-', 'hist_iw': hist_iw or '-',
                    'hist_hc_name': hist_hn or '-',
                    'av_init': av_init, 'av_live': av_live,
                    'jc_init': jc_init, 'jc_live': jc_live,
                    'iw_init': iw_init, 'iw_live': iw_live,
                    'hc_dir': hc_dir, 'hc_init': hc_init, 'hc_live': hc_live,
                    'as_init': as_init, 'as_live': as_live})
    return res


def fmt(tm, hist, cache_info, jc_dir, iw_dir, macau_hc_val, macau_hc_name, hc_dir='-', is_fallback=False):
    home = tm.get('home_team', '?')
    away = tm.get('away_team', '?')
    league = tm.get('league_name', '?')
    mode_tag = ' ⬇兜底' if is_fallback else ''
    lines = ['═' * 60,
             f'{home} vs {away} ({league}) FID={tm.get("fid","?")}{mode_tag}',
             f'澳门亚盘: {macau_hc_name}({macau_hc_val})  竞彩盘路:{jc_dir or "-"}  IW盘路:{iw_dir or "-"}  让球:{hc_dir or "-"}',
             f'缓存: {cache_info}']
    if not hist or (len(hist) == 1 and 'error' in hist[0]):
        lines.append(f'⚠️ {hist[0]["error"]}' if hist else '无匹配')
        lines.append('')
        return '\n'.join(lines)

    def parse_odds(s):
        if not s or s == '-': return None
        try: return [float(x) for x in s.split('/')]
        except: return None

    def dir_change(init_str, live_str):
        init = parse_odds(init_str)
        live = parse_odds(live_str)
        if not init or not live: return ''
        d = []
        for i in range(3):
            if live[i] > init[i] + 0.01: d.append('⬆')
            elif live[i] < init[i] - 0.01: d.append('⬇')
            else: d.append('➡')
        return ''.join(d)

    def min_label(live_str):
        odds = parse_odds(live_str)
        if not odds: return '缺'
        idx = odds.index(min(odds))
        return f'{["胜","平","负"][idx]}{min(odds):.2f}'

    def odds_line(label, init_str, live_str):
        """单家公司明细行"""
        d = dir_change(init_str, live_str)
        ml = min_label(live_str)
        if init_str == '-' or not init_str:
            return f'    {label} 终:{live_str}  ←{ml}' if live_str != '-' else ''
        return f'    {label} {d} 初:{init_str} → 终:{live_str}  ←{ml}'

    n = len(hist)
    cnt = Counter()
    for h in hist:
        r = h.get('result', '')
        if '主胜' in r: cnt['主胜'] += 1
        elif '客胜' in r: cnt['客胜'] += 1
        elif '平' in r: cnt['平'] += 1
        else: cnt[r or '未知'] += 1

    lines.append(f'📊 {n}场{"|".join(f"{res}:{c}({c*100//n}%)" for res,c in sorted(cnt.items()))}')
    for h in hist[:30]:
        r = h.get('result', '')
        tag = '✅' if '主胜' in r else ('❌' if '客胜' in r else ('➖' if '平' in r else '❓'))
        lines.append(f'  [{h.get("date","")[:10]}] {h.get("home","")} vs {h.get("away","")}  {h.get("score","-")} {tag}')

        # 百家
        av_i, av_l = h.get('av_init','-'), h.get('av_live','-')
        if av_l != '-':
            lines.append(odds_line('百家', av_i, av_l))
        # 竞彩
        jc_i, jc_l = h.get('jc_init','-'), h.get('jc_live','-')
        if jc_l != '-':
            lines.append(odds_line('竞彩', jc_i, jc_l))
        # IW
        iw_i, iw_l = h.get('iw_init','-'), h.get('iw_live','-')
        if iw_l != '-':
            lines.append(odds_line('IW', iw_i, iw_l))
        # 让球
        hc_d = h.get('hc_dir','-')
        hc_i, hc_l = h.get('hc_init','-'), h.get('hc_live','-')
        if hc_d != '-':
            lines.append(f'    让球方向:{hc_d}  初:{hc_i} → 终:{hc_l}')
        # 亚盘
        as_i = h.get('as_init','-').replace('↑','').replace('↓','').replace(' ','').strip()
        as_l = h.get('as_live','-').replace('↑','').replace('↓','').replace(' ','').strip()
        if as_i != '-':
            lines.append(f'    亚盘 {as_i} → {as_l}')
        lines.append('')

    return '\n'.join(lines)


def main():
    from argparse import ArgumentParser
    p = ArgumentParser(description='竞彩4条件历史匹配')
    p.add_argument('--date', type=str)
    a = p.parse_args()
    td = datetime.strptime(a.date, '%Y-%m-%d').date() if a.date else date.today()
    ds = td.strftime('%Y-%m-%d')
    print(f'📅 {ds}\n')

    ms = get_today_matches(td)
    if not ms:
        print('⚠️ 无比赛')
        sys.exit(1)
    print(f'📋 {len(ms)} 场\n')

    outs = []
    total_hits = 0
    for i, tm in enumerate(ms):
        home = tm.get('home_team', '?')
        away = tm.get('away_team', '?')
        league = tm.get('league_name', '?')
        fid = tm.get('fid', '')
        print(f'[{i + 1}/{len(ms)}] {home} vs {away} FID={fid}...', end=' ')
        sys.stdout.flush()

        # 加载联赛缓存
        cd, ci = None, '无缓存'
        fp = find_cache(league)
        if fp:
            try:
                with open(fp, encoding='utf-8') as f:
                    cd = json.load(f)
                ci = os.path.basename(fp)
            except:
                pass

        # 获取3项条件：澳门亚盘HANDICAPLINE、竞彩盘路、IW盘路
        jc_dir = iw_dir = hc_dir = None
        macau_hc = None
        macau_hc_name = ''
        today_av_w = None

        if cd:
            today_av_w = None
            for m in cd.get('all_matches', []):
                if str(m.get('FIXTUREID', '')) == str(fid):
                    jc_dir = get_jc_dir(m)
                    iw_dir = get_iw_dir(m)
                    hc_dir = get_hc_dir(m)
                    today_av_w = get_av_w(m)
                    # 从odds_asian澳门亚盘终盘取当天亚盘值
                    oa = m.get('odds_asian')
                    if isinstance(oa, list):
                        for item in oa:
                            lp = item.get('init_pan', '').replace('↑','').replace('↓','').replace(' ','').strip()
                            if '门' in item.get('name', '') and lp:
                                macau_hc = _match_hc_name(lp)
                                macau_hc_name = lp
                                break
                            if item == oa[0] and lp:
                                macau_hc = _match_hc_name(lp)
                                macau_hc_name = lp
                                break
                    break

        # 无缓存澳门亚盘 → 实时抓取
        if macau_hc is None:
            macau_hc = fetch_macau_handicap(fid)
            for name, val in _HANDICAP_ITEMS:
                if val == macau_hc:
                    macau_hc_name = name
                    break
            if macau_hc is None:
                macau_hc_name = '未获取到'
            else:
                macau_hc_name = macau_hc_name or str(macau_hc)

        # 无缓存盘路 → 实时抓取
        if jc_dir is None or iw_dir is None:
            jc_dir, iw_dir = fetch_odds_dirs(fid)
            src = '实时'
        else:
            src = '缓存'
        if hc_dir is None:
            hc_dir = fetch_handicap_dir(fid)
        if today_av_w is None:
            today_av_w = fetch_av_w(fid)

        print(f'{src} jc={jc_dir} iw={iw_dir} 让球={hc_dir} 澳门={macau_hc_name}({macau_hc})', end=' ')
        sys.stdout.flush()

        if jc_dir is None and iw_dir is None:
            print('⚠️ 缺盘路')
            outs.append(fmt(tm, [{'error': f'缺盘路 jc={jc_dir} iw={iw_dir} hc={hc_dir}'}],
                           ci, jc_dir, iw_dir, macau_hc, macau_hc_name, hc_dir))
            continue

        if macau_hc is None:
            print('⚠️ 缺澳门亚盘')
            outs.append(fmt(tm, [{'error': '缺澳门亚盘'}],
                           ci, jc_dir, iw_dir, macau_hc, macau_hc_name, hc_dir))
            continue

        # 竞彩密度判断：缓存中竞彩场数 ≤100 则启用降级兜底
        jc_cnt = count_jc_matches(cd)
        use_fallback = (jc_cnt <= 100)
        
        if use_fallback:
            # 竞彩稀疏：先严格匹配，0结果则降级兜底
            used_fallback = False
            hist = match_hist(cd, macau_hc, jc_dir, iw_dir, strict_jc=True)
            valid = [h for h in hist if 'error' not in h]
            if len(valid) == 0 and iw_dir is not None:
                # 降级兜底：IW欧赔+IW让球+亚盘
                iw_hc_dir = get_iw_hc_dir_from_today(cd, fid)
                if iw_hc_dir is None:
                    iw_hc_dir = fetch_iw_handicap_dir(fid)
                if iw_hc_dir is not None:
                    hist = match_hist(cd, macau_hc, None, iw_dir, iw_hc_dir, strict_jc=False)
                    valid = [h for h in hist if 'error' not in h]
                    used_fallback = True
                    # 降级后超过10场 → 加百家主胜范围过滤
                    if len(valid) > 10 and today_av_w is not None:
                        lo = math.floor(today_av_w * 10) / 10
                        hi = round(lo + 0.09, 2)
                        hist2 = match_hist(cd, macau_hc, None, iw_dir, iw_hc_dir, strict_jc=False, av_w_range=(lo, hi))
                        valid2 = [h for h in hist2 if 'error' not in h]
                        if len(valid2) > 0:
                            hist = hist2
                            valid = valid2
                            print(f'[百家{lo:.2f}-{hi:.2f}]', end='')
                    print(f'⬇兜底', end='')
                else:
                    print(f'缺IW让球', end='')
        else:
            # 竞彩充足：严格匹配
            used_fallback = False
            hist = match_hist(cd, macau_hc, jc_dir, iw_dir, strict_jc=True)
            valid = [h for h in hist if 'error' not in h]

        print(f'→ {len(valid)}场')
        if len(valid) > 0:
            total_hits += 1
        outs.append(fmt(tm, hist, ci, jc_dir, iw_dir, macau_hc, macau_hc_name, hc_dir, is_fallback=used_fallback))

    for o in outs:
        print(o)
    print('=' * 60)
    print('📊 汇总')
    print(f'{total_hits}/{len(ms)} 场找到历史匹配（缺竞彩时仅用亚盘+IW）')


if __name__ == '__main__':
    main()
