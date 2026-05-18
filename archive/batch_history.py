# -*- coding: utf-8 -*-
"""
历史数据批量处理总控脚本

用法:
  python batch_history.py                        # 处理4月全月（有报告的直接feedback）
  python batch_history.py --start 2026-04-24     # 指定起始日期
  python batch_history.py --dates 2026-04-24,2026-04-25  # 指定具体日期
  python batch_history.py --feedback-only        # 只跑feedback（不重新生成报告）
"""
import os, sys, json, re, time, subprocess
from datetime import datetime, timedelta

import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')

def log(tag, msg):
    t = datetime.now().strftime('%H:%M:%S')
    msg = str(msg).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    print('[{}] [{}] {}'.format(t, tag, msg))

def run(cmd, timeout=600):
    log('RUN', ' '.join(str(x) for x in cmd[-3:]))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=timeout)
        if result.returncode != 0:
            err_lines = result.stderr.strip().split('\n')[-3:] if result.stderr else ['unknown']
            for line in err_lines:
                log('ERR', line.strip())
            return False
        return True
    except subprocess.TimeoutExpired:
        log('ERR', '超时({}s)'.format(timeout))
        return False
    except Exception as e:
        log('ERR', str(e))
        return False

def has_reports(date_str):
    """检查某天是否已有报告"""
    task_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.exists(task_dir):
        return False
    for f in os.listdir(task_dir):
        if f.endswith('.md') and re.search(r'周[一二三四五六日]\d{3}_', f):
            return True
    return False

def has_results(date_str):
    """检查是否有赛果文件"""
    return os.path.exists(os.path.join(SCRIPT_DIR, 'results_{}.json'.format(date_str)))

def process_date(date_str, feedback_only=False):
    """处理单个日期"""
    log('DATE', '====== {} ======'.format(date_str))
    
    has_rpt = has_reports(date_str)
    has_res = has_results(date_str)
    
    log('STATUS', '报告: {}, 赛果: {}'.format('有' if has_rpt else '无', '有' if has_res else '无'))
    
    if feedback_only:
        # 只跑feedback
        pass
    else:
        # 先跑pipeline生成报告
        if not has_rpt:
            log('STEP', 'Step0: 获取比赛列表')
            ok = run([
                sys.executable, os.path.join(SCRIPT_DIR, 'step0_fetch_matches.py'),
                '--date', date_str, '--output-dir', TASKS_DIR
            ], timeout=60)
            if not ok:
                log('SKIP', '获取比赛列表失败')
                time.sleep(5)
                return False
            
            time.sleep(3)
            
            log('STEP', 'Pipeline: 生成报告')
            ok = run([
                sys.executable, os.path.join(SCRIPT_DIR, 'run_pipeline.py'), date_str
            ], timeout=1800)  # 30分钟
            
            if not ok:
                log('WARN', '流水线失败')
            else:
                log('OK', '流水线完成')
            
            time.sleep(5)
        else:
            log('SKIP', '报告已存在，跳过pipeline')
    
    # 跑feedback
    if has_rpt or has_reports(date_str):
        log('STEP', 'Feedback: 学习历史数据')
        ok = run([
            sys.executable, os.path.join(SCRIPT_DIR, 'jingcai_feedback_v2.py'), date_str
        ], timeout=120)
        
        if ok:
            log('OK', '反馈完成')
        else:
            log('WARN', '反馈失败')
        
        time.sleep(2)
    else:
        log('SKIP', '无报告，跳过feedback')
    
    return True

def main():
    phase = 'pipeline+feedback'
    start_date = datetime(2026, 4, 24)
    end_date = datetime(2026, 4, 30)
    specific_dates = []
    feedback_only = False
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--start' and i+1 < len(args):
            start_date = datetime.strptime(args[i+1], '%Y-%m-%d')
            i += 2
        elif args[i] == '--end' and i+1 < len(args):
            end_date = datetime.strptime(args[i+1], '%Y-%m-%d')
            i += 2
        elif args[i] == '--dates' and i+1 < len(args):
            specific_dates = [d.strip() for d in args[i+1].split(',')]
            i += 2
        elif args[i] == '--feedback-only':
            feedback_only = True
            i += 1
        else:
            i += 1
    
    if specific_dates:
        dates = specific_dates
    else:
        dates = []
        d = start_date
        while d <= end_date:
            dates.append(d.strftime('%Y-%m-%d'))
            d += timedelta(days=1)
    
    log('START', '批量历史数据处理')
    log('CONFIG', '日期: {} ~ {} ({} 天)'.format(dates[0], dates[-1], len(dates)))
    log('CONFIG', '模式: {}'.format('仅反馈' if feedback_only else 'pipeline+feedback'))
    
    # 预检查
    print('')
    for date_str in dates:
        r = '有报告' if has_reports(date_str) else '无报告'
        s = '有赛果' if has_results(date_str) else '缺赛果'
        print('  {} | {} | {}'.format(date_str, r, s))
    print('')
    
    # 执行
    success_count = 0
    for i, date_str in enumerate(dates):
        print('')
        if process_date(date_str, feedback_only):
            success_count += 1
        if (i + 1) % 5 == 0:
            log('PROGRESS', '{}/{} 完成'.format(i+1, len(dates)))
    
    log('DONE', '完成: {}/{}'.format(success_count, len(dates)))

if __name__ == '__main__':
    main()
