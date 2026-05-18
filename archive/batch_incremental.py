# -*- coding: utf-8 -*-
"""
增量重跑 - 只跑未完成的场次
用法: python batch_incremental.py
"""
import os, sys, json, time, subprocess
from datetime import datetime

import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')

def log(tag, msg):
    t = datetime.now().strftime('%H:%M:%S')
    msg = str(msg).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    print('[{}] [{}] {}'.format(t, tag, msg))
    sys.stdout.flush()

def run(cmd, timeout=600, label=''):
    log('RUN', '{}{}'.format(label, ' '.join(cmd[-3:])))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=timeout)
        if result.returncode != 0:
            for line in (result.stderr or '').strip().split('\n')[-3:]:
                log('ERR', line.strip())
            return False
        return True
    except subprocess.TimeoutExpired:
        log('ERR', '超时({}s)'.format(timeout))
        return False
    except Exception as e:
        log('ERR', str(e))
        return False

# ===== 工作区锁 =====
def _acquire_lock(name):
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, 'protect.py'), 'lock', name],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0
    except:
        return False

def _release_lock(name):
    try:
        subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, 'protect.py'), 'unlock', name],
            capture_output=True, text=True, timeout=10
        )
    except:
        pass

def check_match_completed(task_dir, match_dir_name):
    """检查单场比赛是否已完成"""
    # Check if report exists
    report_name = match_dir_name.replace('_', '')
    report_path = os.path.join(task_dir, '{}.md'.format(report_name))
    if os.path.exists(report_path):
        return True
    
    # Check if step24 output exists
    data_dir = os.path.join(task_dir, 'data', match_dir_name)
    if os.path.exists(os.path.join(data_dir, 'step24_output.txt')):
        return True
    
    return False

def get_pending_matches():
    """获取所有未完成的场次"""
    pending = []
    
    if not os.path.exists(TASKS_DIR):
        return pending
    
    dates = sorted([d for d in os.listdir(TASKS_DIR) 
                    if os.path.isdir(os.path.join(TASKS_DIR, d)) and d.count('-') == 2])
    
    for date_str in dates:
        task_dir = os.path.join(TASKS_DIR, date_str)
        data_dir = os.path.join(task_dir, 'data')
        
        if not os.path.exists(data_dir):
            continue
        
        matches = sorted([d for d in os.listdir(data_dir) 
                         if d.startswith('match') and os.path.isdir(os.path.join(data_dir, d))])
        
        for m in matches:
            if not check_match_completed(task_dir, m):
                pending.append((date_str, m))
    
    return pending

def reprocess_match(date_str, match_dir_name):
    """重新处理单场比赛"""
    data_dir = os.path.join(TASKS_DIR, date_str, 'data')
    match_dir = os.path.join(data_dir, match_dir_name)
    
    # Extract match number from dir name (e.g., match001__xxx)
    match_num = match_dir_name.split('__')[0].replace('match', '')
    
    log('REPROCESS', '{} {}'.format(date_str, match_dir_name))
    
    # Run pipeline steps
    steps = [
        (['python', os.path.join(SCRIPT_DIR, 'step146_extractor.py'), match_dir], 'S146'),
        (['python', os.path.join(SCRIPT_DIR, 'step235_runner.py'), match_dir], 'S235'),
        (['python', os.path.join(SCRIPT_DIR, 'step7_runner.py'), match_dir], 'S7'),
        (['python', os.path.join(SCRIPT_DIR, 'step8_1923_extractor.py'), match_dir], 'S8'),
        (['python', os.path.join(SCRIPT_DIR, 'step918_extractor.py'), match_dir], 'S918'),
        (['python', os.path.join(SCRIPT_DIR, 'step24_extractor.py'), match_dir], 'S24'),
        (['python', os.path.join(SCRIPT_DIR, 'final_report_generator.py'), match_dir], 'REPORT'),
    ]
    
    for cmd, label in steps:
        ok = run(cmd, timeout=300, label='[{}] '.format(label))
        if not ok:
            log('FAIL', '{} 失败'.format(label))
            return False
        time.sleep(2)
    
    return True

def main():
    # 获取锁
    log('LOCK', '尝试获取 batch 锁...')
    if not _acquire_lock('batch'):
        log('LOCK', 'batch 锁已被占用，退出')
        sys.exit(1)
    log('LOCK', 'OK 已获取 batch 锁')
    
    try:
        # Get pending matches
        pending = get_pending_matches()
        
        if not pending:
            log('INFO', '没有未完成的场次')
            return
        
        log('START', '增量重跑: {} 场未完成'.format(len(pending)))
        
        success = 0
        for i, (date_str, match_dir_name) in enumerate(pending):
            log('MATCH', '({}/{}) {} {}'.format(i+1, len(pending), date_str, match_dir_name))
            
            if reprocess_match(date_str, match_dir_name):
                success += 1
                log('OK', '{} 完成'.format(match_dir_name))
            else:
                log('FAIL', '{} 失败'.format(match_dir_name))
            
            time.sleep(3)
        
        # ============ Summary ============
        print('\n' + '='*60)
        log('SUMMARY', '全部完成')
        log('SUMMARY', '成功: {} 场'.format(success))
        log('SUMMARY', '失败: {} 场'.format(len(pending) - success))
        print('='*60)
    
    finally:
        _release_lock('batch')
        log('LOCK', '已释放 batch 锁')

if __name__ == '__main__':
    main()
