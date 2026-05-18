# -*- coding: utf-8 -*-
"""
批量重跑 step8 + step19-23 - 只处理未完成的比赛
"""
import os, sys, json, time, subprocess
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(BASE_DIR, 'tasks')

def get_dates_from(start_date_str):
    start = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    today = datetime.now().date()
    dates = []
    d = start
    while d <= today:
        date_str = d.strftime('%Y-%m-%d')
        date_dir = os.path.join(TASKS_DIR, date_str)
        if os.path.isdir(date_dir):
            dates.append(date_str)
        d += timedelta(days=1)
    return dates

def get_match_dirs(date_str):
    data_dir = os.path.join(TASKS_DIR, date_str, 'data')
    if not os.path.isdir(data_dir):
        return []
    match_dirs = []
    for name in sorted(os.listdir(data_dir)):
        full = os.path.join(data_dir, name)
        if os.path.isdir(full) and name.startswith('match'):
            meta_path = os.path.join(full, 'meta.json')
            if os.path.exists(meta_path):
                match_dirs.append((name, full))
    return match_dirs

def read_meta(match_dir):
    with open(os.path.join(match_dir, 'meta.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

def needs_rerun(match_dir):
    """检查是否需要重跑"""
    step8_path = os.path.join(match_dir, 'group03_asian', 'step8_same_league.txt')
    step19_path = os.path.join(match_dir, 'group06_baijia', 'step19_baijia_compare.txt')
    
    if not os.path.exists(step8_path) or os.path.getsize(step8_path) < 100:
        return True
    if not os.path.exists(step19_path) or os.path.getsize(step19_path) < 100:
        return True
    
    # 检查修改时间是否是今天
    s8mod = datetime.fromtimestamp(os.path.getmtime(step8_path))
    if s8mod.date() >= datetime.now().date():
        return False  # 今天已更新，不需要重跑
    
    return True

def process_one_match(args):
    """处理单场比赛"""
    date_str, match_name, match_dir = args
    meta = read_meta(match_dir)
    home = meta.get('home', '')
    away = meta.get('away', '')
    
    # 运行 step8+19-23
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(BASE_DIR, 'step8_1923_extractor.py'), match_dir],
            cwd=BASE_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=300
        )
        step8_ok = result.returncode == 0
        if step8_ok:
            step8_path = os.path.join(match_dir, 'group03_asian', 'step8_same_league.txt')
            step19_path = os.path.join(match_dir, 'group06_baijia', 'step19_baijia_compare.txt')
            step8_ok = os.path.exists(step8_path) and os.path.getsize(step8_path) > 100
            step19_ok = os.path.exists(step19_path) and os.path.getsize(step19_path) > 100
            step8_ok = step8_ok and step19_ok
    except:
        step8_ok = False
    
    if not step8_ok:
        return '%s/%s: FAIL (step8/19-23)' % (date_str, match_name)
    
    # 生成最终报告
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(BASE_DIR, 'final_report_generator.py'), date_str, match_name, match_dir],
            cwd=BASE_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60
        )
        report_ok = result.returncode == 0
    except:
        report_ok = False
    
    if not report_ok:
        return '%s/%s: FAIL (report)' % (date_str, match_name)
    
    return '%s/%s: %s vs %s OK' % (date_str, match_name, home, away)

def main():
    start_date = '2026-05-07'
    dates = get_dates_from(start_date)
    print('日期范围: %s ~ %s' % (start_date, dates[-1] if dates else '无'))
    print('共 %d 天\n' % len(dates))
    
    # 收集所有待处理比赛
    all_matches = []
    for date_str in dates:
        for match_name, match_dir in get_match_dirs(date_str):
            if needs_rerun(match_dir):
                all_matches.append((date_str, match_name, match_dir))
    
    print('需要重跑: %d 场比赛\n' % len(all_matches))
    
    if not all_matches:
        print('所有比赛都已更新！')
        return
    
    success = 0
    failed = []
    
    # 并发处理（3个并发，避免被封IP）
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(process_one_match, m): m for m in all_matches}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            if 'FAIL' in result:
                failed.append(result)
                print('[%d/%d] %s' % (completed, len(all_matches), result))
            else:
                if completed % 5 == 0 or completed == len(all_matches):
                    print('[%d/%d] %s' % (completed, len(all_matches), result))
    
    print('\n' + '='*60)
    print('完成！共处理 %d 场比赛' % len(all_matches))
    print('成功: %d/%d' % (len(all_matches) - len(failed), len(all_matches)))
    if failed:
        print('失败: %d 场' % len(failed))
        for f in failed[:20]:
            print('  - %s' % f)

if __name__ == '__main__':
    main()
