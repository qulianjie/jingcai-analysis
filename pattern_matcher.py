# -*- coding: utf-8 -*-
"""
竞彩模式匹配器 V2 - 跑完当天比赛后调用
"""

import os, sys, json, re, glob
from datetime import datetime
from collections import defaultdict

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _util import rd, safe_json_load, ensure_utf8_stdout
    ensure_utf8_stdout()
except ImportError:
    def rd(path):
        try: return open(path, 'r', encoding='utf-8').read()
        except: return ''

# 增强特征抽取：补充赔率衍生+盘路+方向维度（使4D模式可命中）
try:
    from _enhance_features import enhance_features
    HAS_ENHANCED = True
except ImportError:
    HAS_ENHANCED = False
    def enhance_features(md, feat): return feat

# 增强特征抽取：补充赔率衍生+盘路+方向维度（使4D模式可命中）
try:
    from _enhance_features import enhance_features
    HAS_ENHANCED = True
except ImportError:
    HAS_ENHANCED = False
    def enhance_features(md, feat): return feat

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PATTERNS_FILE = os.path.join(SCRIPT_DIR, 'learnings', 'historical_patterns.json')
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')


def extract_match_features(date, match_num, match_dir):
    feat = {}
    meta_file = os.path.join(match_dir, 'meta.json')
    if os.path.exists(meta_file):
        try:
            meta = json.loads(rd(meta_file))
            league = meta.get('league', '')
            if league: feat['联赛'] = league
            macau_line = meta.get('macau_line', '')
            if macau_line:
                feat['澳门亚盘'] = macau_line
        except: pass
    s25_file = os.path.join(match_dir, 'step25_zhuangjia.json')
    if os.path.exists(s25_file):
        try:
            s25 = json.loads(rd(s25_file))
            data = s25.get('data', s25)
            labels = s25.get('labels', {})
            for r in ['主胜', '平局', '客胜']:
                if r in data:
                    pd = data[r].get('profit_dir', None)
                    if pd is True: feat['庄家' + r + '盈亏'] = '赢'
                    elif pd is False: feat['庄家' + r + '盈亏'] = '亏'
            ratios = []
            for r, s in [('主胜', '主'), ('平局', '平'), ('客胜', '客')]:
                bp = data.get(r, {}).get('bet_pct', '0')
                try:
                    v = float(str(bp).replace('%', ''))
                    if v >= 45: bucket = '高'
                    elif v >= 30: bucket = '中'
                    else: bucket = '低'
                    feat['投注占比_' + s] = bucket
                    ratios.append(bucket)
                except: ratios.append('')
            if len(ratios) == 3 and '' not in ratios:
                feat['投注占比三段'] = '/'.join(ratios)
            for key in ['主胜', '平局', '客胜']:
                if key in labels:
                    bp_label = labels[key].get('bet_pct', '')
                    if bp_label == '多':
                        feat['大热方'] = key
                        break
        except: pass
    s26_file = os.path.join(match_dir, 'step26_profit_ratio.json')
    if os.path.exists(s26_file):
        try:
            s26 = json.loads(rd(s26_file))
            analysis = s26.get('analysis', {})
            profit_ratio = analysis.get('盈亏占比', {})
            for r in ['主', '平', '客']:
                v = profit_ratio.get(r, 0)
                try:
                    vf = float(v)
                    if vf >= 0.4: feat['盈亏占比_' + r] = '高'
                    elif vf >= 0.2: feat['盈亏占比_' + r] = '中'
                    else: feat['盈亏占比_' + r] = '低'
                except: pass
            if analysis.get('庄家最看好'):
                feat['综合盈亏方向'] = analysis['庄家最看好']
        except: pass
    # 增强特征抽取
    if HAS_ENHANCED:
        enhance_features(match_dir, feat)
    return feat


def find_today_matches(date_str=None):
    all_dates = []
    if date_str:
        dd = os.path.join(TASKS_DIR, date_str)
        if not os.path.isdir(dd):
            return None, []
        all_dates = [date_str]
    else:
        dl = [d for d in os.listdir(TASKS_DIR)
              if os.path.isdir(os.path.join(TASKS_DIR, d)) and d.startswith('2026-')]
        all_dates = sorted(dl, reverse=True)[:3]
    matches = []
    seen_nums = set()
    for d in all_dates:
        date_dir = os.path.join(TASKS_DIR, d)
        data_dir = os.path.join(date_dir, 'data')
        base = data_dir if os.path.isdir(data_dir) else date_dir
        for sub in sorted(os.listdir(base)):
            sub_path = os.path.join(base, sub)
            if not os.path.isdir(sub_path) or not sub.startswith('match'):
                continue
            meta_file = os.path.join(sub_path, 'meta.json')
            if not os.path.exists(meta_file):
                continue
            try:
                meta = json.loads(rd(meta_file))
                mn = meta.get('matchnum', sub)
                if mn in seen_nums:
                    continue
                seen_nums.add(mn)
                matches.append({
                    'date': d, 'match_num': mn, 'dir': sub_path,
                    'home': meta.get('home', ''),
                    'away': meta.get('away', ''),
                    'league': meta.get('league', ''),
                    'macau_line': meta.get('macau_line', ''),
                })
            except: pass
    return all_dates, matches


def match_patterns(matches, patterns, min_lift=1.5, sequences=None):
    if sequences is None:
        sequences = {}
    report_items = []
    for m in matches:
        feat = extract_match_features(m['date'], m['match_num'], m['dir'])
        if not feat:
            continue
        league = feat.get('联赛', '')
        hits = []
        cycle_hits = []  # hits that also have periodicity signal
        for p in patterns:
            if p['lift'] < min_lift:
                continue
            match_all = True
            for k, v in p['combo'].items():
                if feat.get(k) != v:
                    match_all = False
                    break
            if match_all:
                hits.append(p)
                # Check if any dim of this pattern has periodicity in this league
                p_cycle = None
                for k, v in p['combo'].items():
                    group_key = '%s|%s=%s' % (league, k, v)
                    seq_entry = sequences.get(group_key, {})
                    period_info = seq_entry.get('period', {})
                    if period_info.get('found'):
                        if p_cycle is None or period_info.get('confidence', 0) > p_cycle.get('confidence', 0):
                            p_cycle = {
                                'period': period_info['period'],
                                'pattern': period_info['pattern'],
                                'next': period_info['next'],
                                'match_rate': period_info.get('match_rate', 0),
                                'total_cycles': period_info.get('total_cycles', 0),
                                'confidence': period_info.get('confidence', 0),
                                'sequence_length': seq_entry.get('length', 0),
                                'recent': ' '.join(seq_entry.get('sequence', [])[-10:]),
                                'dimension': k,
                                'value': v,
                            }
                if p_cycle:
                    cycle_hits.append({'pattern': p, 'cycle': p_cycle})
        if hits:
            hits.sort(key=lambda x: -x['lift'])
            report_items.append({
                'match_num': m['match_num'],
                'home': m.get('home', ''),
                'away': m.get('away', ''),
                'league': league,
                'date': m['date'],
                'hits': hits[:10],
                'total_hits': len(hits),
                'features': feat,
                'cycle_hits': cycle_hits[:5],
            })
    return report_items


def print_report(report, date_label):
    if not report:
        print('\n' + '='*60)
        print('模式匹配报告 - %s' % date_label)
        print('='*60)
        print('没有匹配到历史模式')
        return
    scored_report = []
    for r in report:
        by_result = {}
        for h in r['hits']:
            result = h['result']
            if result not in by_result: by_result[result] = []
            by_result[result].append(h)
        scores = {}
        for result, hlist in by_result.items():
                        # 维度权重: 2维=1.3, 3维=1.7, 4维=2.5, 5维=3.0, 6维=4.0
            def _dim_weight(dn):
                w = {2:1.3, 3:1.7, 4:2.5, 5:3.0, 6:4.0}
                return w.get(dn, 1.0)
            scores[result] = sum(h['lift'] * h['correct'] * h['pct'] * _dim_weight(h.get('dim_n', 1)) for h in hlist[:3])
        # 高维优先：有3+维就全留，没有才兜底2维
        has_3plus = any(h.get('dim_n', 1) >= 3 for hlist in by_result.values() for h in hlist)
        if has_3plus:
            filtered = {}
            for res, hlist in by_result.items():
                fh = [h for h in hlist if h.get('dim_n', 1) >= 3]
                if fh:
                    filtered[res] = fh
            if filtered:
                by_result = filtered
                # 重算scores（维度权重仍生效）
                scores = {}
                for result, hlist in by_result.items():
                    scores[result] = sum(h['lift'] * h['correct'] * h['pct'] * _dim_weight(h.get('dim_n', 1)) for h in hlist[:3])
        sr = sorted(scores.items(), key=lambda x: -x[1])
        top = sr[0][1]
        sec = sr[1][1] if len(sr) >= 2 else 0
        dom = top / sec if sec > 0 else 99
        scored_report.append((dom, scores, sr, by_result, r))
    scored_report.sort(key=lambda x: -x[0])
    print('\n' + '='*60)
    print('模式匹配报告 - %s' % date_label)
    print('='*60)
    for dom, scores, sr, by_result, r in scored_report:
        if dom >= 3.0: c = '🔥'
        elif dom >= 2.0: c = '💡'
        elif dom >= 1.5: c = '⚡'
        else: c = '❓'
        label = '%s %s' % (r['match_num'], r.get('home', '') + ' vs ' + r.get('away', ''))
        print('\n%s %s' % (c, label))
        cyc_info = ''
        if r.get('cycle_hits'):
            cyc_list = []
            for ch in r['cycle_hits'][:3]:
                cy = ch['cycle']
                cyc_list.append('%s=%s 🔄周期%d→%s(%.0f%%)' % (cy['dimension'], cy['value'], cy['period'], cy['next'], cy['match_rate']*100))
            cyc_info = ' | ' + ' '.join(cyc_list)
        print('   联赛: %s | 命中: %d模式%s' % (r.get('league', '?'), r['total_hits'], cyc_info))
        for result, _ in sr:
            hlist = by_result[result]
            # 高维优先显示（同分时lift高的靠前）
            _dw = {2:1.3, 3:1.7, 4:2.5, 5:3.0, 6:4.0}
            hlist.sort(key=lambda h: (_dw.get(h.get('dim_n',1),1.0) * h['lift'] * h['pct'], h['lift']), reverse=True)
            best = hlist[0]
            dim_n = best.get('dim_n', len(best['combo']))
            combo = '[%d维] ' % dim_n + ' / '.join('%s=%s' % (k, v) for k, v in sorted(best['combo'].items()))
            m = '▶' if result == sr[0][0] else ' '
            # Check if this result direction matches any cycle prediction
            cycle_marker = ''
            if r.get('cycle_hits'):
                for ch in r['cycle_hits']:
                    if ch['cycle']['next'] == result:
                        cy = ch['cycle']
                        cycle_marker = ' 🔄周期%d(%d场)' % (cy['period'], cy['sequence_length'])
                        break
            # 4维以上且非100%时标注剩余场次的其他赛果
            other_mark = ''
            dim_n = best.get('dim_n', 1)
            if dim_n >= 4 and best['pct'] < 1.0 and best.get('outcomes'):
                others = {k: v for k, v in best['outcomes'].items() if k != best['result']}
                if others:
                    parts = []
                    for k, v in sorted(others.items(), key=lambda x: -x[1]):
                        k_label = {'胜':'胜','平':'平','负':'负'}.get(k, k)
                        parts.append('%s%d' % (k_label, v))
                    if parts:
                        other_mark = '(另:%s)' % ''.join(parts)
            print('  %s %s  %.0f%% (x%.1f, %d/%d)%s %s%s' % (m, result, best['pct']*100, best['lift'], best['correct'], best['total'], cycle_marker, combo[:50], other_mark))
            if len(hlist) > 1:
                for h in hlist[1:5]:
                    dim_n = h.get('dim_n', len(h['combo']))
                    cs = '[%d维] ' % dim_n + ' / '.join('%s=%s' % (k, v) for k, v in sorted(h['combo'].items()))
                    print('    + %s (%.0f%%, %d场)' % (cs, h['pct']*100, h['total']))
    print('\n' + '-'*60)
    s = sum(1 for d,_,_,_,_ in scored_report if d>=3)
    c = sum(1 for d,_,_,_,_ in scored_report if 2<=d<3)
    l = sum(1 for d,_,_,_,_ in scored_report if 1.5<=d<2)
    u = sum(1 for d,_,_,_,_ in scored_report if d<1.5)
    print('🔥%d 💡%d ⚡%d ❓%d | 共%d场命中' % (s, c, l, u, len(report)))


def main():
    print('竞彩模式匹配器 V2')
    print('数据时间: %s' % datetime.now().strftime('%Y-%m-%d %H:%M'))
    print('')
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if not os.path.exists(PATTERNS_FILE):
        print('ERROR: 模式库不存在')
        return
    pl = json.loads(rd(PATTERNS_FILE))
    raw_patterns = pl.get('patterns', [])
    sequences = pl.get('sequences', {})
    # 去重：组合的(k,v)集合相同即同一模式，保留最优者
    groups = defaultdict(list)
    for p in raw_patterns:
        key = frozenset((k, v) for k, v in p.get('combo', {}).items())
        groups[key].append(p)
    patterns = []
    dedup_count = 0
    for key, group in groups.items():
        group.sort(key=lambda x: (x.get('dim_n', 0), x['lift'] * x['pct'], x['lift']), reverse=True)
        patterns.append(group[0])
        dedup_count += len(group) - 1
    periodic_count = len([v for v in sequences.values() if v.get('period', {}).get('found')])
    print('[1/3] 加载模式库: %d 个模式 → 去重后 %d 个 (-%d), %d 个时间序列(含%d个周期信号)' % (len(raw_patterns), len(patterns), dedup_count, len(sequences), periodic_count))
    dates, matches = find_today_matches(date_arg)
    if not matches:
        print('[2/3] 未找到比赛')
        return
    date_label = dates[0] + (' 等%d天' % len(dates) if len(dates) > 1 else '')
    print('[2/3] 找到 %d 场比赛 (%s)' % (len(matches), date_label))
    print('[3/3] 模式匹配...')
    report = match_patterns(matches, patterns, min_lift=1.5, sequences=sequences)
    print_report(report, date_label)
    out_file = os.path.join(SCRIPT_DIR, 'learnings', 'match_patterns_report.json')
    out = {
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'date': date_label,
        'total_matches': len(matches),
        'matched': len(report),
        'matches': report,
    }
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print('\n报告已保存: %s' % out_file)


if __name__ == '__main__':
    main()