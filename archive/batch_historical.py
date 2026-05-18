# -*- coding: utf-8 -*-
"""
批量跑历史竞彩数据
用法: python batch_historical.py
      python batch_historical.py --start 2026-04-01 --end 2026-04-30
      python batch_historical.py --start 2026-04-24 --end 2026-04-30 --feedback-only
"""
import os, sys, json, time, subprocess
from datetime import datetime, timedelta

import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def log(tag, msg):
    t = datetime.now().strftime('%H:%M:%S')
    print('[{}] [{}] {}'.format(t, tag, msg))

def run(cmd, timeout=600):
    """运行命令并返回结果"""
    log('RUN', ' '.join(str(x) for x in cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=timeout)
        if result.returncode != 0:
            err = result.stderr.strip().split('\n')[-3:] if result.stderr else ['unknown error']
            for line in err:
                log('ERR', line)
            return False
        return True
    except subprocess.TimeoutExpired:
        log('ERR', '超时')
        return False
    except Exception as e:
        log('ERR', str(e))
        return False

def is_empty_or_partial(date_str):
    """检查某天是否已经有完整报告"""
    task_dir = os.path.join(SCRIPT_DIR, 'tasks', date_str)
    if not os.path.exists(task_dir):
        return True
    
    # 统计报告数量
    report_count = 0
    for f in os.listdir(task_dir):
        if f.endswith('.md') and '周' in f:
            report_count += 1
    
    if report_count == 0:
        return True
    
    log('INFO', '{} 已有{}份报告'.format(date_str, report_count))
    return False

def main():
    start_date = datetime(2026, 4, 1)
    end_date = datetime(2026, 4, 30)
    feedback_only = False
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--start' and i + 1 < len(args):
            start_date = datetime.strptime(args[i+1], '%Y-%m-%d')
            i += 2
        elif args[i] == '--end' and i + 1 < len(args):
            end_date = datetime.strptime(args[i+1], '%Y-%m-%d')
            i += 2
        elif args[i] == '--feedback-only':
            feedback_only = True
            i += 1
        else:
            i += 1
    
    dates = []
    d = start_date
    while d <= end_date:
        dates.append(d.strftime('%Y-%m-%d'))
        d += timedelta(days=1)
    
    log('START', '批量历史数据处理')
    log('CONFIG', '日期范围: {} ~ {}'.format(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    log('CONFIG', '共{}天, 模式: {}'.format(len(dates), '仅反馈' if feedback_only else '完整流水线'))
    
    # Phase 1: 跑流水线
    if not feedback_only:
        log('PHASE', 'Phase 1: 跑流水线')
        for date_str in dates:
            if not is_empty_or_partial(date_str):
                log('SKIP', '{} 已有报告，跳过'.format(date_str))
                continue
            
            log('DATE', '处理 {}'.format(date_str))
            
            # Step 0: 获取比赛列表
            step0_ok = run([
                sys.executable,
                os.path.join(SCRIPT_DIR, 'step0_fetch_matches.py'),
                '--date', date_str,
                '--output-dir', os.path.join(SCRIPT_DIR, 'tasks')
            ], timeout=60)
            
            if not step0_ok:
                log('SKIP', '{} 获取比赛列表失败，跳过'.format(date_str))
                time.sleep(5)
                continue
            
            # Step 1-25: 跑流水线
            run_ok = run([
                sys.executable,
                os.path.join(SCRIPT_DIR, 'run_pipeline.py'),
                date_str
            ], timeout=3600)  # 1小时超时（一天可能有多场比赛）
            
            if run_ok:
                log('OK', '{} 流水线完成'.format(date_str))
            else:
                log('FAIL', '{} 流水线失败'.format(date_str))
            
            time.sleep(10)  # 避免太快被限流
    
    # Phase 2: 跑反馈
    log('PHASE', 'Phase 2: 跑反馈')
    for date_str in dates:
        log('DATE', '反馈 {}'.format(date_str))
        
        feedback_ok = run([
            sys.executable,
            os.path.join(SCRIPT_DIR, 'jingcai_feedback_v2.py'),
            date_str
        ], timeout=120)
        
        if feedback_ok:
            log('OK', '{} 反馈完成'.format(date_str))
        else:
            log('FAIL', '{} 反馈失败'.format(date_str))
        
        time.sleep(3)
    
    log('DONE', '全部完成')

if __name__ == '__main__':
    main()
