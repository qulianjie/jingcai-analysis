# -*- coding: utf-8 -*-
"""竞彩24步全自动流水线 - 一键生成所有比赛的最终报告

用法:
    python run_pipeline.py                    # 分析今天所有未开赛比赛
    python run_pipeline.py 2026-04-29         # 分析指定日期
    python run_pipeline.py 001                # 分析今日第001场
    python run_pipeline.py all                # 分析今日所有场次(包括已开赛)
"""
import os, sys, json, re, time, subprocess, shutil, argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')
ROOT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # jingcai root
CACHE_DIR = os.path.join(ROOT_DIR, "data", "league_cache")  # 全局联赛缓存

sys.path.insert(0, SCRIPT_DIR)
from _verify_util import verify_all_steps, verify_checklist_summary

def log(tag, msg):
    t = datetime.now().strftime('%H:%M:%S')
    msg = str(msg).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    print('[{}] [{}] {}'.format(t, tag, msg))

def run_script(script_name, args, timeout=300):
    script_path = os.path.join(SCRIPT_DIR, script_name)
    if not os.path.exists(script_path):
        log('ERROR', '脚本不存在: {}'.format(script_name))
        return False
    cmd = [sys.executable, script_path] + args
    log('RUN', 'python {} {}'.format(script_name, ' '.join(str(a) for a in args)))
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        if result.stdout:
            for line in result.stdout.decode('utf-8', errors='replace').strip().split('\n')[-5:]:
                log('OUT', line)
        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="replace").strip().split('\n')[-1] if result.stderr else 'unknown error'
            log('ERR', err)
            return False
        return True
    except subprocess.TimeoutExpired:
        log('ERR', '超时({}s)'.format(timeout))
        return False

def move_file(src, dst):
    if not os.path.exists(src):
        return False
    dst_dir = os.path.dirname(dst)
    os.makedirs(dst_dir, exist_ok=True)
    try:
        if os.path.exists(dst):
            os.remove(dst)
        shutil.move(src, dst)
        return True
    except Exception as e:
        log('ERR', 'Move failed: {}'.format(e))
        return False

def copy_file(src, dst):
    if not os.path.exists(src):
        return False
    dst_dir = os.path.dirname(dst)
    os.makedirs(dst_dir, exist_ok=True)
    try:
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        log('ERR', 'Copy failed: {}'.format(e))
        return False

def fetch_matches(date_str):
    log('STEP0', '获取{}竞彩列表'.format(date_str))
    if not run_script('step0_fetch_matches.py', ['--date', date_str, '--output-dir', TASKS_DIR]):
        log('ERROR', '获取比赛列表失败')
        return []

    matches_file = os.path.join(TASKS_DIR, date_str, 'matches_data.json')
    if not os.path.exists(matches_file):
        log('ERROR', 'matches_data.json未找到')
        return []

    with open(matches_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_matches = []
    groups = data.get('groups', {})
    if isinstance(groups, dict):
        for gname, gdata in groups.items():
            if isinstance(gdata, dict) and 'matches' in gdata:
                all_matches.extend(gdata['matches'])
    elif isinstance(groups, list):
        all_matches = groups

    return all_matches

def get_match_dir(task_dir, match_num):
    for d in os.listdir(task_dir):
        if d.startswith('match{}'.format(match_num)) or 'match{}'.format(match_num) in d:
            dp = os.path.join(task_dir, d)
            if os.path.isdir(dp):
                return dp, d
    return None, None

def run_match_pipeline(match, date_str, match_index):
    match_num = match.get('matchnum', '{:03d}'.format(match_index))
    match_num_clean = re.search(r'(\d+)', match_num)
    fid = str(match.get('fid', ''))
    league = match.get('league', '')
    home = match.get('home', '')
    away = match.get('away', '')

    task_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.exists(task_dir):
        os.makedirs(task_dir)

    match_dir, dir_name = get_match_dir(task_dir, match_num_clean.group() if match_num_clean else '')
    if not match_dir:
        home_en = home.replace('vs', '_').replace(' ', '_')
        away_en = away.replace(' ', '_')
        dir_name = 'match{}{}_{}_{}'.format(
            match_num_clean.group() if match_num_clean else match_index,
            '_', home_en, away_en)
        match_dir = os.path.join(task_dir, dir_name)
        os.makedirs(match_dir, exist_ok=True)

        for g in ['group01_europe', 'group02_handicap', 'group03_asian',
                  'group04_teamA', 'group05_teamB', 'group06_baijia']:
            os.makedirs(os.path.join(match_dir, g), exist_ok=True)

        meta = {
            'matchnum': match_num,
            'match': '{}_{}vs{}'.format(match_num, home, away),
            'fid': fid,
            'league': league,
            'home': home,
            'away': away,
            'date': date_str,
            'rq': match.get('rq', ''),
            'status': 'running'
        }
        with open(os.path.join(match_dir, 'meta.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    else:
        log('INFO', '使用已有目录: {}'.format(dir_name))

    # 检查已完成步骤
    completed = check_completed(match_dir)
    start_from = 1
    if completed >= 8:
        log('SKIP', '{} 已完成全部步骤'.format(match_num))
        return True
    elif completed > 0:
        log('RESUME', '{} 从第{}步继续'.format(match_num, completed+1))
        start_from = completed + 1

    # 中间文件路径
    tmp_s24 = os.path.join(match_dir, 'step24_output.txt')
    meta_path = os.path.join(match_dir, 'meta.json')

    # 从meta.json读取（断点续跑）
    home_id = away_id = macau_line = ''
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        home_id = meta.get('home_id', '')
        away_id = meta.get('away_id', '')
        macau_line = meta.get('macau_line', '')

    # 如果没有，调用extract_team_info提取（写入文件，避免stdout编码问题）
    if not home_id or not macau_line:
        log('EXTRACT', '提取队ID和澳门盘口')
        team_info_file = os.path.join(match_dir, 'team_info.json')
        try:
            script_path = os.path.join(ROOT_DIR, 'extract_team_info.py')
            result = subprocess.run([sys.executable, script_path, fid, league, team_info_file],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            if os.path.exists(team_info_file):
                with open(team_info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                home_id = info.get('home_id', '')
                away_id = info.get('away_id', '')
                macau_line = info.get('macau_line', '')
                log('INFO', 'home_id={} away_id={} macau_line={}'.format(home_id, away_id, macau_line))
                if os.path.exists(meta_path):
                    with open(meta_path, 'r', encoding='utf-8') as mf:
                        meta = json.load(mf)
                    meta['home_id'] = home_id
                    meta['away_id'] = away_id
                    meta['macau_line'] = macau_line
                    with open(meta_path, 'w', encoding='utf-8') as mf:
                        json.dump(meta, mf, ensure_ascii=False, indent=2)
        except Exception as e:
            log('WARN', '提取队信息失败: {}'.format(e))
    else:
        log('INFO', '从meta读取: home_id={} away_id={} macau_line={}'.format(home_id, away_id, macau_line))

    # 脚本接口
    # step1/4/6合并为一次调用，直接输出到目标路径
    # step2/3/5/7合并为一次调用，直接输出到目标路径
    s1_out = os.path.join(match_dir, 'group01_europe', 'step01_europe_basic.md')
    s4_out = os.path.join(match_dir, 'group02_handicap', 'step04_handicap_basic.md')
    s6_out = os.path.join(match_dir, 'group03_asian', 'step06_asian_basic.md')
    s2_out = os.path.join(match_dir, 'group01_europe', 'step02_jingcai_same.md')
    s3_out = os.path.join(match_dir, 'group01_europe', 'step03_interwetten_same.md')
    s5_out = os.path.join(match_dir, 'group02_handicap', 'step05_handicap_same.md')
    s7_out = os.path.join(match_dir, 'group03_asian', 'step07_macau_same.md')

    steps = [
        (1, '欧赔+让球+亚盘(1+4+6)', 'step146_extractor.py', [fid, league, s1_out, s4_out, s6_out]),
        (2, '同赔(2+3+5)', 'step235_runner.py', [fid, league, s2_out, s3_out, s5_out]),
        (7, '澳门亚盘同赔(7)', 'step7_runner.py', [fid, league, s7_out]),
        (8, '同联赛+百家(8,19-23)', 'step8_1923_extractor.py', [home_id, away_id, league, fid, macau_line,
            os.path.join(match_dir, 'group03_asian', 'step08_same_league.md'),
            os.path.join(match_dir, 'group06_baijia', 'step19_23_baijia.md')]),
        (9, '主客队(9-18)', 'step918_extractor.py', [home_id, away_id, league, fid, macau_line, match_dir,
            os.path.join(match_dir, 'group04_teamA', 'step09_13_teamA.md'),
            os.path.join(match_dir, 'group05_teamB', 'step14_18_teamB.md')]),
        (10, '盘路匹配(24)', 'step24_extractor.py', [home_id, away_id, league, fid, tmp_s24]),
    ]

    for step_num, desc, script, script_args in steps:
        if step_num < start_from:
            continue
        log('STEP', '{} - {}'.format(match_num, desc))
        success = run_script(script, script_args, timeout=600)
        if not success:
            log('WARN', '{} 失败，继续下一步'.format(desc))
            time.sleep(2)

        if step_num == 1:
            # step1/4/6 directly writes to target paths, no move needed
            pass
        elif step_num == 2:
            # step2/3/5/7 merged into step2357_runner.py, all files written directly to target paths
            # step02 -> group01_europe, step03 -> group01_europe
            # step05 -> group02_handicap, step07 -> group03_asian
            pass
        elif step_num == 8:
            # step8_1923_extractor.py now writes directly to target paths (group03 and group06)
            pass
        elif step_num == 9:
            # step918 now writes directly to target paths (group04 and group05)
            pass
        elif step_num == 10:
            move_file(tmp_s24, os.path.join(match_dir, 'step24_panlu_match.json'))

    # 生成最终报告
    log('REPORT', '生成{}最终报告'.format(match_num))
    run_script('final_report_generator.py', [match_dir], timeout=120)

    # 更新状态
    meta_path = os.path.join(match_dir, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        meta['status'] = 'completed'
        meta['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    return True

def check_completed(match_dir):
    """检查已完成的步骤 - 检查关键文件是否存在且非空"""
    group_checks = [
        ['group01_europe', ['step01_europe_basic.md', 'step02_jingcai_same.md', 'step03_interwetten_same.md']],
        ['group02_handicap', ['step04_handicap_basic.md', 'step05_handicap_same.md']],
        ['group03_asian', ['step06_asian_basic.md', 'step07_macau_same.md', 'step08_same_league.md']],
        ['group06_baijia', ['step19_23_baijia.md']],
    ]
    completed = 0

    for group, expected_files in group_checks:
        gp = os.path.join(match_dir, group)
        if os.path.isdir(gp):
            has_content = False
            for ef in expected_files:
                fp = os.path.join(gp, ef)
                if os.path.isfile(fp) and os.path.getsize(fp) > 100:
                    has_content = True
                    break
            if has_content:
                completed += 1

    s918_home = os.path.join(match_dir, 'group04_teamA', 'step09_13_teamA.md')
    s918_away = os.path.join(match_dir, 'group05_teamB', 'step14_18_teamB.md')
    if (os.path.isfile(s918_home) and os.path.getsize(s918_home) > 100) or \
       (os.path.isfile(s918_away) and os.path.getsize(s918_away) > 100):
        completed += 1

    if completed >= 5:
        completed = 20
    else:
        completed = completed * 4

    s24 = os.path.join(match_dir, 'step24_panlu_match.json')
    if os.path.exists(s24) and os.path.getsize(s24) > 100:
        completed = 24

    s25 = os.path.join(match_dir, 'step25_zhuangjia.json')
    if os.path.exists(s25) and os.path.getsize(s25) > 100:
        completed = 25

    report = os.path.join(match_dir, 'final_report.md')
    if os.path.exists(report) and os.path.getsize(report) > 5000:
        completed = 26

    return completed

def organize_data(date_str):
    task_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.exists(task_dir):
        return

    data_dir = os.path.join(task_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # 白名单：不移动的文件/目录（保护 feedback 输出）
    protected_names = {
        'data',           # 数据目录本身
        'feedback',       # feedback 输出目录（如果有）
    }

    def is_protected(name):
        # 保护最终报告（周X001_xxx.md）
        if name.endswith('.md') and re.search(r'周[一二三四五六日]\d+_', name):
            return True
        # 保护 feedback 输出文件
        if name.startswith('feedback_') and name.endswith('.txt'):
            return True
        # 保护 results 文件
        if name.startswith('results_') and name.endswith('.json'):
            return True
        # 保护精确匹配的目录/文件
        if name in protected_names:
            return True
        return False

    for f in sorted(os.listdir(task_dir)):
        if is_protected(f):
            continue
        fp = os.path.join(task_dir, f)
        dest = os.path.join(data_dir, f)
        try:
            if os.path.isdir(fp) and os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.move(fp, dest)
        except Exception as e:
            log('ERR', 'Move failed {}: {}'.format(f, e))


def expand_match_filter(match_expr):
    if not match_expr:
        return None
    match_expr = match_expr.strip()
    if match_expr in ('all', '全部'):
        return None
    range_m = re.match(r'(\d+)\s*\-\s*(\d+)$', match_expr)
    if range_m:
        start, end = int(range_m.group(1)), int(range_m.group(2))
        return set('{:03d}'.format(i) for i in range(start, end + 1))
    if ',' in match_expr:
        nums = re.findall(r'\\d+', match_expr)
        return set(n.zfill(3) for n in nums)
    nums = re.findall(r'\\d+', match_expr)
    if nums:
        return {nums[0].zfill(3)}
    return {match_expr}


def fetch_matches(date_str):
    log('STEP0', '获取{}竞彩列表'.format(date_str))
    if not run_script('step0_fetch_matches.py', ['--date', date_str, '--output-dir', TASKS_DIR]):
        log('ERROR', '获取比赛列表失败')
        return []
    matches_file = os.path.join(TASKS_DIR, date_str, 'matches_data.json')
    if not os.path.exists(matches_file):
        log('ERROR', 'matches_data.json未找到')
        return []
    with open(matches_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    all_matches = []
    groups = data.get('groups', {})
    if isinstance(groups, dict):
        for gname, gdata in groups.items():
            if isinstance(gdata, dict) and 'matches' in gdata:
                all_matches.extend(gdata['matches'])
    elif isinstance(groups, list):
        all_matches = groups
    return all_matches


def organize_data(date_str):
    task_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.exists(task_dir):
        return
    data_dir = os.path.join(task_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    protected_names = {'data', 'feedback'}
    def is_protected(name):
        if name.endswith('.md') and re.search(r'周[一二三四五六日]\\d+_', name):
            return True
        if name.startswith('feedback_') and name.endswith('.txt'):
            return True
        if name.startswith('results_') and name.endswith('.json'):
            return True
        if name in protected_names:
            return True
        return False
    for f in sorted(os.listdir(task_dir)):
        if is_protected(f):
            continue
        fp = os.path.join(task_dir, f)
        dest = os.path.join(data_dir, f)
        try:
            if os.path.isdir(fp) and os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.move(fp, dest)
        except Exception as e:
            log('ERR', 'Move failed {}: {}'.format(f, e))


def main():
    """Run full 24-step pipeline for today's matches"""
    log('START', '竞彩24步全自动流水线启动')
    parser = argparse.ArgumentParser(description='竞彩24步全自动流水线')
    parser.add_argument('--date', '-d', default=datetime.now().strftime('%Y-%m-%d'),
                        help='日期 yyyy-mm-dd (默认今天)')
    parser.add_argument('--match', '-m', default=None,
                        help='比赛筛选: 001 / 001-007 / 001,003,005')
    parser.add_argument('--parallel', '-p', type=int, default=1,
                        help='并行线程数 (默认1=串行)')
    parser.add_argument('--pipeline-only', action='store_true',
                        help='只跑分析，不触发汇总步骤')
    args = parser.parse_args()
    date_str = args.date
    pipeline_only = args.pipeline_only
    parallel_workers = args.parallel
    log('CONFIG', '日期: {}, parallel: {}, pipeline-only: {}'.format(
        date_str, parallel_workers, pipeline_only))
    matches = fetch_matches(date_str)
    log('PRECACHE', '联赛数据预缓存...')
    precache_py = os.path.join(ROOT_DIR, 'precache_leagues.py')
    if os.path.exists(precache_py):
        log('PRECACHE', 'python {} {}'.format(precache_py, date_str))
        subprocess.run([sys.executable, precache_py, date_str], timeout=600)
    log('CACHE', '全局联赛缓存: {}'.format(CACHE_DIR))
    if not matches:
        log('ERROR', '未找到比赛数据')
        return
    log('FOUND', '找到{}场比赛'.format(len(matches)))
    match_filter_set = expand_match_filter(args.match)
    if match_filter_set is not None:
        filtered = []
        for m in matches:
            mn = m.get('matchnum', '')
            if mn in match_filter_set:
                filtered.append(m)
            else:
                mn_clean = re.sub(r'\D', '', mn)
                if mn_clean in match_filter_set:
                    filtered.append(m)
        matches = filtered
        log('FILTER', '过滤后剩余{}场: {}'.format(len(matches),
            ', '.join(m.get('matchnum','') for m in matches)))
    if not matches:
        log('ERROR', '没有需要分析的比赛')
        return
    success_count = 0
    if parallel_workers > 1 and len(matches) > 1:
        log('PARALLEL', '使用{}线程并行执行{}场比赛'.format(parallel_workers, len(matches)))
        futures = {}
        with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
            for i, match in enumerate(matches):
                match_num = match.get('matchnum', '{:03d}'.format(i+1))
                log('SUBMIT', '提交 {} {} vs {}'.format(match_num,
                    match.get('home',''), match.get('away','')))
                future = executor.submit(run_match_pipeline, match, date_str, i+1)
                futures[future] = match_num
            for future in as_completed(futures):
                mn = futures[future]
                try:
                    if future.result():
                        success_count += 1
                        log('OK', '{} 完成'.format(mn))
                    else:
                        log('FAIL', '{} 失败'.format(mn))
                except Exception as e:
                    log('FAIL', '{} 异常: {}'.format(mn, e))
    else:
        for i, match in enumerate(matches):
            match_num = match.get('matchnum', '{:03d}'.format(i+1))
            log('MATCH', '({}/{}) {} {} vs {}'.format(i+1, len(matches),
                match_num, match.get('home',''), match.get('away','')))
            if run_match_pipeline(match, date_str, i+1):
                success_count += 1
                log('OK', '{} 完成'.format(match_num))
            else:
                log('FAIL', '{} 失败'.format(match_num))
            time.sleep(3)
    if not pipeline_only:
        log('STEP25', '庄家盈亏分析(25) - 全量处理')
        s25_path = os.path.join(ROOT_DIR, 'step25_zhuangjia.py')
        if os.path.exists(s25_path):
            subprocess.run([sys.executable, s25_path, date_str], timeout=300)
        log('REGEN', '重新生成报告（含第25步）')
        task_dir_regen = os.path.join(TASKS_DIR, date_str)
        data_dir_regen = os.path.join(task_dir_regen, 'data')
        if os.path.exists(data_dir_regen):
            for d in sorted(os.listdir(data_dir_regen)):
                if d.startswith('match') and os.path.isdir(os.path.join(data_dir_regen, d)):
                    match_dir = os.path.join(data_dir_regen, d)
                    report_name = d.split('__', 1)[1].replace('_', '') if '__' in d else d
                    report_path = os.path.join(task_dir_regen, '{}.md'.format(report_name))
                    run_script('final_report_generator.py', [match_dir, report_path], timeout=120)
    log('ORGANIZE', '整理文件结构')
    organize_data(date_str)
    log('NOTION', '同步数据到 Notion...')
    sync_script = os.path.join(ROOT_DIR, 'sync_notion.js')
    if os.path.exists(sync_script):
        cmd = ['node', sync_script, 'add', date_str]
        if match_filter_set is not None:
            filter_str = ','.join(sorted(match_filter_set))
            cmd.append(filter_str)
        try:
            env_copy = os.environ.copy()
            env_copy['NOTION_TASKS_DIR'] = TASKS_DIR
            result = subprocess.run(cmd, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                encoding='utf-8', errors='replace', timeout=120, env=env_copy)
            if result.stdout:
                for line in result.stdout.strip().split('\n')[-10:]:
                    log('SYNC', line)
            if result.returncode != 0:
                err = result.stderr.strip().split('\n')[-1] if result.stderr else ''
                log('SYNC_ERR', 'Notion同步返回非零: {}'.format(err))
            else:
                log('SYNC_OK', 'Notion同步完成')
        except Exception as e:
            log('SYNC_ERR', 'Notion同步异常: {}'.format(e))
    else:
        log('SYNC_WARN', 'sync_notion.js 未找到，跳过同步')
    log('DONE', '全部完成: {}/{} 场成功'.format(success_count, len(matches)))
    if match_filter_set is not None:
        log('NOTE', '筛选模式: 仅同步了筛选的场次到 Notion')
    else:
        log('REPORTS', '最终报告位置: {}/'.format(os.path.join(TASKS_DIR, date_str)))

if __name__ == '__main__':
    main()
