# -*- coding: utf-8 -*-
"""
竞彩反馈 Python 版 -- 替代 feedback.js（Node.js 不可用时的降级方案）
从 task 目录提取比赛结果，合并 step25/26 数据，更新 feedback.json
"""
import os, sys, json, re, glob
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_FILE = os.path.join(SCRIPT_DIR, 'learnings', 'feedback.json')
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')


def find_latest_task_date():
    """找到有比赛数据的最新日期"""
    dates = []
    for d in os.listdir(TASKS_DIR):
        dp = os.path.join(TASKS_DIR, d)
        if os.path.isdir(dp) and re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            data_dir = os.path.join(dp, 'data')
            if os.path.exists(data_dir):
                matches = [m for m in os.listdir(data_dir) 
                          if m.startswith('match') and os.path.isdir(os.path.join(data_dir, m))]
                if matches:
                    dates.append((d, len(matches)))
    dates.sort(key=lambda x: x[0], reverse=True)
    return dates


def load_feedback():
    """加载现有的 feedback.json"""
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'dates': {}, 'stats': {}}


def save_feedback(data):
    """保存 feedback.json"""
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('  feedback.json saved (%d bytes)' % os.path.getsize(FEEDBACK_FILE))


def read_meta_safely(meta_path):
    """安全读取 meta.json"""
    result = {}
    if not os.path.exists(meta_path):
        return result
    try:
        with open(meta_path, 'r', encoding='utf-8', errors='replace') as f:
            meta = json.load(f)
        result['match_num'] = meta.get('matchnum', '')
        result['home'] = meta.get('home', '')
        result['away'] = meta.get('away', '')
        result['fid'] = meta.get('fid', '')
        result['league'] = meta.get('league', '')
        result['rq'] = meta.get('rq', '')
    except Exception:
        try:
            with open(meta_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            mn = re.search(r'\\"matchnum\\"\\s*:\\s*\\"([^\\"]+)\\"', content)
            if mn: result['match_num'] = mn.group(1)
            hm = re.search(r'\\"home\\"\\s*:\\s*\\"([^\\"]+)\\"', content)
            if hm: result['home'] = hm.group(1)
            aw = re.search(r'\\"away\\"\\s*:\\s*\\"([^\\"]+)\\"', content)
            if aw: result['away'] = aw.group(1)
        except Exception:
            pass
    return result


def extract_score_from_step24(match_dir_path):
    """从 step24_panlu_match.json 提取比分"""
    step24_path = os.path.join(match_dir_path, 'step24_panlu_match.json')
    if os.path.exists(step24_path):
        try:
            with open(step24_path, 'r', encoding='utf-8', errors='replace') as f:
                s24 = json.load(f)
            score = s24.get('\\u6bd4\\u5206', '') or s24.get('score', '') or ''
            if ':' in str(score):
                parts = str(score).split(':')
                try:
                    hs, aw = int(parts[0]), int(parts[1])
                    if hs <= 20 and aw <= 20:
                        return hs, aw
                except Exception:
                    pass
        except Exception:
            pass
    return None, None


def extract_score_from_files(match_dir_path):
    """从 match 目录的文件中搜索比分"""
    for root, dirs, files in os.walk(match_dir_path):
        for f in files:
            if 'score' in f.lower() or '\\u6bd4' in f or '\\u5206' in f:
                fp = os.path.join(root, f)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                        content = fh.read()
                    sc = re.search(r'(\\d+)[:：](\\d+)', content)
                    if sc:
                        hs, aw = int(sc.group(1)), int(sc.group(2))
                        if hs <= 20 and aw <= 20:
                            return hs, aw
                except Exception:
                    pass
    return None, None


def extract_match_results_from_report(date_str, match_dir_path):
    """从 step 文件和报告提取比赛结果"""
    result = {'date': date_str, 'has_score': False}
    
    # 1. meta.json
    meta_path = os.path.join(match_dir_path, 'meta.json')
    meta = read_meta_safely(meta_path)
    result.update(meta)
    
    # 2. step24
    hs, aw = extract_score_from_step24(match_dir_path)
    if hs is not None:
        result['home_score'] = hs
        result['away_score'] = aw
        result['has_score'] = True
    
    # 3. try files
    if not result.get('has_score'):
        hs, aw = extract_score_from_files(match_dir_path)
        if hs is not None:
            result['home_score'] = hs
            result['away_score'] = aw
            result['has_score'] = True
    
    if result.get('has_score'):
        hs = result['home_score']
        aw = result['away_score']
        if hs > aw:
            result['result'] = '\\u80dc'
        elif hs < aw:
            result['result'] = '\\u8d1f'
        else:
            result['result'] = '\\u5e73'
        result['score_str'] = '%d:%d' % (hs, aw)
    
    return result


def process_date(date_str):
    """处理一天的数据"""
    task_dir = os.path.join(TASKS_DIR, date_str)
    data_dir = os.path.join(task_dir, 'data')
    if not os.path.exists(data_dir):
        return []
    
    matches = sorted([m for m in os.listdir(data_dir)
                     if m.startswith('match') and os.path.isdir(os.path.join(data_dir, m))])
    
    results = []
    for match_dir in matches:
        match_path = os.path.join(data_dir, match_dir)
        r = extract_match_results_from_report(date_str, match_path)
        results.append(r)
    
    return results


def main():
    print('=' * 60)
    print('\\u7ade\\u5f69\\u53cd\\u9988\\u5f15\\u64ce\\uff08Python \\u964d\\u7ea7\\u7248\\uff09')
    print('\\u8fd0\\u884c\\u65f6\\u95f4: %s' % datetime.now().strftime('%Y-%m-%d %H:%M'))
    print('=' * 60)
    
    latest_dates = find_latest_task_date()
    if not latest_dates:
        print('No task data found')
        return
    
    print('Found %d dates with data' % len(latest_dates))
    print('Latest 5: %s' % [d[0] for d in latest_dates[:5]])
    
    latest = latest_dates[0][0]
    print('Processing latest: %s (%d matches)' % (latest, latest_dates[0][1]))
    
    results = process_date(latest)
    print('Extracted %d matches' % len(results))
    scored = [r for r in results if r.get('has_score')]
    print('With scores: %d' % len(scored))
    for r in scored:
        print('  %s %s vs %s: %s (%s)' % (
            r.get('match_num', '?'), 
            r.get('home', '?'), 
            r.get('away', '?'), 
            r.get('score_str', ''),
            r.get('result', '')))
    
    print('Loading existing feedback...')
    feedback = load_feedback()
    date_count = len(feedback.get('dates', {}))
    print('Current dates in feedback: %d' % date_count)
    
    if latest not in feedback.get('dates', {}):
        date_entry = {}
        for r in results:
            mn = r.get('match_num', '')
            if mn:
                entry = {
                    'result': r.get('result', ''),
                    'score': r.get('score_str', ''),
                    'home': r.get('home', ''),
                    'away': r.get('away', ''),
                    'league': r.get('league', ''),
                    'has_score': r.get('has_score', False),
                }
                date_entry[mn] = entry
        feedback['dates'][latest] = date_entry
        feedback['stats']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print('Added %s to feedback data' % latest)
    else:
        print('%s already in feedback, skipping' % latest)
    
    print('Saving feedback...')
    save_feedback(feedback)
    
    print('Done.')


if __name__ == '__main__':
    main()
