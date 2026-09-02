#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞彩同赔查询 — 按竞彩官方初赔查 500.com 历史同赔比赛，输出胜平负比分分布。

用法:
  python jc_same_odds.py --date 2026-08-30             # 当天全部场次（读 tasks/{date}/matches_data.json）
  python jc_same_odds.py --fid 1364061 --league 挪超   # 单场（自动抓竞彩官方初赔）
  python jc_same_odds.py --fid 1364061 --league 挪超 --win 1.28 --draw 4.90 --lost 7.00  # 指定初赔

输出与 pipeline step2 一致：竞彩初/终盘 header → 【一、相同联赛】明细+统计 → 【二、所有赛事】明细+统计。
统计列 = 历史同赔比赛的赛果分布（胜/平/负 场数 + 胜率），明细含每场比分。
"""
import sys, os, io, json, time, argparse
import requests
from bs4 import BeautifulSoup

SD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_DIR = os.path.join(SD, 'tasks')

import _http_common
HEADERS = _http_common.headers()
AJAX_H = {'User-Agent': _http_common.UA,
          'Accept': 'application/json, text/javascript, */*; q=0.01',
          'X-Requested-With': 'XMLHttpRequest',
          'Referer': 'https://odds.500.com/fenxi/ouzhi_same.php',
          'Cookie': _http_common.COOKIE}

RESULT = {0: '胜', 1: '平', 2: '负'}


def dir_str(init_vals, live_vals):
    out = ''
    for a, b in zip(init_vals, live_vals):
        if b > a + 0.005:
            out += '↑'
        elif b < a - 0.005:
            out += '↓'
        else:
            out += '→'
    return out


def match_level(bench_dir, hist_dir):
    same = sum(1 for a, b in zip(bench_dir, hist_dir) if a == b)
    if same == 3:
        return '高'
    elif same >= 2:
        return '中'
    return '低'


def same_league(hist_league, cur_league):
    if not hist_league or not cur_league:
        return False
    return hist_league == cur_league or hist_league in cur_league or cur_league in hist_league


def fetch_jc_odds(fid):
    """抓 ouzhi 页 row1=竞彩官方，返回 (init三值, live三值) 或 None"""
    r = requests.get('https://odds.500.com/fenxi/ouzhi-%s.shtml' % fid, headers=HEADERS, timeout=10)
    r.encoding = 'gbk'
    soup = BeautifulSoup(r.text, 'html.parser')
    for table in soup.find_all('table'):
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) < 12:
                continue
            if tds[0].get_text().strip() != '1':
                continue
            nums = []
            for idx in [3, 4, 5, 6, 7, 8]:
                s = tds[idx].get_text().strip().replace(chr(160), '')
                try:
                    nums.append(float(s))
                except Exception:
                    pass
            if len(nums) >= 6:
                return (nums[0], nums[1], nums[2]), (nums[3], nums[4], nums[5])
    return None


def fetch_same_odds(win, draw, lost, fid):
    """500.com 竞彩同赔接口（cid=1 竞彩官方）。返回 {'counts':[胜,平,负], 'match':{lid:联赛名}, 'row':[...]}"""
    url = 'https://odds.500.com/fenxi1/inc/ouzhi_sameajax.php'
    referer = 'https://odds.500.com/fenxi1/ouzhi_same.php?cid=1&win=%s&draw=%s&lost=%s&fixtureid=%s' % (win, draw, lost, fid)
    h = AJAX_H.copy()
    h['Referer'] = referer
    params = {'cid': '1', 'win': win, 'draw': draw, 'lost': lost, 'id': str(fid), 'mid': '0'}
    r = requests.get(url, params=params, headers=h, timeout=15)
    text = r.text.strip()
    if not text:
        # 500.com 对无匹配的赔率组合返回空 body（与 {"counts":[0,0,0]} 等价），非限流/错误
        return {'counts': [0, 0, 0], 'match': {}, 'row': []}
    return r.json()


def query_match(matchnum, home, away, league, fid, out, bench=None):
    p = lambda s='': print(s, file=out)
    p('=' * 70)
    p('【%s】%s vs %s（%s）FID=%s' % (matchnum, home, away, league, fid))
    p('=' * 70)

    if bench is None:
        jc = fetch_jc_odds(fid)
        if jc is None:
            p('⚠️ 无法获取竞彩赔率（ouzhi 页解析失败）')
            p()
            return
        bench = jc
        time.sleep(0.3)
    bench_init, bench_live = bench
    if bench_live is None:
        bench_live = bench_init  # 仅指定初赔时方向显示 →→→
    p('竞彩初盘：%.2f / %.2f / %.2f' % bench_init)
    p('竞彩终盘：%.2f / %.2f / %.2f' % bench_live)
    p('当前联赛：%s' % league)
    p()

    try:
        data = fetch_same_odds('%.2f' % bench_init[0], '%.2f' % bench_init[1], '%.2f' % bench_init[2], fid)
    except Exception as e:
        p('⚠️ 同赔接口请求失败: %s' % e)
        p()
        return

    wins, draws, losses = data.get('counts', [0, 0, 0])
    total = wins + draws + losses
    match_map = data.get('match', {})
    rows = data.get('row', []) or []

    bench_dir = dir_str(bench_init, bench_live)
    parsed = []
    for r in rows:
        lid = str(r[0])
        league_h = match_map.get(lid, lid)
        date = r[3]
        home_h = r[5]
        hs = str(r[6])
        as_ = str(r[7])
        away_h = r[8]
        result = RESULT.get(r[9], '?')
        hist_live = (float(r[10]), float(r[11]), float(r[12]))
        hist_dir = dir_str(bench_init, hist_live)
        ml = match_level(bench_dir, hist_dir)
        parsed.append({'league': league_h, 'date': date, 'home': home_h, 'hs': hs, 'as_': as_,
                       'away': away_h, 'result': result, 'hist_live': hist_live,
                       'hist_dir': hist_dir, 'ml': ml, 'is_same': same_league(league_h, league)})

    same = [x for x in parsed if x['is_same']]
    diff = [x for x in parsed if not x['is_same']]
    level_order = {'高': 0, '中': 1, '低': 2}
    same.sort(key=lambda x: level_order.get(x['ml'], 3))
    diff.sort(key=lambda x: level_order.get(x['ml'], 3))

    def fmt_row(x):
        return '| %s | %s | %s %s:%s %s | %s | %.2f/%.2f/%.2f | %.2f/%.2f/%.2f | %s | %s | %s |' % (
            x['league'], x['date'], x['home'], x['hs'], x['as_'], x['away'], x['result'],
            bench_init[0], bench_init[1], bench_init[2],
            x['hist_live'][0], x['hist_live'][1], x['hist_live'][2],
            x['hist_dir'], x['ml'], '同联赛' if x['is_same'] else '')

    if same:
        n = len(same)
        w = sum(1 for x in same if x['result'] == '胜')
        d = sum(1 for x in same if x['result'] == '平')
        l = sum(1 for x in same if x['result'] == '负')
        p('【一、相同联赛（%s）】%d场' % (league, n))
        p()
        p('| 赛事 | 日期 | 对阵 | 赛果 | 初盘 | 终盘 | 盘路 | 匹配度 | 联赛 |')
        p('|------|------|------|------|------|------|------|--------|------|')
        for x in same:
            p(fmt_row(x))
        p()
        p('📊 相同联赛统计（%s）：胜%d 平%d 负%d（共%d场），胜率%.1f%%' % (league, w, d, l, n, w / n * 100 if n else 0))
        p()
        p('=' * 70)
        p()

    p('【二、所有赛事】%d场' % total)
    p()
    p('| 赛事 | 日期 | 对阵 | 赛果 | 初盘 | 终盘 | 盘路 | 匹配度 | 联赛 |')
    p('|------|------|------|------|------|------|------|--------|------|')
    for x in same:
        p(fmt_row(x))
    for x in diff:
        p(fmt_row(x))
    if total == 0:
        p('（无历史同赔比赛）')
    p()
    p('📊 所有赛事统计：胜%d 平%d 负%d（共%d场），胜率%.1f%%' % (wins, draws, losses, total, wins / total * 100 if total else 0))
    p()


def main():
    ap = argparse.ArgumentParser(description='竞彩同赔比赛胜平负比分查询')
    ap.add_argument('--date', help='比赛日期 YYYY-MM-DD，读 tasks/{date}/matches_data.json 跑全部场次')
    ap.add_argument('--fid', help='单场 FID')
    ap.add_argument('--league', default='', help='单场联赛名')
    ap.add_argument('--win', type=float, help='竞彩初赔主胜（与 --fid 搭配，跳过页面抓取）')
    ap.add_argument('--draw', type=float, help='竞彩初赔平局')
    ap.add_argument('--lost', type=float, help='竞彩初赔客胜')
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
                time.sleep(0.5)
        if n == 0:
            print('⚠️ %s 无任何场次（matches_data.json 为空）' % args.date, file=sys.stderr)
    elif args.fid:
        bench = None
        if args.win is not None and args.draw is not None and args.lost is not None:
            bench = ((args.win, args.draw, args.lost), None)
        query_match('单场', '', '', args.league, args.fid, out, bench=bench, mid=args.mid if hasattr(args, 'mid') else None)
    else:
        ap.print_help()
        sys.exit(1)

    if args.out:
        out.close()


if __name__ == '__main__':
    main()
