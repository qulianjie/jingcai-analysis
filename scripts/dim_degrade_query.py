# -*- coding: utf-8 -*-
"""13维降级查询 — 不要求3先决全过，逐维度单独匹配历史缓存"""
import json, sys, os, re, math
from datetime import datetime
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
import odds_consistency as oc

def rk(v):
    try: return math.floor(float(v)*10)/10
    except: return None

def get_tv(fid):
    """复用 fo() 抓当天数据，构造与 sr() 相同的 tv 字典"""
    tod = oc.fo(fid)
    tv = {}
    av = tod.get('av', {}) or {}
    jc = tod.get('jc', {}) or {}
    hc = tod.get('hc', {}) or {}
    hc_iw = tod.get('hc_iw', {}) or {}
    asn = tod.get('as', {}) or {}
    iw_odds = tod.get('iw_odds', {}) or {}
    _hc = hc if hc.get('dir') else hc_iw
    tv['av_dir'] = av.get('dir', '')
    tv['jc_dir'] = jc.get('dir', '')
    tv['iw_dir'] = tod.get('iw_dir', '')
    tv['as_pan'] = asn.get('lp', '')
    tv['hc_dir'] = _hc.get('dir', '')
    if av.get('lw'): tv['av_w'] = rk(av['lw'])
    if av.get('ld'): tv['av_d'] = rk(av['ld'])
    if av.get('ll'): tv['av_l'] = rk(av['ll'])
    if jc.get('lw'): tv['jc_w'] = rk(jc['lw'])
    if jc.get('ld'): tv['jc_d'] = rk(jc['ld'])
    if jc.get('ll'): tv['jc_l'] = rk(jc['ll'])
    _hc_w = hc if hc.get('lw') else hc_iw
    if _hc_w.get('lw'): tv['hc_w'] = rk(_hc_w['lw'])
    _hc_d = hc if hc.get('ld') else hc_iw
    if _hc_d.get('ld'): tv['hc_d'] = rk(_hc_d['ld'])
    _hc_l = hc if hc.get('ll') else hc_iw
    if _hc_l.get('ll'): tv['hc_l'] = rk(_hc_l['ll'])
    if iw_odds.get('lw'): tv['iw_w'] = rk(iw_odds['lw'])
    if iw_odds.get('ld'): tv['iw_d'] = rk(iw_odds['ld'])
    if iw_odds.get('ll'): tv['iw_l'] = rk(iw_odds['ll'])
    return tod, tv

def hist_val(hm, key):
    """从历史缓存比赛提取维度值（与 sr() ext 一致，as_pan 用澳门行优先）"""
    oe = hm.get('odds_europe', {}) or {}
    try:
        if key == 'av_dir':
            cs = oe.get('companies', [])
            return Counter([c.get('dir', '') for c in cs if c.get('dir')]).most_common(1)[0][0] if cs else None
        if key == 'iw_dir':
            return oc._get_iw_dir_companies(oe.get('companies', []))
        if key == 'as_pan':
            oa = hm.get('odds_asian', []) or []
            # 澳门行优先，无澳门行回退第一行（修复 sr() 恒取第一行的bug）
            for item in oa:
                if '门' in item.get('name', ''):
                    return item.get('live_pan')
            return oa[0].get('live_pan') if oa else None
        if key == 'hc_dir':
            oh = hm.get('odds_handicap', {}) or {}
            if oh.get('jc'): return oh['jc'].get('dir')
            if oh.get('iw'): return oh['iw'].get('dir')
            return None
        if key == 'av_w': return rk(oe.get('av', {}).get('lw')) if oe.get('av', {}).get('lw') else None
        if key == 'av_d': return rk(oe.get('av', {}).get('ld')) if oe.get('av', {}).get('ld') else None
        if key == 'av_l': return rk(oe.get('av', {}).get('ll')) if oe.get('av', {}).get('ll') else None
        if key == 'jc_w': return rk(oe.get('jc', {}).get('lw')) if oe.get('jc', {}).get('lw') else None
        if key == 'jc_d': return rk(oe.get('jc', {}).get('ld')) if oe.get('jc', {}).get('ld') else None
        if key == 'jc_l': return rk(oe.get('jc', {}).get('ll')) if oe.get('jc', {}).get('ll') else None
        oh = hm.get('odds_handicap', {}) or {}
        if key == 'hc_w':
            if oh.get('jc', {}).get('lw'): return rk(oh['jc']['lw'])
            if oh.get('iw', {}).get('lw'): return rk(oh['iw']['lw'])
            return None
        if key == 'hc_d':
            if oh.get('jc', {}).get('ld'): return rk(oh['jc']['ld'])
            if oh.get('iw', {}).get('ld'): return rk(oh['iw']['ld'])
            return None
        if key == 'hc_l':
            if oh.get('jc', {}).get('ll'): return rk(oh['jc']['ll'])
            if oh.get('iw', {}).get('ll'): return rk(oh['iw']['ll'])
            return None
        iw = oc._get_iw_odds_companies(oe.get('companies', []))
        if key == 'iw_w': return rk(iw.get('lw')) if iw.get('lw') else None
        if key == 'iw_d': return rk(iw.get('ld')) if iw.get('ld') else None
        if key == 'iw_l': return rk(iw.get('ll')) if iw.get('ll') else None
    except Exception:
        return None
    return None

def main():
    ds = sys.argv[1] if len(sys.argv) > 1 else None
    ml, dt = oc.get_ms(ds)
    if not ml:
        print('未找到比赛数据（先跑 step0）')
        return
    print(f'# 13维降级查询 {dt}\n')
    for m in ml:
        fid = m.get('fid')
        home = m.get('home', '')
        away = m.get('away', '')
        league = m.get('league', '')
        print(f'═ {m.get("matchnum","")} {home} vs {away} ({league}) FID={fid} ═')
        if not fid or str(fid) in ('-1', 'None'):
            print('  ⚠️ FID无效，跳过\n')
            continue
        tod, tv = get_tv(fid)
        hist = oc.ld(league)
        if not hist:
            print('  ⚠️ 无联赛缓存\n')
            continue
        hms = hist.get('matches', [])
        print(f'  缓存: {hist.get("league", league)} ({len(hms)}场)')
        print(f'  当天值: 百{ tv.get("av_dir","-") } IW{ tv.get("iw_dir","-") } 让{ tv.get("hc_dir","-") } 亚盘{ tv.get("as_pan","-") }')
        # 逐维度匹配
        for key, dn in zip(oc.DK, oc.DN):
            tv_v = tv.get(key)
            tag = '【先决】' if key in oc.PREREQ_KEYS else ''
            if tv_v is None or tv_v == '':
                print(f'  {tag}{dn}: 当天无值')
                continue
            cnt = 0
            rc = Counter()
            samples = []
            for hm in hms:
                hv = hist_val(hm, key)
                if hv is not None and hv == tv_v:
                    cnt += 1
                    c = hm.get('_computed', {}) or {}
                    r = c.get('match_result', '')
                    # 归一化: 主胜→胜, 客胜→负, 平局→平
                    if r == '主胜': rn = '胜'
                    elif r == '客胜': rn = '负'
                    elif r == '平局': rn = '平'
                    else: rn = r
                    rc[rn] += 1
                    if len(samples) < 5:
                        samples.append((hm.get('MATCHDATE', ''), hm.get('HOMETEAMSXNAME', ''), hm.get('AWAYTEAMSXNAME', ''), f"{hm.get('HOMESCORE','')}:{hm.get('AWAYSCORE','')}", r))
            if cnt > 0:
                tot = sum(rc.values())
                w, d, l = rc.get('胜', 0), rc.get('平', 0), rc.get('负', 0)
                wr = w / tot * 100 if tot else 0
                smp = '; '.join(f'{d_} {h} {s} {r}' for d_, h, a, s, r in samples[:4])
                print(f'  {tag}{dn}={tv_v}: {cnt}场 (胜{w} 平{d} 负{l} 胜率{wr:.0f}%)')
                if smp: print(f'       例: {smp}')
            else:
                print(f'  {tag}{dn}={tv_v}: 0场')
        print()

if __name__ == '__main__':
    main()
