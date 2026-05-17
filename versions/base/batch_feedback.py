# -*- coding: utf-8 -*-
"""
批量反馈 - 对已有报告的日期运行反馈机制
用法: python batch_feedback.py [--dates 2026-04-24,2026-04-25,...]
"""
import os, sys, json, re
from datetime import datetime

import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')
LEARNINGS_DIR = os.path.join(SCRIPT_DIR, 'learnings')

def log(tag, msg):
    t = datetime.now().strftime('%H:%M:%S')
    msg = str(msg).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    print('[{}] [{}] {}'.format(t, tag, msg))

def find_report_files(date_str):
    """找到某天的所有报告文件"""
    task_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.exists(task_dir):
        return []
    
    reports = []
    for f in os.listdir(task_dir):
        if f.endswith('.md') and re.search(r'周[一二三四五六日]\d{3}_', f):
            reports.append(os.path.join(task_dir, f))
    
    # Also check data/ subdirectory
    data_dir = os.path.join(task_dir, 'data')
    if os.path.exists(data_dir):
        for d in os.listdir(data_dir):
            dp = os.path.join(data_dir, d)
            if os.path.isdir(dp):
                for f in os.listdir(dp):
                    if f == 'final_report.md':
                        reports.append(os.path.join(dp, f))
    
    return reports

def extract_prediction(report_path):
    """从报告中提取预测"""
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return None
    
    # Extract match number
    match_num_match = re.search(r'(周[一二三四五六日])(\d{3})', os.path.basename(report_path))
    if not match_num_match:
        # Try to find in content
        match_num_match = re.search(r'竞彩编号[：:]\s*(\d{3})', content)
        if not match_num_match:
            return None
    
    match_num = match_num_match.group(2)
    
    # Extract recommendation
    pred = ''
    rec_match = re.search(r'\*\*推荐\*\*\s*\|\s*([^\|]+)', content)
    if rec_match:
        rec_text = rec_match.group(1).strip()
        if '主胜' in rec_text or ('胜' in rec_text and '客' not in rec_text and '平' not in rec_text):
            pred = '胜'
        elif '客胜' in rec_text:
            pred = '负'
        elif '平局' in rec_text or ('平' in rec_text and '胜' not in rec_text and '负' not in rec_text):
            pred = '平'
        elif '不败' in rec_text:
            pred = '胜/平'
        elif '分胜负' in rec_text:
            pred = '胜/负'
    
    # Extract confidence
    confidence = ''
    conf_match = re.search(r'\*\*信心\*\*\s*\|\s*([^\|]+)', content)
    if conf_match:
        confidence = conf_match.group(1).strip()
    
    # Extract home/away
    home = away = ''
    team_match = re.search(r'主队[：:]\s*(.+)', content)
    if team_match:
        home = team_match.group(1).strip()
    team_match = re.search(r'客队[：:]\s*(.+)', content)
    if team_match:
        away = team_match.group(1).strip()
    
    return {
        'match_num': match_num,
        'home': home,
        'away': away,
        'predicted': pred,
        'confidence': confidence,
    }

def run_feedback_for_date(date_str):
    """对单个日期运行反馈"""
    log('DATE', '处理 {}'.format(date_str))
    
    # Find reports
    reports = find_report_files(date_str)
    if not reports:
        log('SKIP', '没有找到报告文件')
        return
    
    log('INFO', '找到 {} 份报告'.format(len(reports)))
    
    # Extract predictions
    predictions = {}
    for rp in reports:
        pred = extract_prediction(rp)
        if pred:
            predictions[pred['match_num']] = pred
    
    log('INFO', '提取到 {} 个预测'.format(len(predictions)))
    
    # Load results
    results_file = os.path.join(SCRIPT_DIR, 'results_{}.json'.format(date_str))
    if not os.path.exists(results_file):
        log('WARN', '没有找到结果文件: {}'.format(results_file))
        log('INFO', '反馈需要实际赛果数据，请先准备 results_{}.json'.format(date_str))
        return
    
    with open(results_file, 'r', encoding='utf-8') as f:
        all_results = json.load(f)
    
    results = all_results.get(date_str, {})
    if not results:
        # Try to find results in the date_str key format
        for k, v in all_results.items():
            if date_str in k or k in date_str:
                results = v
                break
    
    log('INFO', '找到 {} 个实际赛果'.format(len(results)))
    
    # Compare
    feedback_items = []
    total_correct = 0
    total_checked = 0
    
    for match_num, result_data in results.items():
        pred_data = predictions.get(match_num, {})
        
        actual = result_data.get('result', '待查')
        predicted = pred_data.get('predicted', '-')
        confidence = pred_data.get('confidence', '-')
        
        is_correct = (predicted == actual) and actual != '待查'
        if actual != '待查':
            total_checked += 1
            if is_correct:
                total_correct += 1
        
        feedback_items.append({
            'match_num': match_num,
            'match_name': '{} vs {}'.format(
                result_data.get('home', pred_data.get('home', '')),
                result_data.get('away', pred_data.get('away', ''))
            ),
            'score': result_data.get('score', ''),
            'actual': actual,
            'predicted': predicted,
            'confidence': confidence,
            'correct': is_correct,
        })
    
    # Print summary
    print('')
    print('=' * 70)
    print('  {} 反馈结果'.format(date_str))
    print('=' * 70)
    print('{:<6} {:<25} {:<8} {:<8} {:<15} {:<6} {}'.format(
        '场次', '对阵', '比分', '预测', '信心', '实际', '结果'))
    print('-' * 70)
    
    for item in feedback_items:
        status = '[OK]' if item['correct'] else ('[?]' if item['actual'] == '待查' else '[X]')
        print('{:<6} {:<25} {:<8} {:<8} {:<15} {:<6} {}'.format(
            item['match_num'], item['match_name'][:24], item['score'],
            item['predicted'], item['confidence'][:14], item['actual'], status))
    
    print('')
    if total_checked > 0:
        accuracy = total_correct / total_checked * 100
        print('总准确率: {}/{} ({:.1f}%)'.format(total_correct, total_checked, accuracy))
    else:
        print('暂无已结算比赛')
    print('=' * 70)
    print('')

def main():
    log('START', '批量反馈')
    
    # Default: all dates with reports
    dates_to_process = []
    
    if len(sys.argv) > 1 and sys.argv[1] == '--dates':
        dates_to_process = sys.argv[2].split(',') if len(sys.argv) > 2 else []
    else:
        # Auto-detect dates with reports
        if os.path.exists(TASKS_DIR):
            for d in sorted(os.listdir(TASKS_DIR)):
                if re.match(r'\d{4}-\d{2}-\d{2}', d):
                    reports = find_report_files(d)
                    if reports:
                        dates_to_process.append(d)
    
    log('CONFIG', '待处理日期: {}'.format(', '.join(dates_to_process) if dates_to_process else '无'))
    
    for date_str in dates_to_process:
        run_feedback_for_date(date_str)
        print('')
    
    log('DONE', '全部完成')

if __name__ == '__main__':
    main()
