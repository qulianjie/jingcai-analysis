#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百家欧赔同赔查询 — 同联赛 + 百家欧赔(平均值)胜平负三值完全一致的历史比赛。

用户口径(2026-09-05 定义): "相同联赛百家欧赔胜平负都一样，
一样的意思就是保证小数点后一位一致 不要自己定义"。
→ 匹配精度 = round(x, 1) 一位小数一致(严格全等，不做 ±0.09 范围扩展)。
→ 基准 = 当天百家欧赔**终盘**(av_live, 用户 2026-09-05 纠正 "av是终盘的百家")，
   历史 = 缓存内同联赛场次的百家欧赔终盘(av.lw/ld/ll)。
   初盘仅展示参考。输出每场历史比分 + 胜平负分布统计。

用法:
  python av_same_odds.py --date 2026-09-05            # 跑当天全部场次
  python av_same_odds.py --fid 1364123 --league 挪超  # 单场
输出与 sameodds 风格一致: 场次 header → 百家初/终盘 → 命中列表 → 分布统计。
"""
import sys, os, io, json, time, argparse, math

SD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(SD, 'data', 'league_cache')
TASKS_DIR = os.path.join(SD, 'tasks')

# 复用 min_odds_match 的实时抓取 + 缓存查找(纯函数, 无副作用)
sys.path.insert(0, os.path.join(SD, 'scripts'))
from min_odds_match import fetch_today_odds, find_cache, get_hist_odds

RESULT_MAP = {3: '胜', 1: '平', 0: '负', None: '?'}


def get_hist_av_init(m):
    """历史场次百家欧赔初盘 (win, draw, lost) 或 None"""
    oe = m.get('odds_europe', {})
    if not isinstance(oe, dict):
        return None
    av = oe.get('av')
    if not isinstance(av, dict):
        return None
    if av.get('iw') is None or av.get('id') is None or av.get('il') is None:
        return None
    try:
        return (float(av['iw']), float(av['id']), float(av['il']))
    except Exception:
        return None


def get_hist_av_live(m):
    """历史场次百家欧赔终盘 (win, draw, lost) 或 None"""
    oe = m.get('odds_europe', {})
    if not isinstance(oe, dict):
        return None
    av = oe.get('av')
    if not isinstance(av, dict):
        return None
    if av.get('lw') is None or av.get('ld') is None or av.get('ll') is None:
        return None
    try:
        return (float(av['lw']), float(av['ld']), float(av['ll']))
    except Exception:
        return None


def r1(v):
    """round 到 1 位小数(用户口径: 小数点后一位一致)"""
    return round(float(v), 1)


def same1(a, b):
    """三值一位小数全等"""
    if a is None or b is None:
        return False
    return r1(a[0]) == r1(b[0]) and r1(a[1]) == r1(b[1]) and r1(a[2]) == r1(b[2])


def hist_result(m):
    """历史场次赛果: 胜/平/负。优先 RESULT 字段，退而算比分"""
    res = m.get('RESULT')
    if res in (3, 1, 0):
        return RESULT_MAP[res]
    hs = m.get('HOMESCORE')
    as_ = m.get('AWAYSCORE')
    if hs is None or as_ is None:
        return '?'
    try:
        hs, as_ = int(hs), int(as_)
    except Exception:
        return '?'
    return '胜' if hs > as_ else ('平' if hs == as_ else '负')


def fmt_dir(init, live):
    if not init or not live:
        return '→→→'
    out = ''
    for i in range(3):
        if live[i] > init[i] + 0.005:
            out += '↑'
        elif live[i] < init[i] - 0.005:
            out += '↓'
        else:
            out += '→'
    return out


def query_match(matchnum, home, away, league, fid, out):
    p = lambda s='': print(s, file=out)
    p('=' * 70)
    p('【%s】%s vs %s（%s）FID=%s' % (matchnum, home, away, league, fid))
    p('=' * 70)

    # 实时抓当天百家欧赔(初+终)
    (av_init, av_live), _jc, _iw = fetch_today_odds(fid, None)
    if not av_init and not av_live:
        p('⚠️ 无法获取百家欧赔（ouzhi 页解析失败）')
        p()
        return
    bench_live = av_live or av_init
    bench_init = av_init or av_live
    p('百家终盘：%.2f / %.2f / %.2f' % tuple(bench_live))
    p('百家初盘：%.2f / %.2f / %.2f' % tuple(bench_init))
    p('当前联赛：%s' % league)
    p('匹配口径：百家欧赔**终盘**三值 小数点后一位一致（round 1 位全等，同联赛）')
    p()

    # 找同联赛缓存
    fp = find_cache(league)
    if not fp:
        p('⚠️ 无缓存（%s）' % league)
        p()
        return
    with open(fp, encoding='utf-8') as f:
        cd = json.load(f)
    ml = cd.get('all_matches', [])
    p('缓存: %s (%d场)' % (os.path.basename(fp), len(ml)))
    p()

    # 匹配历史: 终盘 round1 全等 (用户纠正 av=终盘百家)
    hits = []
    for m in ml:
        hl = get_hist_av_live(m)
        if same1(bench_live, hl):
            hi = get_hist_av_init(m)
            hits.append((m, hi, hl))

    if not hits:
        p('【一、相同联赛】0场 — 无百家欧赔终盘一位小数全等的历史比赛')
        p()
        return

    n = len(hits)
    w = sum(1 for _m, _a, _b in hits if hist_result(_m) == '胜')
    d = sum(1 for _m, _a, _b in hits if hist_result(_m) == '平')
    l = sum(1 for _m, _a, _b in hits if hist_result(_m) == '负')
    unk = sum(1 for _m, _a, _b in hits if hist_result(_m) == '?')

    p('【一、相同联赛（%s）】%d场' % (league, n))
    p()
    p('| 日期 | 对阵 | 比分 | 赛果 | 历史百家初盘 | 历史百家终盘 | 盘路 |')
    p('|------|------|------|------|------------|------------|------|')
    for m, hi, hl in hits:
        hs = m.get('HOMESCORE', '?')
        as_ = m.get('AWAYSCORE', '?')
        dirs = fmt_dir(hi, hl) if hl else '→→→'
        hl_s = '%.2f/%.2f/%.2f' % tuple(hl) if hl else '-/-/-'
        p('| %s | %s vs %s | %s:%s | %s | %.2f/%.2f/%.2f | %s | %s |' % (
            m.get('MATCHDATE', '?'), m.get('HOMETEAMSXNAME', '?'), m.get('AWAYTEAMSXNAME', '?'),
            hs, as_, hist_result(m), hi[0], hi[1], hi[2], hl_s, dirs))
    p()
    p('📊 相同联赛统计（%s）：胜%d 平%d 负%d（共%d场），胜率%.1f%%' % (
        league, w, d, l, n, w / (n - unk) * 100 if n > unk else 0.0))
    p()


def main():
    ap = argparse.ArgumentParser(description='百家欧赔同赔查询（同联赛+一位小数全等）')
    ap.add_argument('--date', help='比赛日期 YYYY-MM-DD')
    ap.add_argument('--fid', help='单场 FID')
    ap.add_argument('--league', default='', help='单场联赛名')
    ap.add_argument('--out', help='输出文件路径（默认 stdout）')
    args = ap.parse_args()

    out = open(args.out, 'w', encoding='utf-8') if args.out else sys.stdout

    if args.date:
        md_path = os.path.join(TASKS_DIR, args.date, 'matches_data.json')
        if not os.path.exists(md_path):
            print('⚠️ 未找到 %s——先跑 step0_fetch_matches.py' % md_path, file=sys.stderr)
            sys.exit(1)
        md = json.load(open(md_path, encoding='utf-8'))
        groups = md.get('groups', {})
        n = 0
        for weekday in sorted(groups.keys()):
            for m in groups[weekday].get('matches', []):
                query_match(m.get('matchnum', ''), m.get('home', ''), m.get('away', ''),
                            m.get('league', ''), m.get('fid', ''), out)
                n += 1
                time.sleep(2.0)
        if n == 0:
            print('⚠️ %s 无任何场次（matches_data.json 为空）' % args.date, file=sys.stderr)
    elif args.fid:
        query_match('单场', '', '', args.league, args.fid, out)
    else:
        ap.print_help()
        sys.exit(1)

    if args.out:
        out.close()


if __name__ == '__main__':
    main()
