# -*- coding: utf-8 -*-
"""
批量拉取赛果 + 批量反馈
用法: python batch_feedback_full.py
"""
import os, sys, json, time, subprocess
from datetime import datetime, timedelta

import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def log(tag, msg):
    t = datetime.now().strftime('%H:%M:%S')
    msg = str(msg).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    print('[{}] [{}] {}'.format(t, tag, msg))
    sys.stdout.flush()

def main():
    # Dates 04-03 to 04-28
    start = datetime(2026, 4, 3)
    end = datetime(2026, 4, 28)
    
    dates = []
    d = start
    while d <= end:
        ds = d.strftime('%Y-%m-%d')
        rf = os.path.join(SCRIPT_DIR, 'results_{}.json'.format(ds))
        if not os.path.exists(rf):
            dates.append(ds)
        d += timedelta(days=1)
    
    print('=' * 60)
    log('START', '拉取赛果: {} 个日期'.format(len(dates)))
    print('=' * 60)
    
    fetched = 0
    for i, ds in enumerate(dates):
        log('FETCH', '({}/{}) {}'.format(i+1, len(dates), ds))
        
        # Use the internal fetch function
        sys.path.insert(0, SCRIPT_DIR)
        import fetch_results
        results = fetch_results.fetch_results_for_date(ds)
        
        if results:
            rf = os.path.join(SCRIPT_DIR, 'results_{}.json'.format(ds))
            
            # Merge with existing
            existing = {}
            if os.path.exists(rf):
                with open(rf, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            
            existing[ds] = results
            with open(rf, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            
            log('OK', '{} 拉取到 {} 个赛果'.format(ds, len(results)))
            fetched += 1
        else:
            log('WARN', '{} 无赛果'.format(ds))
        
        time.sleep(3)
    
    print('\n' + '=' * 60)
    log('FETCH', '完成: {} 个日期'.format(fetched))
    print('=' * 60)
    
    # Now run feedback for all dates that have both reports and results
    print('\n' + '=' * 60)
    log('FEED', '开始批量反馈')
    print('=' * 60)
    
    import batch_feedback
    
    # Dates that have results
    all_dates = []
    d = start
    while d <= end:
        ds = d.strftime('%Y-%m-%d')
        rf = os.path.join(SCRIPT_DIR, 'results_{}.json'.format(ds))
        if os.path.exists(rf):
            all_dates.append(ds)
        d += timedelta(days=1)
    
    feedback_count = 0
    for ds in all_dates:
        log('FEED', '反馈 {}'.format(ds))
        try:
            batch_feedback.run_feedback_for_date(ds)
            feedback_count += 1
        except Exception as e:
            log('ERR', '{} 反馈失败: {}'.format(ds, e))
        time.sleep(1)
    
    print('\n' + '=' * 60)
    log('DONE', '反馈完成: {} 个日期'.format(feedback_count))
    print('=' * 60)

if __name__ == '__main__':
    main()
