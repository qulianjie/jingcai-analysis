# -*- coding: utf-8 -*-
"""
历史数据全量重跑 - 2026-04-01 至 2026-04-28
用法: python batch_full.py
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

# ===== 工作区锁：防止多session冲突 =====
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

def clean_date_dir(date_str):
    """清空某天的tasks目录（保证重跑）"""
    task_dir = os.path.join(TASKS_DIR, date_str)
    if os.path.exists(task_dir):
        import shutil
        shutil.rmtree(task_dir)
        log('CLEAN', '已清空 {}'.format(date_str))

def main():
    # 获取锁
    log('LOCK', '尝试获取 batch 锁...')
    if not _acquire_lock('batch'):
        log('LOCK', 'batch 锁已被占用，退出')
        sys.exit(1)
    log('LOCK', 'OK 已获取 batch 锁')
    
    try:
        start = datetime(2026, 4, 1)
        end = datetime(2026, 4, 28)
        
        dates = []
        d = start
        while d <= end:
            dates.append(d.strftime('%Y-%m-%d'))
            d += timedelta(days=1)
        
        log('START', '历史数据全量重跑: {} ~ {} ({} 天)'.format(dates[0], dates[-1], len(dates)))
        
        # ============ Phase 1: 跑Pipeline ============
        print('\n' + '='*60)
        log('PHASE', 'Phase 1: Pipeline 生成报告')
        print('='*60 + '\n')
        
        pipeline_success = []
        for i, date_str in enumerate(dates):
            log('DATE', '({}/{}) {}'.format(i+1, len(dates), date_str))
            
            # 清空旧数据
            clean_date_dir(date_str)
            
            # Step0: 获取比赛列表
            ok = run([
                sys.executable, os.path.join(SCRIPT_DIR, 'step0_fetch_matches.py'),
                '--date', date_str, '--output-dir', TASKS_DIR
            ], timeout=60, label='[S0] ')
            if not ok:
                log('SKIP', '{} 获取比赛列表失败'.format(date_str))
                time.sleep(5)
                continue
            
            time.sleep(2)
            
            # Pipeline: 生成报告
            ok = run([
                sys.executable, os.path.join(SCRIPT_DIR, 'run_pipeline.py'), date_str
            ], timeout=1800, label='[PIPE] ')
            
            if ok:
                log('OK', '{} 流水线完成'.format(date_str))
                pipeline_success.append(date_str)
            else:
                log('WARN', '{} 流水线异常'.format(date_str))
            
            time.sleep(5)
        
        log('PHASE', 'Phase 1 完成: {}/{} 成功'.format(len(pipeline_success), len(dates)))
        
        # ============ Phase 2: 拉取赛果 ============
        print('\n' + '='*60)
        log('PHASE', 'Phase 2: 拉取赛果')
        print('='*60 + '\n')
        
        for date_str in pipeline_success:
            log('DATE', '拉取 {} 赛果'.format(date_str))
            run([
                sys.executable, os.path.join(SCRIPT_DIR, 'fetch_results.py'),
                '--date', date_str
            ], timeout=30, label='[RES] ')
            time.sleep(2)
        
        log('PHASE', 'Phase 2 完成')
        
        # ============ Phase 3: 反馈学习 ============
        print('\n' + '='*60)
        log('PHASE', 'Phase 3: 反馈学习')
        print('='*60 + '\n')
        
        feedback_success = []
        for date_str in pipeline_success:
            # 检查是否有赛果
            rf = os.path.join(SCRIPT_DIR, 'results_{}.json'.format(date_str))
            if not os.path.exists(rf):
                log('SKIP', '{} 无赛果，跳过反馈'.format(date_str))
                continue
            
            log('DATE', '反馈 {}'.format(date_str))
            ok = run([
                sys.executable, os.path.join(SCRIPT_DIR, 'batch_feedback.py'),
                '--dates', date_str
            ], timeout=60, label='[FB] ')
            
            if ok:
                feedback_success.append(date_str)
                log('OK', '{} 反馈完成'.format(date_str))
            else:
                log('WARN', '{} 反馈异常'.format(date_str))
            
            time.sleep(2)
        
        log('PHASE', 'Phase 3 完成: {}/{} 反馈成功'.format(len(feedback_success), len(pipeline_success)))
        
        # ============ Phase 4: 规律发现 ============
        print('\n' + '='*60)
        log('PHASE', 'Phase 4: 规律发现')
        print('='*60 + '\n')
        
        run([
            sys.executable, os.path.join(SCRIPT_DIR, 'pattern_miner.py')
        ], timeout=120, label='[MINER] ')
        
        # ============ Summary ============
        print('\n' + '='*60)
        log('SUMMARY', '全部完成')
        log('SUMMARY', 'Pipeline 成功: {} 天'.format(len(pipeline_success)))
        log('SUMMARY', '反馈成功: {} 天'.format(len(feedback_success)))
        print('='*60)
    
    finally:
        _release_lock('batch')
        log('LOCK', '已释放 batch 锁')

if __name__ == '__main__':
    main()
