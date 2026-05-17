# -*- coding: utf-8 -*-
"""并行竞彩流水线 - 同时跑多场比赛，大幅提速

用法:
    python run_parallel.py                        # 跑今天所有未完成的比赛
    python run_parallel.py 2026-05-17             # 跑指定日期
    python run_parallel.py --workers 10           # 指定并行数（默认8）
    python run_parallel.py --sequential           # 跑完所有赛后执行 step25/26+report
"""
import os, sys, json, re, time, subprocess, threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')

def log(tag, msg):
    t = datetime.now().strftime('%H:%M:%S')
    plain_msg = str(msg).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    print('[{}] [{}] {}'.format(t, tag, plain_msg))
    sys.stdout.flush()

def run_script(script_name, args, timeout=3600):
    script_path = os.path.join(SCRIPT_DIR, script_name)
    if not os.path.exists(script_path):
        log('ERROR', 'script not exist: {}'.format(script_name))
        return False
    cmd = [sys.executable, script_path] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            if result.stderr:
                log('STDERR', result.stderr[:300])
            return False
        return True
    except subprocess.TimeoutExpired:
        log('TIMEOUT', '{} timeout after {}s'.format(script_name, timeout))
        return False
    except Exception as e:
        log('EXCEPT', '{}: {}'.format(script_name, e))
        return False

def run_one_match(match_info, date_str, match_idx):
    """Run one match through all steps"""
    home = match_info.get('home', '')
    away = match_info.get('away', '')
    match_num = str(match_info.get('matchnum', str(match_idx+1)))
    
    log('START', '[{}] {} vs {}'.format(match_num, home, away))
    
    data_dir = os.path.join(TASKS_DIR, date_str, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    match_dir_name = 'match{}_{}__{}'.format(match_num, home, away)
    match_dir = os.path.join(data_dir, match_dir_name)
    os.makedirs(match_dir, exist_ok=True)
    
    meta = {
        'matchnum': match_num,
        'match': '{} {} vs {}'.format(match_num, home, away),
        'fid': match_info.get('fid', ''),
        'league': match_info.get('league', ''),
        'home': home,
        'away': away,
        'date': date_str,
        'status': 'in_progress',
        'home_id': match_info.get('home_id', ''),
        'away_id': match_info.get('away_id', ''),
        'rq': match_info.get('rq', ''),
        'macau_line': match_info.get('macau_line', ''),
    }
    with open(os.path.join(match_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    steps = [
        ('step146_extractor.py', [match_dir]),
        ('step235_runner.py', [match_dir]),
        # step7_runner.py is run SEPARATELY after all parallel steps (browser single-instance)
        ('step8_1923_extractor.py', [match_dir]),
        ('step918_extractor.py', [match_dir]),
        ('step24_extractor.py', [match_dir]),
    ]
    
    for script, args in steps:
        tname = script.split('.')[0]
        start_t = time.time()
        log('STEP', '[{}] {} vs {} -> {}'.format(match_num, home, away, tname))
        t = 3600*2 if script == 'step8_1923_extractor.py' else 3600
        ok = run_script(script, args, timeout=t)
        elapsed = int(time.time() - start_t)
        if not ok:
            log('FAIL', '[{}] {} vs {} step {} FAIL ({:.0f}s)'.format(match_num, home, away, tname, elapsed))
            return False
        log('STEPOK', '[{}] {} step {} ({:.0f}s)'.format(match_num, home, away, elapsed))
        time.sleep(0.5)
    
    # Verify
    try:
        from run_pipeline import verify_match_data
        passed, issues = verify_match_data(match_dir, home, away)
        log('DONE', '[{}] {} vs {} DONE (issues:{})'.format(match_num, home, away, len(issues)))
    except:
        log('DONE', '[{}] {} vs {} DONE'.format(match_num, home, away))
    
    return True

def run_parallel_pipeline(date_str, num_workers=8):
    matches_json = os.path.join(TASKS_DIR, date_str, 'matches_data.json')
    with open(matches_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_matches = []
    if 'groups' in data:
        for g in sorted(data['groups'].keys()):
            gm = data['groups'][g].get('matches', [])
            all_matches.extend(gm)
    elif isinstance(data, list):
        all_matches = data
    elif 'matches' in data:
        all_matches = data['matches']
    
    if not all_matches:
        log('ERROR', 'No matches found')
        return
    
    log('INFO', 'Total {} matches, {} workers'.format(len(all_matches), num_workers))
    
    # Check which are already done
    data_dir = os.path.join(TASKS_DIR, date_str, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    pending = []
    for i, m in enumerate(all_matches):
        mn = str(m.get('matchnum', ''))
        fid = str(m.get('fid', ''))
        found = False
        if os.path.exists(data_dir):
            for d in sorted(os.listdir(data_dir), reverse=True):
                if d.startswith('match'):
                    fp = os.path.join(data_dir, d, 'step24_panlu_match.json')
                    if os.path.exists(fp) and os.path.getsize(fp) > 100:
                        mp = os.path.join(data_dir, d, 'meta.json')
                        if os.path.exists(mp):
                            with open(mp, 'r', encoding='utf-8') as mf:
                                mm = json.load(mf)
                            if mn and mm.get('matchnum') == mn:
                                found = True
                                break
                            if fid and mm.get('fid') == fid:
                                found = True
                                break
        if not found:
            pending.append((i, m))
    
    log('INFO', '{} done, {} remaining'.format(len(all_matches)-len(pending), len(pending)))
    
    if not pending:
        log('INFO', 'All done, skipping parallel phase')
        return True, True
    
    actual_workers = min(num_workers, len(pending))
    log('INFO', 'Starting {} workers...'.format(actual_workers))
    
    ok_count = 0
    fail_count = 0
    
    with ThreadPoolExecutor(max_workers=actual_workers) as executor:
        futures = {}
        for idx, m in pending:
            mn = str(m.get('matchnum', str(idx+1)))
            log('QUEUE', '[{}] {} vs {}'.format(mn, m.get('home',''), m.get('away','')))
            fut = executor.submit(run_one_match, m, date_str, idx)
            futures[fut] = mn
        
        for fut in as_completed(futures):
            mn = futures[fut]
            try:
                ok = fut.result()
                if ok:
                    ok_count += 1
                else:
                    fail_count += 1
                log('FINISH', '[{}] status={} ({:.0f} / {:.0f})'.format(mn, 'OK' if ok else 'FAIL', ok_count, fail_count))
            except Exception as e:
                fail_count += 1
                log('ERROR', '[{}] exception: {}'.format(mn, e))
    
    log('SUMMARY', 'OK={}, FAIL={}, Total={}'.format(ok_count, fail_count, ok_count+fail_count))
    
    # ============ PHASE 2: Step 7 - serial (agent-browser is single-instance) ============
    log('PHASE2', 'Step 7 - serial (agent-browser single-instance)...')
    s7_ok = 0
    s7_fail = 0
    for idx, m in pending:
        home = m.get('home', '')
        away = m.get('away', '')
        mn = str(m.get('matchnum', str(idx+1)))
        match_dir_name = 'match{}_{}__{}'.format(mn, home, away)
        match_dir = os.path.join(data_dir, match_dir_name)
        
        s7path = os.path.join(match_dir, 'group03_asian', 'step7_macau_same.txt')
        if os.path.exists(s7path) and os.path.getsize(s7path) > 1000:
            log('S7SKIP', '[{}] step7 already done ({}B)'.format(mn, os.path.getsize(s7path)))
            s7_ok += 1
            continue
        
        log('S7', '[{}] {} vs {} -> step7'.format(mn, home, away))
        ok = run_script('step7_runner.py', [match_dir], timeout=3600)
        if ok:
            s7_ok += 1
            log('S7OK', '[{}] {} vs {} step7 DONE'.format(mn, home, away))
        else:
            s7_fail += 1
            log('S7FAIL', '[{}] {} vs {} step7 FAIL'.format(mn, home, away))
        time.sleep(3)
    
    log('PHASE2_DONE', 'Step7: OK={}, FAIL={}'.format(s7_ok, s7_fail))
    
    return ok_count > 0, fail_count == 0

def main():
    date_str = datetime.now().strftime('%Y-%m-%d')
    num_workers = 8
    run_sequential = False
    
    if len(sys.argv) > 1:
        args_rest = sys.argv[1:]
        for i, a in enumerate(args_rest):
            if a.startswith('--workers='):
                num_workers = int(a.split('=')[1])
            elif a == '--sequential':
                run_sequential = True
            elif a == '--workers' and i+1 < len(args_rest):
                num_workers = int(args_rest[i+1])
            elif re.match(r'\d{4}-\d{2}-\d{2}', a):
                date_str = a
    
    log('START', 'Parallel pipeline: {} ({} workers)'.format(date_str, num_workers))
    run_parallel_pipeline(date_str, num_workers=num_workers)
    
    if run_sequential:
        log('PHASE2', 'All matches done, running batch steps...')
        run_script('step25_zhuangjia.py', [date_str], timeout=3600)
        run_script('step26_profit_ratio.py', [date_str], timeout=3600)
        
        task_dir = os.path.join(TASKS_DIR, date_str)
        data_dir = os.path.join(task_dir, 'data')
        if os.path.exists(data_dir):
            for d in sorted(os.listdir(data_dir)):
                if d.startswith('match') and os.path.isdir(os.path.join(data_dir, d)):
                    match_dir = os.path.join(data_dir, d)
                    meta_file = os.path.join(match_dir, 'meta.json')
                    if not os.path.exists(meta_file):
                        continue
                    with open(meta_file, 'r', encoding='utf-8') as mf:
                        meta_data = json.load(mf)
                    mn = meta_data.get('matchnum', '')
                    ho = meta_data.get('home', '')
                    aw = meta_data.get('away', '')
                    if not (mn and ho and aw):
                        continue
                    rname = '{}_{}vs{}'.format(mn, ho, aw)
                    rpath = os.path.join(task_dir, '{}.md'.format(rname))
                    log('REPORT', '{} {} vs {}'.format(mn, ho, aw))
                    run_script('final_report_generator.py', [match_dir, rpath], timeout=3600)
        
        log('COMPLETE', 'All done! Date: {}'.format(date_str))

if __name__ == '__main__':
    main()
