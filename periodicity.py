# -*- coding: utf-8 -*-
"""周期检测引擎 — 自动发现时间序列中的重复模式"""
from collections import Counter


def find_period(sequence, max_period=6, min_cycles=2, min_confidence=0.6):
    """自动发现最小重复周期。最小周期优先，完美周期立即返回"""
    if len(sequence) < 4:
        return {'found': False, 'reason': '序列太短(%d场)' % len(sequence)}

    best = {'found': False, 'confidence': 0}

    for period in range(1, max_period + 1):
        need = period * min_cycles
        if len(sequence) < need:
            continue

        remainder = len(sequence) % period
        if remainder == 0:
            aligned = sequence
        else:
            aligned = sequence[remainder:]

        chunks = []
        for i in range(0, len(aligned), period):
            chunk = tuple(aligned[i:i + period])
            if len(chunk) == period:
                chunks.append(chunk)

        if len(chunks) < min_cycles:
            continue

        # 方案一: 完美周期（所有块一致）— 发现即返回，最小周期优先
        all_identical = all(c == chunks[0] for c in chunks)
        if all_identical:
            pattern = list(chunks[0])
            if not (period == 1 and len(set(pattern)) == 1):
                return {
                    'found': True, 'period': period,
                    'pattern': pattern, 'next': pattern[0],
                    'match_rate': 1.0, 'total_cycles': len(chunks),
                    'confidence': 1.0,
                }

        # 已有完美周期则不评估多数投票
        if best.get('found') and best.get('match_rate', 0) == 1.0:
            continue

        # 方案二: 多数投票
        pattern = []
        pos_matches = []
        for pos in range(period):
            values_at_pos = [c[pos] for c in chunks]
            counter = Counter(values_at_pos)
            most_common, count = counter.most_common(1)[0]
            pattern.append(most_common)
            pos_matches.append(count / len(chunks))

        match_rate = sum(pos_matches) / period

        if match_rate >= min_confidence:
            next_result = pattern[0]
            total_counter = Counter(sequence)
            base_rate = total_counter.get(next_result, 0) / max(len(sequence), 1)
            lift_vs_base = match_rate / base_rate if base_rate > 0 else 1.0
            conf = match_rate * min(1.0, len(chunks) / (min_cycles + 1))
            score = conf * lift_vs_base

            if score > best.get('score', 0) and lift_vs_base >= 1.2:
                best = {
                    'found': True, 'period': period,
                    'pattern': pattern, 'next': next_result,
                    'match_rate': round(match_rate, 2),
                    'total_cycles': len(chunks),
                    'confidence': round(conf, 2),
                    'lift_vs_base': round(lift_vs_base, 2),
                }

    return best if best.get('found') else {'found': False, 'reason': '未发现有效周期'}


def build_combo_sequences(matches):
    """构建 (联赛+特征组合) -> 时间序列"""
    from collections import defaultdict

    groups = defaultdict(list)
    for m in matches:
        feat = m.get('features', {})
        league = feat.get('联赛', '未知联赛')
        actual = m.get('actual', '')
        if actual not in ('胜', '平', '负'):
            continue
        for k, v in feat.items():
            if k == '联赛' or not v:
                continue
            group_key = '%s|%s=%s' % (league, k, v)
            groups[group_key].append({
                'actual': actual,
                'date': m.get('date', ''),
                'match_num': m.get('match_num', ''),
            })

    result = {}
    for group_key, items in groups.items():
        if len(items) < 5:
            continue
        items.sort(key=lambda x: x['date'])
        league = group_key.split('|')[0]
        dim_raw = group_key.split('|')[1]
        dim_name, dim_value = dim_raw.split('=', 1)

        sequence = [it['actual'] for it in items]
        dates = [it['date'] for it in items]

        entry = {
            'league': league, 'combo': {dim_name: dim_value},
            'sequence': sequence, 'dates': dates, 'length': len(sequence),
        }
        period_result = find_period(sequence)
        if period_result.get('found'):
            entry['period'] = period_result
        result[group_key] = entry

    return result


def print_periodic_patterns(sequences, top=20):
    found = {k: v for k, v in sequences.items() if v.get('period', {}).get('found')}
    if not found:
        print('  未发现周期性序列')
        return
    found_sorted = sorted(
        found.items(),
        key=lambda x: (x[1]['period'].get('confidence', 0) * x[1]['period'].get('total_cycles', 0)),
        reverse=True
    )
    for key, val in found_sorted[:top]:
        p = val['period']
        pattern_str = '→'.join(p['pattern'])
        seq_preview = ' '.join(val['sequence'][-12:])
        print('  🔄 [周期%d] %s' % (p['period'], key))
        print('     模式: [%s] -> 下次预测%s | 匹配率=%.0f%% | %d周期%d场' % (
            pattern_str, p['next'], p['match_rate'] * 100,
            p['total_cycles'], val['length']))
        print('     最近: %s' % seq_preview)
