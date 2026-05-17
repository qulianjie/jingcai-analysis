#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""5月10日全流程补跑：step25 + step26 + 报告生成 + Notion同步"""
import os, sys, subprocess, time, json, glob

SCRIPT_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
DATE = '2026-05-10'
MATCH_ROOT = os.path.join(SCRIPT_DIR, 'tasks', DATE)
DATA_DIR = os.path.join(MATCH_ROOT, 'data')
LOG_PATH = os.path.join(SCRIPT_DIR, 'patch_0510_progress.txt')

def log(msg):
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')
    print(msg)

def run_python(script, args, timeout=1800):
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, script)] + args
    log('  RUN: {} {}'.format(script, ' '.join(args)))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                                encoding='utf-8', errors='replace')
        if result.returncode != 0:
            log('  FAIL rc={}'.format(result.returncode))
            if result.stderr:
                log('  STDERR: {}'.format(result.stderr[:300]))
            if result.stdout:
                log('  STDOUT: {}'.format(result.stdout[:200]))
            return False
        log('  OK')
        return True
    except subprocess.TimeoutExpired:
        log('  TIMEOUT after {}s'.format(timeout))
        return False
    except Exception as e:
        log('  ERROR: {}'.format(e))
        return False

# 清除旧日志
if os.path.isfile(LOG_PATH):
    os.remove(LOG_PATH)

log('=== 5月10日全流程补跑开始 ===')
log('数据目录: {}'.format(DATA_DIR))

# 查找所有task
tasks = sorted([os.path.basename(d.rstrip('\\')) for d in glob.glob(DATA_DIR + '\\match*\\')])
log('Tasks: {}'.format(len(tasks)))

# ===== 1. 检查已有的step24 =====
has24 = sum(1 for t in tasks if os.path.isfile(os.path.join(DATA_DIR, t, 'step24_panlu_match.json')))
log('Step24: {}/{} already exist'.format(has24, len(tasks)))

# ===== 2. Step25 =====
log('\n=== Step 25: 庄家盈亏分析 ===')
if not run_python('step25_zhuangjia.py', [DATE]):
    log('Step25 FAILED - continuing anyway')

# 检查结果
has25 = sum(1 for t in tasks if os.path.isfile(os.path.join(DATA_DIR, t, 'step25_zhuangjia.json')))
log('Step25 result: {}/{}'.format(has25, len(tasks)))

# ===== 3. Step26 =====
log('\n=== Step 26: 盈利比例分析 ===')
if not run_python('step26_profit_ratio.py', [DATE]):
    log('Step26 FAILED - continuing anyway')

has26 = sum(1 for t in tasks if os.path.isfile(os.path.join(DATA_DIR, t, 'step26_profit_ratio.json')))
log('Step26 result: {}/{}'.format(has26, len(tasks)))

# ===== 4. 生成报告 =====
log('\n=== 生成最终报告 ===')
report_count = 0
for t in tasks:
    tdir = os.path.join(DATA_DIR, t)
    meta_path = os.path.join(tdir, 'meta.json')
    if not os.path.isfile(meta_path):
        log('  SKIP {}: no meta.json'.format(t[:40]))
        continue
    with open(meta_path, encoding='utf-8') as f:
        meta = json.load(f)
    
    match_num = meta.get('matchnum', '')
    home = meta.get('home', '')
    away = meta.get('away', '')
    if not match_num or not home or not away:
        log('  SKIP {}: incomplete meta'.format(t[:40]))
        continue
    
    report_name = '{}_{}vs{}'.format(match_num, home, away)
    report_path = os.path.join(MATCH_ROOT, '{}.md'.format(report_name))
    
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPT_DIR, 'final_report_generator.py'), tdir, report_path],
        capture_output=True, text=True, timeout=300, encoding='utf-8', errors='replace'
    )
    if result.returncode == 0 and os.path.isfile(report_path):
        sz = os.path.getsize(report_path)
        report_count += 1
        log('  OK {}: {}B'.format(report_name[:45], sz))
    else:
        log('  FAIL {}: rc={}'.format(report_name[:45], result.returncode))
        if result.stderr:
            log('    {}'.format(result.stderr[:200]))
    time.sleep(0.3)

log('\nReports: {}/{} generated'.format(report_count, len(tasks)))

# ===== 5. Notion同步 =====
log('\n=== 同步到Notion ===')
if not run_python('sync_notion_wrapper.py', ['add', DATE], timeout=1800):
    log('Notion sync FAILED')

log('\n=== 全部完成 ===')
