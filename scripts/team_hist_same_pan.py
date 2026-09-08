#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
team_hist_same_pan.py — 当天比赛 主/客场队 同终盘亚盘（澳门优先威廉希尔保底）历史统计

对当天每场比赛：
  主队线：缓存中该队作为【主队】(HOMETEAMSXNAME) 且 亚盘终盘（澳门优先威廉希尔保底）== 当天盘口 的历史比赛
  客队线：缓存中该队作为【客队】(AWAYTEAMSXNAME) 且 亚盘终盘（澳门优先威廉希尔保底）== 当天盘口 的历史比赛
输出：赛果分布汇总 + 逐场比分串（✅❌➖）

匹配口径（用户确认 2026-08-15）：
  - 亚盘数值 ±0.01 精确匹配（非盘口名子串）
  - 全量历史（不限最近N场）
  - 同联赛缓存
  - 输出：汇总分布 + 比分串（4way 风格）
"""
import json
import time
import os
import re
import sys
import _http_common
import okooo_api
import glob

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'league_cache')

ALIAS = {
    '韩职': 'K1联赛', 'K1联赛': '韩职',
    '美职足': '美职联', '美职联': '美职足',
    '英联赛杯': '英联杯', '英联杯': '英联赛杯',
}

_HANDICAP_ITEMS = sorted([
    ('受三球半', 3.5), ('受三球', 3.0), ('受两球半/三球', 2.75), ('受两球半', 2.5),
    ('受两球/两球半', 2.25), ('受两球', 2.0), ('受球半/两球', 1.75), ('受球半', 1.5),
    ('受一球/球半', 1.25), ('受一球', 1.0), ('受半球/一球', 0.75), ('受半球', 0.5),
    ('受平手/半球', 0.25), ('平手', 0.0),
    ('平手/半球', -0.25), ('平半', -0.25), ('半球', -0.5),
    ('半球/一球', -0.75), ('一球', -1.0), ('一球/球半', -1.25), ('球半', -1.5),
    ('球半/两球', -1.75), ('两球', -2.0), ('两球/两球半', -2.25), ('两球半', -2.5),
    ('两球半/三球', -2.75), ('三球', -3.0), ('三球/三球半', -3.25), ('三球半', -3.5),
], key=lambda x: -len(x[0]))


def _match_hc_name(txt):
    if not txt:
        return None
    txt = txt.replace('\xa0', '').replace('↑', '').replace('↓', '').strip()
    for name, val in _HANDICAP_ITEMS:
        if name in txt:
            return val
    try:
        return float(txt)
    except Exception:
        return None


def find_cache(league):
    league = ALIAS.get(league, league)
    candidates = []
    for fn in glob.glob(os.path.join(CACHE_DIR, '*.json')):
        base = os.path.basename(fn)[:-5]
        if base == league:
            score = 100
        elif base.startswith(league):
            score = 50
        elif league in base:
            score = 10
        else:
            continue
        try:
            with open(fn, encoding='utf-8') as f:
                d = json.load(f)
            cnt = len(d.get('all_matches', []))
            if d.get('enriched'):
                score += 1000
            score += cnt * 0.5
        except Exception:
            cnt = 0
        candidates.append((score, cnt, fn))
    if not candidates:
        return None, 0
    candidates.sort(key=lambda x: -x[0])
    return candidates[0][2], candidates[0][1]


def get_macau_live_val(m):
    oa = m.get('odds_asian')
    if not isinstance(oa, list) or not oa:
        return None
    for item in oa:
        if '门' in item.get('name', ''):
            return _match_hc_name(item.get('live_pan', ''))
        if '威' in item.get('name', ''):
            return _match_hc_name(item.get('live_pan', ''))
    return _match_hc_name(oa[0].get('live_pan', ''))


# 队名译名映射（matches_data trade短名 → 500.com缓存名）
TEAM_ALIAS = {
    '基尔': '荷尔斯泰因', '不伦瑞克': '布伦瑞克', '埃夫斯堡': '埃尔夫斯堡',
    '韦斯特罗斯': '瓦斯特拉斯', '达曼协定': '达曼协作', '哈马赫费萨利': '费萨里',
    '新未来SC': '新未来城体育', '鹿斯巴达': '鹿特丹斯巴达', '赫拉克勒': '赫拉克勒斯',
    '登博思': '邓伯什', '阿纳西': '昂纳西', '里斯本': '葡萄牙体育',
    '瓦萨': 'VPS瓦萨', 'TPS图尔': 'TPS图尔库',
    '秋田闪电': '秋田蓝闪电',
    # 2026-08-15 日韩/欧洲队名模糊搜索修复
    '首尔FC': 'FC首尔', '东京FC': 'FC东京', '浦项制铁': '浦项铁人',
    '赛哈特海湾': '塞哈特海湾', '奥斯KFUM': 'KFUM奥斯陆',
    '阿尔维卡': '艾华卡', '塞伊奈': '塞那乔其',
    '帕梅拉斯': '帕尔梅拉斯', '穆拜赖兹征服': '哈萨征服',
    '赫塔费': '赫塔菲',
    # 2026-08-16 samepan ERR 译名变体修复
    '鸟栖沙岩': '鸟栖砂岩', '布鲁马波': '布洛马波卡纳', '厄格里特': '奥尔格里特',
    '佐加顿斯': '尤尔加登', '国际图尔': '图尔库国际', '葡国民': '马德拉国民',
    '桑纳菲': '桑德菲杰', '摩雷伦斯': '莫雷拉人', '吉维森特': '吉尔维森特',
    # 2026-08-17 samepan ERR 译名变体修复
    '里莫': '雷莫', '哈尔姆斯': '哈姆斯塔德', '加的夫城': '卡迪夫城',
    '雷克斯': '雷克瑟姆', '卡萨皮亚': '卡萨比亚',
    # 2026-08-18 samepan ERR 译名变体修复
    '里瓦达维亚独立': '门多萨独立', '索列夫': '索非亚列夫斯基',
    '萨迪纳摩': '萨格勒布迪纳摩',
    # 2026-08-20 samepan ERR 译名变体修复
    '迈季迈阿宽广': '费哈', '贝红星': '贝尔格莱德红星',
    # 2026-08-21 samepan ERR 译名变体修复
    '长崎航海': '长崎成功丸', '胡巴尔卡德西亚': '胡拜尔库迪西亚',
    '埃因FC': 'FC埃因霍温',
    # 2026-08-23 samepan ERR 译名变体修复
    # 2026-08-26 samepan ERR 译名变体修复
    '蔚山现代': '蔚山HD',
    '弗洛西诺': '弗罗西诺内',
    # 2026-08-23 samepan ERR 译名变体修复(2)
    '盖斯': '哥德堡盖斯',
    # 2026-08-24 samepan ERR 译名变体修复
    '巴竞技': '巴拉纳竞技',
    # 2026-08-25 samepan ERR 译名变体修复
    '巴伦西亚': '瓦伦西亚',
    # 2026-08-27 samepan ERR 译名变体修复
    '阿拉木图': '凯拉特',
    # 2026-08-28 samepan ERR 译名变体修复
    '巴黎圣曼': '巴黎圣日耳曼',
    # 2026-08-29 samepan ERR 译名变体修复
    '清水鼓动': '清水心跳',
    '大宫松鼠RB': 'RB大宫松鼠',
    '湘南海洋': '湘南丽海',
    '卡斯鲁厄': '卡尔斯鲁厄',
    '沃夫斯堡': '沃尔夫斯堡',
    '伍尔弗汉普顿': '狼队',
    '埃沃斯堡': '艾禾斯堡',
    '莱红牛': 'RB莱比锡',
    # 2026-08-30 samepan ERR 译名变体修复
    '不来梅': '云达不莱梅',
    '国际米兰': '国米',
    # 2026-09-08 samepan ERR 译名变体修复
    '南安普敦': '南安普顿',
    '维拉': '阿斯顿维拉',
    'LASK林茨': '林茨',
}


def _fc_swap(name):
    """FC 前后颠倒变体：首尔FC <-> FC首尔；返回候选名列表"""
    cands = []
    up = name.upper()
    if up.endswith('FC') and len(name) > 2:
        cands.append('FC' + name[:-2])
    if up.startswith('FC') and len(name) > 2:
        cands.append(name[2:] + 'FC')
    return cands


def fuzzy_team(name, cache_names):
    """队名模糊匹配：精确 → 别名 → FC颠倒 → 子串；返回匹配到的缓存名或 None"""
    if not name:
        return None
    if name in cache_names:
        return name
    alias = TEAM_ALIAS.get(name)
    if alias and alias in cache_names:
        return alias
    for cand in _fc_swap(name):
        if cand in cache_names:
            return cand
    for cn in cache_names:
        # 前缀/后缀匹配（防中间子串误匹配：维京→戈塔维京人、里昂→洛里昂）
        if name and cn and (cn.startswith(name) or name.startswith(cn)):
            return cn
    return None


def _fetch_yazhi_company_hc(fid, kw):
    if not fid:
        return None
    import requests
    from bs4 import BeautifulSoup
    url = f'https://odds.500.com/fenxi/yazhi-{fid}.shtml'
    h = _http_common.headers()
    try:
        r = requests.get(url, headers=h, timeout=10)
        r.encoding = 'gbk'
        sp = BeautifulSoup(r.text, 'html.parser')
        for t in sp.find_all('table'):
            for tr in t.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) < 6:
                    continue
                nm = tds[0].get_text().strip()
                if kw not in nm:
                    nm = tds[1].get_text().strip() if len(tds) > 1 else ''
                if kw not in nm:
                    continue
                for idx in [2, 8]:
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
                            except Exception:
                                continue
                continue
    except Exception:
        return None
    return None



def fetch_asian_handicap(fid, mid=None):
    """抓取当天亚盘：澳客威廉希尔优先, 500.com兜底。返回 (数值, 公司标签)"""
    if mid:
        v, ip, lp, comp = okooo_api.fetch_asian_hc(mid)
        if v is not None:
            return v, comp
    for kw, label in [('门', '澳门'), ('威', '威廉希尔')]:
        v = _fetch_yazhi_company_hc(fid, kw)
        if v is not None:
            return v, label
    return None, ''


def fetch_macau_handicap(fid):
    """兼容旧调用：返回亚盘数值（澳门优先，威廉希尔保底）"""
    v, _ = fetch_asian_handicap(fid)
    return v
def pan_name(val):
    """数值 → 盘口名（与4way一致：半球(-0.5)/受半球(0.5)/平手(0.0)）"""
    if val is None:
        return '?'
    for name, v in _HANDICAP_ITEMS:
        if abs(v - val) < 0.001:
            return f'{name}({val:+.2f})'.replace('+0.00', '0.0').replace('+', '')
    return f'{val:.2f}' 


def get_result(m):
    res = None
    comp = m.get('_computed')
    if isinstance(comp, dict):
        res = comp.get('match_result')
    if res:
        return res
    hs, as_ = m.get('HOMESCORE'), m.get('AWAYSCORE')
    if hs is None or as_ is None:
        return None
    return '主胜' if int(hs) > int(as_) else ('平局' if int(hs) == int(as_) else '客胜')


def get_macau_pan_str(m):
    """亚盘 初盘→终盘 文本（如 平手→半球 升）"""
    oa = m.get('odds_asian')
    if not isinstance(oa, list) or not oa:
        return ''
    item = None
    for x in oa:
        if '门' in x.get('name', ''):
            item = x
            break
        if '威' in x.get('name', ''):
            item = x
            break
    if item is None:
        item = oa[0]
    init_p = (item.get('init_pan') or '').replace('↑', '').replace('↓', '').strip()
    live_p = (item.get('live_pan') or '').replace('↑', '').replace('↓', '').strip()
    if not init_p and not live_p:
        return ''
    if init_p == live_p:
        return f'亚盘 {init_p}'
    return f'亚盘 {init_p}→{live_p}'


def fmt_score(m):
    hs, as_ = m.get('HOMESCORE'), m.get('AWAYSCORE')
    if hs is None or as_ is None:
        return None
    res = get_result(m)
    mark = '✅' if res == '主胜' else ('➖' if res == '平局' else '❌')
    date = str(m.get('MATCHDATE', m.get('VSDATE', '')))[:10]
    home = m.get('HOMETEAMSXNAME', '?')
    away = m.get('AWAYTEAMSXNAME', '?')
    pan = get_macau_pan_str(m)
    return f"  [{date}] {home} vs {away}  {int(hs)}:{int(as_)} {mark}  {pan}"


def summarize(hits):
    n = len(hits)
    if n == 0:
        return '0场'
    wins = draws = losses = 0
    for m in hits:
        r = get_result(m)
        if r == '主胜':
            wins += 1
        elif r == '平局':
            draws += 1
        elif r == '客胜':
            losses += 1
    return f'{n}场 主胜{wins} 平{draws} 客胜{losses}'


def main():
    date = None
    out_path = None
    range_str = ''
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == '--date' and i + 1 < len(args):
            date = args[i + 1]
        elif a == '--out' and i + 1 < len(args):
            out_path = args[i + 1]
        elif a == '--range' and i + 1 < len(args):
            range_str = args[i + 1]
    if not date:
        from datetime import datetime
        date = datetime.now().strftime('%Y-%m-%d')

    md_path = os.path.join('tasks', date, 'matches_data.json')
    if not os.path.exists(md_path):
        print(f'[ERR] 未找到 {md_path}，请先跑 step0_fetch_matches.py')
        sys.exit(1)
    with open(md_path, encoding='utf-8') as f:
        md = json.load(f)

    matches = []
    for wk, g in md.get('groups', {}).items():
        for m in g.get('matches', []):
            matches.append(m)

    # --range 过滤（序号=输出顺序=单售卖日竞彩场次尾号）
    lo = hi = None
    if range_str:
        import re as _re
        rm = _re.match(r'^\s*(\d+)\s*-\s*(\d+)\s*$', range_str)
        if not rm:
            print('[ERR] --range 格式应为 001-005')
            sys.exit(2)
        lo, hi = int(rm.group(1)), int(rm.group(2))
    sel = [(i, m) for i, m in enumerate(matches, 1) if lo is None or lo <= i <= hi]
    if not sel:
        print('[ERR] 范围内无场次')
        sys.exit(1)

    print(f'[DATE] {date}  共 {len(matches)} 场' + (f'（范围 {range_str} → 跑 {len(sel)} 场）' if range_str else ''))
    print()

    lines = []
    for i, m in sel:
        num = m.get('matchnum', f'{i}')
        home = m.get('home', '?')
        away = m.get('away', '?')
        league = m.get('league', '?')
        fid = m.get('fid', '')

        mid = None  # 澳客已弃用(2026-09-02)
        time.sleep(2)  # 2026-09-02 降速防EdgeOne suspend
        hc, asian_comp = fetch_asian_handicap(fid, mid)
        if hc is None:
            lines.append(f'[{num}] {home} vs {away} ({league}) FID={fid} mid={mid} [ERR] 亚盘获取失败')
            lines.append('')
            continue

        cache_path, cache_cnt = find_cache(league)
        if not cache_path or cache_cnt == 0:
            lines.append(f'[{num}] {home} vs {away} ({league}) {asian_comp}={pan_name(hc)} [ERR] 无缓存({league})')
            lines.append('')
            continue

        with open(cache_path, encoding='utf-8') as f:
            cd = json.load(f)
        allm = cd.get('all_matches', [])
        cache_names = set()
        for x in allm:
            cache_names.add(x.get('HOMETEAMSXNAME', ''))
            cache_names.add(x.get('AWAYTEAMSXNAME', ''))
        cache_names.discard('')

        home_cn = fuzzy_team(home, cache_names)
        away_cn = fuzzy_team(away, cache_names)

        def _sort_key(x):
            d = str(x.get('MATCHDATE', x.get('VSDATE', '')))[:10]
            return d

        home_hits = []
        away_hits = []
        for x in allm:
            hc_x = get_macau_live_val(x)
            if hc_x is None or abs(hc_x - hc) > 0.01:
                continue
            if home_cn and x.get('HOMETEAMSXNAME', '') == home_cn:
                home_hits.append(x)
            if away_cn and x.get('AWAYTEAMSXNAME', '') == away_cn:
                away_hits.append(x)
        home_hits.sort(key=_sort_key)  # 2026-08-21 正序
        away_hits.sort(key=_sort_key)  # 2026-08-21 正序

        lines.append(f'[{num}] {home} vs {away} ({league}) {asian_comp}终盘={pan_name(hc)}')
        lines.append(f'  缓存: {os.path.basename(cache_path)} ({cache_cnt}场)')
        if home_cn:
            lines.append(f'  主队 {home}->{home_cn} (主场+同盘) {summarize(home_hits)}')
            for x in home_hits:
                s = fmt_score(x)
                if s:
                    lines.append(s)
        else:
            lines.append(f'  主队 {home} [ERR] 缓存无此队名')
        if away_cn:
            lines.append(f'  客队 {away}->{away_cn} (客场+同盘) {summarize(away_hits)}')
            for x in away_hits:
                s = fmt_score(x)
                if s:
                    lines.append(s)
        else:
            lines.append(f'  客队 {away} [ERR] 缓存无此队名')
        lines.append('')

    out = '\n'.join(lines)
    print(out)
    if out_path:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(out + '\n')
        print(f'[FILE] {out_path}')


if __name__ == '__main__':
    main()
