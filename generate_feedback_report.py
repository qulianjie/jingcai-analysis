# -*- coding: utf-8 -*-
"""生成竞彩反馈报告"""
import os, sys, json, re
from datetime import datetime, timedelta

import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')
RESULTS_DIR = SCRIPT_DIR

def get_date_arg():
    if len(sys.argv) > 2 and sys.argv[1] == '--date':
        return sys.argv[2]
    return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

def find_reports(date_str):
    task_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.exists(task_dir):
        return []
    reports = []
    for f in os.listdir(task_dir):
        if f.endswith('.md') and re.search(r'周[一二三四五六日]\d{3}_', f):
            reports.append(os.path.join(task_dir, f))
    return sorted(reports)

def extract_prediction(report_path):
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract match number from filename
    fn = os.path.basename(report_path)
    mn = re.search(r'周[一二三四五六日](\d{3})', fn)
    match_num = mn.group(1) if mn else '???'
    
    # Extract teams from filename
    tm = re.search(r'周[一二三四五六日]\d{3}_(.+?)vs(.+?)\.md', fn)
    home = tm.group(1).strip() if tm else 'Unknown'
    away = tm.group(2).strip() if tm else 'Unknown'
    
    # Extract league from content
    league = ''
    lm = re.search(r'比赛[：:]\s*([^·\n]+)·', content)
    if lm:
        league = lm.group(1).strip()
    
    # Extract recommendation
    pred = ''
    rec = re.search(r'\*\*推荐\*\*\s*\|\s*([^\|]+)', content)
    if rec:
        pred = rec.group(1).strip()
    
    # Extract confidence
    conf = ''
    cm = re.search(r'\*\*信心\*\*\s*\|\s*([^\|]+)', content)
    if cm:
        conf = cm.group(1).strip()
    
    return {
        'match_num': match_num,
        'home': home,
        'away': away,
        'league': league,
        'predicted': pred,
        'confidence': conf,
    }

def load_results(date_str):
    rf = os.path.join(RESULTS_DIR, 'results_{}.json'.format(date_str))
    if not os.path.exists(rf):
        return {}
    with open(rf, 'r', encoding='utf-8') as f:
        data = json.loads(f.read())
    return data.get(date_str, {})

def predict_to_result(pred):
    """Convert prediction to result category"""
    if not pred:
        return ''
    if '主胜' in pred or '胜' in pred:
        return '胜'
    if '客胜' in pred or '负' in pred:
        return '负'
    if '平' in pred:
        return '平'
    return ''

def check_correct(pred, actual):
    """Check if prediction matches actual result"""
    if not pred or not actual or actual == '待查':
        return None
    pred_r = predict_to_result(pred)
    return pred_r == actual

def main():
    date_str = get_date_arg()
    reports = find_reports(date_str)
    
    if not reports:
        print('[WARN] 没有找到 {} 的报告'.format(date_str))
        return
    
    results = load_results(date_str)
    
    items = []
    for rp in reports:
        info = extract_prediction(rp)
        num = info['match_num']
        actual = results.get(num, {'score': '待查', 'result': '待查'})
        score = actual.get('score', '待查')
        actual_result = actual.get('result', '待查')
        correct = check_correct(info['predicted'], actual_result)
        
        items.append({
            **info,
            'score': score,
            'actual': actual_result,
            'correct': correct,
        })
    
    # Summary
    total = sum(1 for i in items if i['correct'] is not None)
    correct_count = sum(1 for i in items if i['correct'])
    accuracy = round(correct_count / total * 100, 1) if total > 0 else 0
    
    print('=' * 70)
    print('  竞彩反馈报告 - {}'.format(date_str))
    print('=' * 70)
    print()
    print('场次    联赛      对阵                    比分      预测        信心            实际      结果')
    print('-' * 70)
    
    for i in items:
        status = '[OK]' if i['correct'] else ('[??]' if i['correct'] is None else '[X]')
        conf_display = i['confidence'] if i['confidence'] else '-'
        teams = '{} vs {}'.format(i['home'], i['away'])
        print('{:<8} {:<8} {:<22} {:<8} {:<10} {:<16} {:<8} {}'.format(
            i['match_num'],
            i['league'] or '-',
            teams,
            i['score'],
            i['predicted'] or '-',
            conf_display,
            i['actual'],
            status
        ))
    
    print('-' * 70)
    print()
    print('总场次: {} | 有效: {} | 正确: {} | 错误: {} | 准确率: {}%'.format(
        len(items), total, correct_count, total - correct_count, accuracy
    ))
    
    # Save feedback
    learnings_dir = os.path.join(SCRIPT_DIR, 'learnings')
    os.makedirs(learnings_dir, exist_ok=True)
    feedback_file = os.path.join(learnings_dir, 'feedback.json')
    
    existing = {'dates': {}, 'stats': {'total_matches': 0, 'total_correct': 0, 'overall_accuracy': 0}}
    if os.path.exists(feedback_file):
        try:
            with open(feedback_file, 'r', encoding='utf-8') as f:
                existing = json.loads(f.read())
        except:
            pass
    
    date_feedback = {'feedback': [], 'accuracy': accuracy}
    for i in items:
        date_feedback['feedback'].append({
            'match_num': i['match_num'],
            'predicted': i['predicted'],
            'actual': i['actual'],
            'score': i['score'],
            'correct': i['correct'],
        })
    
    existing['dates'][date_str] = date_feedback
    
    # Update stats
    all_correct = 0
    all_total = 0
    for ds, df in existing['dates'].items():
        for fb in df.get('feedback', []):
            if fb.get('correct') is not None:
                all_total += 1
                if fb.get('correct'):
                    all_correct += 1
    existing['stats'] = {
        'total_matches': all_total,
        'total_correct': all_correct,
        'overall_accuracy': round(all_correct / all_total * 100, 1) if all_total > 0 else 0
    }
    
    with open(feedback_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(existing, ensure_ascii=False, indent=2))
    
    print()
    print('[LEARN] 已保存 {} 场反馈到 learnings/feedback.json'.format(len(items)))
    print('        累计准确率: {}/{} ({})'.format(
        existing['stats']['total_correct'],
        existing['stats']['total_matches'],
        existing['stats']['overall_accuracy']
    ))
    print()
    print('=' * 70)

if __name__ == '__main__':
    main()
