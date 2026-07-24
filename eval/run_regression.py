#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞彩 Eval 回归测试套件

用途：检测改动（prompt/pattern/config/模型）是否导致预测准确率退化

用法：
  python eval/run_regression.py             # 显示当前 vs baseline 对比
  python eval/run_regression.py --update     # 记录当前为新的 baseline
  python eval/run_regression.py --check      # 只显示当前状态

输出：
  退出码 0 = 无显著退化（accuracy drop < 5%）
  退出码 1 = 显著退化
  退出码 2 = 数据不足
"""

import os, sys, json
from datetime import datetime
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__ or '.')))
EVAL_DIR = os.path.join(ROOT, 'eval')
TEST_SET_FILE = os.path.join(EVAL_DIR, 'test_set.json')
BASELINE_FILE = os.path.join(EVAL_DIR, 'baseline.json')
FEEDBACK_FILE = os.path.join(ROOT, 'learnings', 'feedback.json')

REGRESSION_THRESHOLD = 0.05


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compute_current_accuracy(test_set, feedback):
    dates = feedback.get('dates', {})
    results = []
    for m in test_set:
        d = m['date']
        mn = m['match_num']
        if d not in dates:
            results.append({**m, 'current_correct': None})
            continue
        found = None
        for fb in dates[d].get('feedback', []):
            if fb.get('match_num') == mn:
                found = fb
                break
        if found:
            results.append({
                **m,
                'current_predicted': found.get('predicted'),
                'current_actual': found.get('actual'),
                'current_correct': found.get('correct'),
                'current_confidence': found.get('confidence'),
            })
        else:
            results.append({**m, 'current_correct': None})
    return results


def compute_metrics(results):
    valid = [r for r in results if r.get('current_correct') is not None]
    total = len(valid)
    correct = sum(1 for r in valid if r['current_correct'])
    accuracy = correct / total if total > 0 else 0
    dc = Counter(r['date'] for r in valid)
    per_date = {}
    for d in sorted(dc):
        ms = [r for r in valid if r['date'] == d]
        c = sum(1 for r in ms if r['current_correct'])
        per_date[d] = {'total': len(ms), 'correct': c, 'accuracy': round(c / len(ms), 4)}
    return {'total': total, 'correct': correct, 'accuracy': round(accuracy, 4),
            'per_date': per_date, 'valid': valid}


def print_comparison(current, baseline, test_set_total):
    print('=' * 60)
    print('  竞彩 Eval 回归测试报告')
    print('  生成时间: ' + datetime.now().strftime('%Y-%m-%d %H:%M'))
    print('=' * 60)

    c_acc = current['accuracy']
    c_total = current['total']
    c_correct = current['correct']

    b_total = baseline.get('total', baseline.get('total_matches', 0))
    b_correct = baseline.get('correct', 0)
    b_acc_val = baseline.get('accuracy', 0)

    print()
    print('测试集: ' + str(test_set_total) + ' 场比赛')
    print('  Baseline准确率: ' + format(b_acc_val*100, '.1f') + '% (' + str(b_correct) + '/' + str(b_total) + ')')
    print('  当前准确率:     ' + format(c_acc*100, '.1f') + '% (' + str(c_correct) + '/' + str(c_total) + ')')

    if b_total > 0:
        delta = c_acc - b_acc_val
        delta_str = '+' + format(delta*100, '.1f') + '%' if delta >= 0 else format(delta*100, '.1f') + '%'
        if delta < -REGRESSION_THRESHOLD:
            flag = '退化'
        elif delta > REGRESSION_THRESHOLD:
            flag = '提升'
        else:
            flag = '持平'
        print('  变化: ' + delta_str + ' ' + flag)

    print()
    print('分日表现:')
    for d in sorted(current['per_date']):
        cd = current['per_date'][d]
        bd = baseline.get('per_date', {}).get(d, {})
        b_acc = bd.get('accuracy', 0)
        b_tot = bd.get('total', 0)
        delta = cd['accuracy'] - b_acc
        delta_s = ' (' + format(delta*100, '+.1f') + '%)' if b_tot > 0 else ' (新)'
        bar = '#' * int(cd['accuracy'] * 30) + '-' * (30 - int(cd['accuracy'] * 30))
        print('  ' + d + ': ' + format(cd['accuracy']*100, '5.1f') + delta_s + ' ' + bar + ' (' + str(cd['correct']) + '/' + str(cd['total']) + ')')

    print()
    print('联赛分布:')
    leagues = {}
    for r in current['valid']:
        league = r.get('league', '其他')
        if league not in leagues:
            leagues[league] = {'total': 0, 'correct': 0}
        if r.get('current_correct') is not None:
            leagues[league]['total'] += 1
            if r['current_correct']:
                leagues[league]['correct'] += 1
    for league, ld in sorted(leagues.items(), key=lambda x: -x[1]['total']):
        acc = ld['correct'] / ld['total'] if ld['total'] > 0 else 0
        bar = '#' * int(acc * 20) + '-' * (20 - int(acc * 20))
        print('  ' + league.ljust(12) + ': ' + format(acc*100, '5.1f') + '% ' + bar + ' (' + str(ld['correct']) + '/' + str(ld['total']) + ')')

    no_result = [r for r in current['valid'] if r.get('current_correct') is None]
    if no_result:
        print()
        print('注意: ' + str(len(no_result)) + ' 场比赛无当前反馈数据')
        for nr in no_result[:3]:
            print('  ' + nr['date'] + ' #' + nr.get('match_num', '?') + ': ' + nr.get('league', '?'))
        if len(no_result) > 3:
            print('  ... 还有 ' + str(len(no_result)-3) + ' 场')

    return c_acc - b_acc_val


def main():
    if not os.path.exists(FEEDBACK_FILE):
        print('feedback.json 不存在')
        sys.exit(2)
    if not os.path.exists(TEST_SET_FILE):
        print('test_set.json 不存在')
        sys.exit(2)

    test_set_data = load_json(TEST_SET_FILE)
    test_set = test_set_data.get('matches', [])
    feedback = load_json(FEEDBACK_FILE)

    results = compute_current_accuracy(test_set, feedback)
    current = compute_metrics(results)

    if current['total'] < 10:
        print('测试集只有 ' + str(current['total']) + ' 场比赛有反馈数据')
        sys.exit(2)

    if os.path.exists(BASELINE_FILE):
        baseline = load_json(BASELINE_FILE)
    else:
        baseline = {'accuracy': 0, 'total': 0, 'correct': 0, 'per_date': {}}

    update_baseline = '--update' in sys.argv
    check_only = '--check' in sys.argv

    if check_only:
        print('当前准确率: ' + format(current['accuracy']*100, '.1f') + '% (' + str(current['correct']) + '/' + str(current['total']) + ')')
        return

    delta = print_comparison(current, baseline, len(test_set))

    if update_baseline:
        leagues = {}
        for r in current['valid']:
            league = r.get('league', '其他')
            if league not in leagues:
                leagues[league] = {'total': 0, 'correct': 0}
            if r.get('current_correct') is not None:
                leagues[league]['total'] += 1
                if r['current_correct']:
                    leagues[league]['correct'] += 1
        per_league = {}
        for league, ld in leagues.items():
            per_league[league] = {
                'total': ld['total'],
                'correct': ld['correct'],
                'accuracy': round(ld['correct'] / ld['total'], 4) if ld['total'] > 0 else 0
            }
        new_baseline = {
            'created': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'test_dates': test_set_data.get('test_dates'),
            'total_matches': current['total'],
            'correct': current['correct'],
            'accuracy': current['accuracy'],
            'per_date': current['per_date'],
            'per_league': per_league,
        }
        with open(BASELINE_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_baseline, f, ensure_ascii=False, indent=2)
        print()
        print('Baseline 已更新为 ' + format(new_baseline['accuracy']*100, '.1f') + '%')

    if delta < -REGRESSION_THRESHOLD:
        print()
        print('准确率下降 ' + format(abs(delta)*100, '.1f') + '% > ' + format(REGRESSION_THRESHOLD*100, '.0f') + '% 阈值，标记退化')
        sys.exit(1)
    elif delta > REGRESSION_THRESHOLD:
        print()
        print('准确率提升 ' + format(delta*100, '.1f') + '%')


if __name__ == '__main__':
    main()
