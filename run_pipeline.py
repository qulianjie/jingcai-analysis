# -*- coding: utf-8 -*-
"""竞彩24步全自动流水线 - 一键生成所有比赛的最终报告

用法:
    python run_pipeline.py                    # 分析今天所有未开赛比赛
    python run_pipeline.py 2026-04-29         # 分析指定日期
    python run_pipeline.py 001                # 分析今日第001场
    python run_pipeline.py all                # 分析今日所有场次(包括已开赛)
"""
import os, sys, json, re, time, subprocess, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from _log_util import setup_logger
_logger = None
LOG_DIR = None

from datetime import datetime

import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ============ Macau Line 提取（从 500.com 亚盘页） ============
def _fetch_macau_line(fid):
    """从500.com亚盘页提取澳门盘口，返回盘口名或空字符串"""
    if not fid:
        return ''
    import requests
    sess = requests.Session()
    sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    try:
        r = sess.get('https://odds.500.com/fenxi/yazhi-%s.shtml' % fid, timeout=15)
        r.encoding = 'gbk'
        raw = r.text.encode('gbk', errors='replace')
        m = re.search(rb'cid=5.*?quancheng.*?</span>.*?pl_table_data[^>]*>.*?<tr[^>]*>.*?<td[^>]*>[^<]*</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>[^<]*</td>', raw, re.DOTALL)
        if m:
            cp = m.group(1).decode('gbk', errors='replace').strip()
            cp = re.sub(r'<[^>]+>', '', cp)
            return cp
    except:
        pass
    return ''


# ============ 缓存清除 + 球队ID提取（Loop Engineering 工具函数）============
def _clear_step_cache(fid, url_patterns):
    """按URL模式清除HTTP缓存（如缓存污染导致空数据时调用）"""
    if not fid or not url_patterns:
        return
    import hashlib, os
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'http_cache')
    if not os.path.isdir(cache_dir):
        return
    for fname in os.listdir(cache_dir):
        if not fname.endswith('.meta.json'):
            continue
        meta_path = os.path.join(cache_dir, fname)
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            cached_url = meta.get('url', '')
            if any(p in cached_url for p in url_patterns):
                base = fname.replace('.meta.json', '')
                for ext in ['.html', '.meta.json']:
                    p = os.path.join(cache_dir, base + ext)
                    if os.path.exists(p):
                        os.remove(p)
        except:
            pass


def _fetch_team_id(fid, side='home'):
    """从500.com欧赔页提取主队/客队ID"""
    if not fid:
        return ''
    import requests, re
    sess = requests.Session()
    sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    try:
        r = sess.get('https://odds.500.com/fenxi/ouzhi-%s.shtml' % fid, timeout=15)
        r.encoding = 'gbk'
        if side == 'home':
            m = re.search(r'href="https://liansai\.500\.com/team/(\d+)/teamfixture/"[^>]*>主', r.text)
        else:
            m = re.search(r'href="https://liansai\.500\.com/team/(\d+)/teamfixture/"[^>]*>客', r.text)
        if m:
            return m.group(1)
    except:
        pass
    return ''


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')

def log(tag, msg):
    global _logger
    if _logger is None:
        _logger = setup_logger('pipeline', LOG_DIR)
    t = datetime.now().strftime('%H:%M:%S')
    msg = str(msg).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    _logger.info('[{}] [{}] {}'.format(t, tag, msg))
    sys.stdout.flush()

def run_script(script_name, args, timeout=3600):
    script_path = os.path.join(SCRIPT_DIR, script_name)
    if not os.path.exists(script_path):
        log('ERROR', '脚本不存在: {}'.format(script_name))
        return False
    cmd = [sys.executable, script_path] + args
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            log('ERROR', '{} 返回码: {}'.format(script_name, result.returncode))
            if result.stderr:
                log('STDERR', result.stderr[:1000])
            return False
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                log(script_name.split('.')[0], line.strip())
        return True
    except subprocess.TimeoutExpired:
        log('ERROR', '{} 超时'.format(script_name))
        return False
    except Exception as e:
        log('ERROR', '{} 异常: {}'.format(script_name, e))
        return False

# ===== 工作区锁：防止多session冲突 =====
def _acquire_lock(name):
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, 'protect.py'), 'lock', name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        print('  [LOCK] _acquire_lock error: %s' % e)
        return False

def _release_lock(name):
    try:
        subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, 'protect.py'), 'unlock', name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10
        )
    except:
        pass

def _get_today_group_name(date_str):
    """根据日期字符串获取今天的中文星期名（如'周五'）"""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        return weekday_names[dt.weekday()]
    except:
        return None

def fetch_matches(date_str, today_only=True):
    """加载比赛列表
    
    Args:
        date_str: 日期字符串 YYYY-MM-DD
        today_only: 是否只返回今天的比赛（默认True）
    """
    matches_file = os.path.join(TASKS_DIR, date_str, 'matches_data.json')
    all_search_paths = []
    # 优先路径
    all_search_paths.append(matches_file)
    # 也尝试 data/ 子目录
    for fname in ['matches_data.json', 'matches.json']:
        for search_dir in [TASKS_DIR, os.path.join(TASKS_DIR, date_str)]:
            all_search_paths.append(os.path.join(search_dir, fname))
    
    for fpath in all_search_paths:
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 顶层 matches 数组
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                if 'matches' in data and isinstance(data['matches'], list):
                    return data['matches']
                # groups 格式: { "周五": { "matches": [...] } }
                if 'groups' in data and isinstance(data['groups'], dict):
                    groups = data['groups']
                    if today_only:
                        # 只取今天的星期组
                        today_name = _get_today_group_name(date_str)
                        if today_name and today_name in groups:
                            group_data = groups[today_name]
                            if isinstance(group_data, dict) and 'matches' in group_data:
                                return group_data['matches']
                        # 如果找不到精确匹配，退化为全部
                        all_matches = []
                        for gn, gd in groups.items():
                            if isinstance(gd, dict) and 'matches' in gd:
                                all_matches.extend(gd['matches'])
                        return all_matches
                    else:
                        # 取全部
                        all_matches = []
                        for group_name, group_data in groups.items():
                            if isinstance(group_data, dict) and 'matches' in group_data:
                                all_matches.extend(group_data['matches'])
                        if all_matches:
                            return all_matches
    return []

def organize_data(date_str):
    """整理文件：data/ 子目录 + 根目录只留报告"""
    task_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.exists(task_dir):
        return
    
    data_dir = os.path.join(task_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    moved = 0
    for item in os.listdir(task_dir):
        item_path = os.path.join(task_dir, item)
        if os.path.isdir(item_path) and item.startswith('match'):
            shutil.move(item_path, os.path.join(data_dir, item))
            moved += 1
    
    # 也移走group目录
    for item in os.listdir(task_dir):
        if item.startswith('group'):
            src = os.path.join(task_dir, item)
            if os.path.isdir(src):
                shutil.move(src, os.path.join(data_dir, item))
                moved += 1
    
    if moved > 0:
        log('ORGANIZE', '已移动 {} 个目录到 data/'.format(moved))

def run_match_pipeline(match, date_str, match_num, league_cache_dir=None):
    """单场比赛的24步流水线"""
    home = match.get('home', '')
    away = match.get('away', '')
    match_id = match.get('matchnum', '{}'.format(match_num))
    
    match_dir_name = 'match{}_{}__{}'.format(match_num, home, away)
    match_dir = os.path.join(TASKS_DIR, date_str, 'data', match_dir_name)
    os.makedirs(match_dir, exist_ok=True)
    
    # 写 meta.json（步骤脚本从这里读 fid/league 等参数）
    meta = {
        'matchnum': match_id,
        'match': '{} {} vs {}'.format(match_id, home, away),
        'fid': match.get('fid', ''),
        'league': match.get('league', ''),
        'home': home,
        'away': away,
        'date': date_str,
        'status': 'in_progress',
        'home_id': match.get('home_id', ''),
        'away_id': match.get('away_id', ''),
        'rq': match.get('rq', ''),
        'macau_line': match.get('macau_line', ''),
    }
    meta_path = os.path.join(match_dir, 'meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    # 自动补全 macau_line（如缺失则从500.com亚盘页提取）
    if not meta.get('macau_line'):
        log('MACAU', '自动提取澳门盘口(fid=%s)...' % meta.get('fid', ''))
        macau_line = _fetch_macau_line(meta.get('fid', ''))
        if macau_line:
            meta['macau_line'] = macau_line
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            log('MACAU', '澳门盘口: %s' % macau_line)
        else:
            log('MACAU', '⚠️ 未提取到澳门盘口')
    
    # 直接调用各步骤脚本（所有脚本都支持 match_dir 模式，从 meta.json 读参数）
    steps = [
        ('step146_extractor.py', [match_dir]),
        ('step235_runner.py', [match_dir]),
        ('step7_runner.py', [match_dir]),
        ('step8_1923_extractor.py', [match_dir, '--cache', league_cache_dir]) if league_cache_dir else ('step8_1923_extractor.py', [match_dir]),
        ('step918_extractor.py', [match_dir]),
        ('step24_extractor.py', [match_dir]),
        ('step25_zhuangjia.py', ['--match-dir', match_dir]),
    ]
    
    # 杯赛step8需要迭代收集大量球队，加大超时
    cup_leagues = ['欧罗巴', '欧联', '欧协联', '解放者杯', '南美解放者杯', '欧冠', '欧洲冠军联赛']
    step8_timeout = 3600
    
    for script, args in steps:
        log('STEP', '{} {}'.format(script, ' '.join(args)))
        t = step8_timeout if script == 'step8_1923_extractor.py' else 3600
        if not run_script(script, args, timeout=t):
            log('FAIL', '步骤失败: {}'.format(script))
            return False
        time.sleep(2)
    
    # ============ 数据质量核查 + Loop Engineering（自动修复）============
    passed, issues = verify_match_data(match_dir, home, away)
    _save_verify_result(match_dir, home, away, passed, issues)
    if issues:
        log('CHECK', '🔍 {} vs {} 发现{}项'.format(home, away, len(issues)))
        # ---- Loop Engineering: 遍历所有步骤，逐项修复 ----
        
        # 步骤文件 → 对应脚本 + 需清除的缓存URL模式
        STEP_ISSUE_MAP = {
            '欧赔基础':    ('step146_extractor.py', ['fenxi/ouzhi']),
            '让球基础':    ('step146_extractor.py', ['fenxi/rangqiu']),
            '亚盘基础':    ('step146_extractor.py', ['fenxi/yazhi']),
            '竞彩同赔':    ('step235_runner.py',   ['ouzhi_sameajax', 'rangqiu_sameajax']),
            'Interwetten同赔': ('step235_runner.py', ['ouzhi_sameajax', 'rangqiu_sameajax']),
            '让球同赔':    ('step235_runner.py',   ['ouzhi_sameajax', 'rangqiu_sameajax']),
            '澳门同赔':    ('step7_runner.py',     []),
            '同联赛亚盘':  ('step8_1923_extractor.py', []),
            '主队历史':    ('step918_extractor.py', ['liansai.500.com/team']),
            '客队历史':    ('step918_extractor.py', ['liansai.500.com/team']),
            '百家对比':    ('step918_extractor.py', ['fenxi1']),
            '盘路匹配':    ('step24_extractor.py',  ['fenxi1']),
            '庄家盈亏':    ('step25_zhuangjia.py',  []),
            '盈亏占比':    ('step25_zhuangjia.py',  []),
            'step25_zhuangjia.json': ('step25_zhuangjia.py',  []),
            'step26_profit_ratio.json': ('step25_zhuangjia.py',  []),
        }
        
        retry_scripts = []
        fixed_any = False
        
        # 修复1: macau_line为空（特殊处理，需写meta.json）
        for issue in issues:
            if 'macau_line为空' in issue:
                ml = _fetch_macau_line(meta.get('fid', ''))
                if ml:
                    meta['macau_line'] = ml
                    with open(meta_path, 'w', encoding='utf-8') as f:
                        json.dump(meta, f, ensure_ascii=False, indent=2)
                    log('FIX', '✅ macau_line已补: {}'.format(ml))
                    fixed_any = True
                    for s in ['step7_runner.py']:
                        if s not in retry_scripts: retry_scripts.append(s)
                    for s in ['step8_1923_extractor.py']:
                        if s not in retry_scripts: retry_scripts.append(s)

        # 修复2: home_id/away_id为空 → 从胜负彩页面提取
        for issue in issues:
            if 'home_id为空' in issue:
                hid = _fetch_team_id(meta.get('fid', ''), 'home')
                if hid:
                    meta['home_id'] = hid
                    fixed_any = True
            if 'away_id为空' in issue:
                aid = _fetch_team_id(meta.get('fid', ''), 'away')
                if aid:
                    meta['away_id'] = aid
                    fixed_any = True
        if fixed_any and ('home_id' in meta or 'away_id' in meta):
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            for s in ['step918_extractor.py']:
                if s not in retry_scripts: retry_scripts.append(s)

        # 修复3: 通用步骤文件空数据 → 清除对应HTTP缓存后重跑
        for issue in issues:
            for keyword, (script, cache_urls) in STEP_ISSUE_MAP.items():
                if keyword in issue:
                    if script not in retry_scripts:
                        log('FIX', '🔄 {} 数据空，清除缓存后重跑 {}'.format(keyword, script))
                        fixed_any = True
                        retry_scripts.append(script)
                        # 清除该步骤对应的HTTP缓存
                        _clear_step_cache(meta.get('fid', ''), cache_urls)

        # 执行修复后重跑
        if retry_scripts:
            for script_name in sorted(set(retry_scripts)):
                script_args_map = {
                    'step146_extractor.py':        ('step146_extractor.py', [match_dir]),
                    'step235_runner.py':           ('step235_runner.py', [match_dir]),
                    'step7_runner.py':             ('step7_runner.py', [match_dir]),
                    'step8_1923_extractor.py':     ('step8_1923_extractor.py', [match_dir, '--cache', league_cache_dir]) if league_cache_dir else ('step8_1923_extractor.py', [match_dir]),
                    'step918_extractor.py':        ('step918_extractor.py', [match_dir]),
                    'step24_extractor.py':         ('step24_extractor.py', [match_dir]),
                    'step25_zhuangjia.py':         ('step25_zhuangjia.py', ['--match-dir', match_dir]),
                }
                if script_name in script_args_map:
                    s, a = script_args_map[script_name]
                    log('RETRY', '重跑 {}'.format(s))
                    run_script(s, a, timeout=3600)
                    time.sleep(1)

            # 修复后重新验证
            passed2, issues2 = verify_match_data(match_dir, home, away)
            _save_verify_result(match_dir, home, away, passed2, issues2)
            if issues2:
                for iss in issues2:
                    log('CHECK', '🔍 修复后仍有: {}'.format(iss))
                log('CHECK', '🔍 共{}项未修复（已持久化）'.format(len(issues2)))
            else:
                log('CHECK', '✅ 修复后全部通过')
    else:
        log('CHECK', '✅ {} vs {} 数据完整'.format(home, away))
    
    return True

def _save_verify_result(match_dir, home, away, passed, issues):
    """持久化核查结果到 verify_result.json"""
    import os, json
    result_path = os.path.join(match_dir, 'verify_result.json')
    result = {
        'passed': passed,
        'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'match': '{} vs {}'.format(home, away),
        'issues': issues,
    }
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def verify_match_data(match_dir, home='', away=''):
    """核查单场比赛的数据质量，返回 (passed, issues)"""
    import os, json
    issues = []
    
    # 读取meta.json
    meta_path = os.path.join(match_dir, 'meta.json')
    if not os.path.exists(meta_path):
        issues.append('缺少meta.json')
        return (False, issues)
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    # 检查关键字段
    if not meta.get('home_id'):
        issues.append('home_id为空（step9-18会失败）')
    if not meta.get('away_id'):
        issues.append('away_id为空（step9-18会失败）')
    if not meta.get('macau_line') or meta.get('macau_line') == '':
        issues.append('macau_line为空（step8盘口筛选会失败）')
    
    # 检查关键文件是否存在且有内容
    key_files = [
        ('group01_europe/step1_europe_base.txt', '欧赔基础'),
        ('group01_europe/step2_jingcai_same.txt', '竞彩同赔'),
        ('group01_europe/step3_interwetten_same.txt', 'Interwetten同赔'),
        ('group02_handicap/step4_handicap_base.txt', '让球基础'),
        ('group02_handicap/step5_handicap_same.txt', '让球同赔'),
        ('group03_asian/step6_asian_base.txt', '亚盘基础'),
        ('group03_asian/step7_macau_same.txt', '澳门同赔'),
        ('group03_asian/step8_same_league.txt', '同联赛亚盘'),
        ('group04_teamA/step9_home_history.txt', '主队历史'),
        ('group05_teamB/step14_away_history.txt', '客队历史'),
        ('group06_baijia/step19_baijia_compare.txt', '百家对比'),
        ('step25_zhuangjia.json', '庄家盈亏'),
        ('step26_profit_ratio.json', '盈亏占比'),
    ]
    
    # 各步骤空模板阈值（实测空模板大小+100B余量）
    # step5/step7 的"无同赔数据"极小 (~300B)，属正常情况，阈值设为动态检测
    EMPTY_TEMPLATE_THRESHOLDS = {
        'group01_europe/step2_jingcai_same.txt': 630,       # 空模板527+103
        'group01_europe/step3_interwetten_same.txt': 640,   # 空模板536+104
        'group02_handicap/step5_handicap_same.txt': 420,    # 空模板315+105 (无同赔数据)
        'group03_asian/step7_macau_same.txt': 1200,         # 澳门同赔无数据时约1100
        'group03_asian/step8_same_league.txt': 880,         # 空模板774+106 (原1370太宽→改880)
        'group04_teamA/step9_home_history.txt': 1700,       # 空模板1520+180
        'group05_teamB/step14_away_history.txt': 1700,      # 空模板1500+200
        'group06_baijia/step19_baijia_compare.txt': 1800,   # 空模板1700+100
        'step25_zhuangjia.json': 1100,                      # 正常~1150, 空JSON <1100
        'step26_profit_ratio.json': 1550,                   # 正常~1630, 空JSON <1550
    }
    for filepath, desc in key_files:
        full_path = os.path.join(match_dir, filepath)
        if not os.path.exists(full_path):
            issues.append('缺少文件: {}'.format(filepath))
        else:
            size = os.path.getsize(full_path)
            if filepath in EMPTY_TEMPLATE_THRESHOLDS:
                threshold = EMPTY_TEMPLATE_THRESHOLDS[filepath]
                if size <= threshold:
                    issues.append('{}数据为空（文件仅{}B，低于空模板阈值{}B）'.format(desc, size, threshold))
            else:
                if size == 0:
                    issues.append('空文件: {} ({})'.format(filepath, desc))
    
    # 检查step2竞彩同赔是否有有效数据
    step2_path = os.path.join(match_dir, 'group01_europe/step2_jingcai_same.txt')
    if os.path.exists(step2_path):
        with open(step2_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if '共0场' in content or '共 0 场' in content or '筛选结果为0场' in content or '提取失败' in content:
            issues.append('step2竞彩同赔0场或提取失败')
    
    # 检查step5让球同赔是否有有效数据
    step5_path = os.path.join(match_dir, 'group02_handicap/step5_handicap_same.txt')
    if os.path.exists(step5_path):
        with open(step5_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if '共0场' in content or '共 0 场' in content or '筛选结果为0场' in content or '提取失败' in content:
            issues.append('step5让球同赔0场或提取失败')
    
    # 检查step7澳门同赔是否有有效数据
    step7_path = os.path.join(match_dir, 'group03_asian/step7_macau_same.txt')
    if os.path.exists(step7_path):
        with open(step7_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if '共0场' in content or '共 0 场' in content or '筛选结果为0场' in content:
            issues.append('step7澳门同赔0场（可能无同赔数据）')
        if '无同赔数据' in content:
            issues.append('step7澳门同赔无同赔数据')
    
    # 检查step3 Interwetten同赔是否有有效数据
    step3_path = os.path.join(match_dir, 'group01_europe/step3_interwetten_same.txt')
    if os.path.exists(step3_path):
        with open(step3_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if '共0场' in content or '共 0 场' in content or '筛选结果为0场' in content:
            issues.append('step3 Interwetten同赔0场（可能无同赔数据）')
        if '无同赔数据' in content:
            issues.append('step3 Interwetten同赔无同赔数据')
    
    # 检查step8同联赛数据是否有有效行
    step8_path = os.path.join(match_dir, 'group03_asian/step8_same_league.txt')
    if not os.path.exists(step8_path):
        issues.append('缺少文件: group03_asian/step8_same_league.txt')
    else:
        with open(step8_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if '0场' in content or '筛选结果为0场' in content:
            issues.append('step8同联赛筛选0场（macau_line可能为空或联赛/盘口不匹配）')
    
    # 检查step9/14是否有有效筛选结果
    for step_file, desc in [('group04_teamA/step9_home_history.txt', '主队'), ('group05_teamB/step14_away_history.txt', '客队')]:
        fp = os.path.join(match_dir, step_file)
        if not os.path.exists(fp):
            issues.append('缺少文件: {} ({})'.format(step_file, desc))
        else:
            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()
            if '共0场' in content or '筛选结果为0场' in content or 'team_id为空' in content:
                issues.append('{}历史筛选0场（team_id可能为空或联赛/盘口不匹配）'.format(desc))
    
    # 检查step19百家对比是否有有效数据
    for step_file, desc in [
        ('group06_baijia/step19_baijia_compare.txt', '百家对比'),
    ]:
        fp = os.path.join(match_dir, step_file)
        if not os.path.exists(fp):
            issues.append('缺少文件: {} ({})'.format(step_file, desc))
        else:
            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()
            if '提取失败' in content or '表格无数据行' in content or '共0场' in content:
                issues.append('{}提取失败或无数据 ({})'.format(desc, step_file))
    
    if issues:
        return (False, issues)
    else:
        return (True, [])


def _auto_fix_issues(match_dir, match_name, issues, date_str):
    """尝试自动修复可修复的问题，返回 (fixed, unfixable_issues)"""
    import os, json, subprocess, sys
    fixed = []
    unfixable = []
    
    for issue in issues:
        # --- 步25/26 庄家盈亏: 重新抓取500.com投注页 ---
        if ('庄家盈亏' in issue or '盈亏占比' in issue or 'step25_zhuangjia' in issue or 'step26_profit_ratio' in issue) and ('为空' in issue or '空文件' in issue or '缺少文件' in issue):
            log('AUTO_FIX', '[AUTO_FIX] 尝试重新抓取步25/26: %s' % match_name)
            try:
                meta_path = os.path.join(match_dir, 'meta.json')
                if os.path.exists(meta_path):
                    with open(meta_path, 'r') as f:
                        meta = json.load(f)
                    fid = meta.get('fid', '')
                    if fid:
                        runner = os.path.join(os.path.dirname(os.path.dirname(match_dir)), 'step25_zhuangjia.py')
                        if os.path.exists(runner):
                            py = sys.executable
                            r = subprocess.run([py, runner, '--fid', fid, '--date', date_str],
                                               capture_output=True, text=True, timeout=60)
                            if r.returncode == 0:
                                fixed.append('步25/26已自动重抓修复')
                                log('AUTO_FIX', '[AUTO_FIX] OK 步25/26重抓成功: %s' % match_name)
                            else:
                                unfixable.append('步25/26重抓失败: %s' % r.stderr[:100])
                        else:
                            unfixable.append('步25/26重抓脚本不存在: %s' % runner)
            except Exception as e:
                unfixable.append('步25/26自动修复异常: %s' % str(e))
        
        # --- step8 同联赛亚盘0场: 检查macau_line ---
        elif 'step8同联赛筛选0场' in issue:
            log('AUTO_FIX', '[AUTO_FIX] 检查步8根因: %s' % match_name)
            meta_path = os.path.join(match_dir, 'meta.json')
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
                macau_line = meta.get('macau_line', '')
                if not macau_line:
                    unfixable.append('step8同联赛0场根因: macau_line为空(无盘口数据)')
                else:
                    unfixable.append('step8同联赛0场: 有macau_line(%s)但联赛无同盘口数据' % macau_line)
        
        # --- step9/14 历史0场: 检查team_id ---
        elif '历史筛选0场' in issue:
            side = '主队' if '主队' in issue else '客队'
            meta_path = os.path.join(match_dir, 'meta.json')
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
                key = 'home_id' if '主队' in issue else 'away_id'
                tid = meta.get(key, '')
                if not tid:
                    unfixable.append('%s历史0场根因: %s为空' % (side, key))
                else:
                    unfixable.append('%s历史0场: %s=%s但无历史数据' % (side, key, tid))
        
        else:
            # 其余问题: 0场/无同赔等属正常情况
            unfixable.append(issue)
    
    return fixed, unfixable


def _notify_quality_flag(date_str, results):
    """显式FLAG输出到stdout"""
    failed = [r for r in results if r.get('passed') in (False, 'unknown')]
    if not failed:
        return
    
    print()
    print('=' * 60)
    print('[FLAG]  DATA QUALITY FLAG: %d场数据异常' % len(failed))
    print('=' * 60)
    for r in failed:
        match = r.get('match', r.get('match_dir', '未知'))
        auto_fixed = r.get('auto_fixed', [])
        still_broken = r.get('issues', [])
        if auto_fixed:
            print('  [FIXED] %s: %s' % (match, '; '.join(auto_fixed)))
        if still_broken:
            print('  [FAIL]  %s: %s' % (match, '; '.join(still_broken)))
    print()
    print('[FLAG]  详情: %s' % os.path.join(TASKS_DIR, date_str, 'data', 'verify_summary.json'))
    print('=' * 60)
    print()


def _summarize_verify_results(date_str):
    """汇总当天所有比赛的核查结果，写入 data/verify_summary.json"""
    import os, json
    data_dir = os.path.join(TASKS_DIR, date_str, 'data')
    if not os.path.exists(data_dir):
        log('VERIFY_SUMMARY', 'data目录不存在: {}'.format(data_dir))
        return
    
    results = []
    passed_count = 0
    failed_count = 0
    
    for d in sorted(os.listdir(data_dir)):
        if not d.startswith('match'):
            continue
        vp = os.path.join(data_dir, d, 'verify_result.json')
        if not os.path.exists(vp):
            results.append({'match_dir': d, 'passed': 'unknown', 'reason': '无核查记录'})
            continue
        with open(vp, 'r', encoding='utf-8') as f:
            r = json.load(f)
        if r.get('passed'):
            passed_count += 1
        else:
            failed_count += 1
        results.append({
            'match_dir': d,
            'match': r.get('match', ''),
            'passed': r.get('passed'),
            'checked_at': r.get('checked_at', ''),
            'issues': r.get('issues', []),
        })
    
    summary = {
        'date': date_str,
        'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total': len(results),
        'passed': passed_count,
        'failed': failed_count,
        'details': results,
    }
    
    summary_path = os.path.join(data_dir, 'verify_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    log('VERIFY_SUMMARY', '✅ {}通过, ❌ {}未通过, 共{}场'.format(passed_count, failed_count, len(results)))
    log('VERIFY_SUMMARY', '汇总写入: {}'.format(summary_path))
    
    if failed_count > 0:
        log('VERIFY_SUMMARY', '--- 未通过比赛 ---')
        for r in results:
            if r['passed'] in (False, 'unknown'):
                log('VERIFY_SUMMARY', '  ❌ {}: {}'.format(r.get('match', r['match_dir']), r.get('issues', ['无记录'])))
    else:
        log('VERIFY_SUMMARY', '✅ 全部通过')
    
    # FLAG + 自动修复: 显式输出到stdout
    if failed_count > 0:
        # 尝试自动修复每个失败项
        for r in results:
            if r['passed'] in (False, 'unknown'):
                match_dir_full = os.path.join(data_dir, r['match_dir'])
                fixed, unfixable = _auto_fix_issues(
                    match_dir_full, r.get('match', r['match_dir']),
                    r.get('issues', []), date_str)
                if fixed:
                    r['auto_fixed'] = fixed
                r['issues'] = unfixable
                # 更新verify_result.json
                vp = os.path.join(data_dir, r['match_dir'], 'verify_result.json')
                if os.path.exists(vp):
                    with open(vp, 'r', encoding='utf-8') as f:
                        vr = json.load(f)
                    vr['issues'] = unfixable
                    if fixed:
                        vr['auto_fixed'] = fixed
                    with open(vp, 'w', encoding='utf-8') as f:
                        json.dump(vr, f, ensure_ascii=False, indent=2)
        _notify_quality_flag(date_str, results)


def main():
    # 先解析日期（用于按日期隔离锁）
    date_str = datetime.now().strftime('%Y-%m-%d')
    filter_match = None
    
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        if re.match(r'\d{4}-\d{2}-\d{2}', arg1):
            date_str = arg1
        else:
            filter_match = arg1
    
    # 按日期获取锁，不同日期可并行
    lock_name = 'pipeline_{}'.format(date_str)
    log('LOCK', '尝试获取 pipeline 锁 ({})...'.format(date_str))
    if not _acquire_lock(lock_name):
        log('LOCK', 'pipeline 锁已被占用 ({})，退出'.format(date_str))
        sys.exit(1)
    log('LOCK', 'OK 已获取 pipeline 锁 ({})'.format(date_str))
    
    try:
        log('START', '竞彩24步全自动流水线启动')
        
        if len(sys.argv) > 2:
            arg2 = sys.argv[2]
            if re.match(r'\d{4}-\d{2}-\d{2}', arg2):
                date_str = arg2
            else:
                filter_match = arg2
        
        log('CONFIG', '日期: {}, 过滤: {}'.format(date_str, filter_match or '全部'))
        
        # 判断是否来自cron自动运行（无参数）
        from_cron = len(sys.argv) <= 1
        
        matches = fetch_matches(date_str, today_only=False)
        if not matches:
            log('ERROR', '未找到比赛数据')
            return
        
        log('FOUND', '找到{}场比赛'.format(len(matches)))
        
        # Cron自动运行时：强制只跑当天星期开头的比赛
        if from_cron:
            today_weekday = _get_today_group_name(date_str)
            if today_weekday:
                before = len(matches)
                matches = [m for m in matches if m.get('matchnum', '').startswith(today_weekday)]
                log('CRON_FILTER', '只保留{}开头的比赛: {} -> {}'.format(today_weekday, before, len(matches)))
        
        if filter_match and filter_match != 'all':
            # 支持范围格式: 001-006 或单个: 001
            import re as _re
            _range_m = _re.match(r'(\d+)-(\d+)', str(filter_match))
            if _range_m:
                _start, _end = int(_range_m.group(1)), int(_range_m.group(2))
                _nums = {f'{i:03d}' for i in range(_start, _end + 1)}
                matches = [m for m in matches if any(n in m.get('matchnum', '') for n in _nums)]
                log('FILTER', '范围过滤 {}~{}: {}场'.format(_start, _end, len(matches)))
            else:
                matches = [m for m in matches if filter_match in m.get('matchnum', '')]
                log('FILTER', '过滤后剩余{}场'.format(len(matches)))
        
        # ============ 预缓存阶段：按联赛分组提前爬取共享历史数据 ============
        cache_dir = os.path.join(SCRIPT_DIR, 'data', 'league_cache')
        log('PRECACHE', '使用全局联赛缓存 → {}'.format(cache_dir))
        run_script('precache_leagues.py', [date_str], timeout=3600)
        log('PRECACHE', '预缓存完成')

        success_count = 0
        match_results = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_map = {}
            for i, match in enumerate(matches):
                match_num = match.get('matchnum', '{:03d}'.format(i+1))
                log('MATCH', '({}/{}) {} {} vs {} (提交并发)'.format(i+1, len(matches), match_num, match.get('home',''), match.get('away','')))
                fut = executor.submit(run_match_pipeline, match, date_str, i+1, cache_dir)
                future_map[fut] = match_num
            
            for fut in as_completed(future_map):
                mn = future_map[fut]
                try:
                    if fut.result():
                        success_count += 1
                        log('OK', '{} 完成'.format(mn))
                    else:
                        log('FAIL', '{} 失败'.format(mn))
                except Exception as e:
                    log('ERROR', '{} 异常: {}'.format(mn, e))
        
        log('STEP25', '庄家盈亏分析(25) - 全量处理')
        run_script('step25_zhuangjia.py', [date_str], timeout=3600)
        
        log('STEP26', '盈亏占比分析(25→26) - 全量处理(已合并)')
        run_script('step25_zhuangjia.py', [date_str, '--all'], timeout=3600)
        
        # Re-generate all reports with step 25+26 data
        log('REGEN', '重新生成报告（含第25+26步）')
        task_dir_regen = os.path.join(TASKS_DIR, date_str)
        data_dir_regen = os.path.join(task_dir_regen, 'data')
        if os.path.exists(data_dir_regen):
            for d in sorted(os.listdir(data_dir_regen)):
                if d.startswith('match') and os.path.isdir(os.path.join(data_dir_regen, d)):
                    match_dir = os.path.join(data_dir_regen, d)
                    # Output report to task root (not data/)
                    # 标准命名格式：周X0XX_主队vs客队.md（从 meta.json 提取，不依赖目录名）
                    meta_file = os.path.join(match_dir, 'meta.json')
                    if not os.path.exists(meta_file):
                        log('WARN', '缺少 meta.json: {}'.format(match_dir))
                        continue
                    try:
                        with open(meta_file, 'r', encoding='utf-8') as mf:
                            meta_data = json.loads(mf.read())
                        match_num = meta_data.get('matchnum', '')
                        home = meta_data.get('home', '')
                        away = meta_data.get('away', '')
                        if not match_num or not home or not away:
                            log('WARN', 'meta.json 字段不完整: {}'.format(meta_file))
                            continue
                        report_name = '{}_{}vs{}'.format(match_num, home, away)
                    except Exception as e:
                        log('ERROR', 'meta.json 解析失败: {}'.format(e))
                        continue
                    report_path = os.path.join(task_dir_regen, '{}.md'.format(report_name))
                    log('REGEN', d)
                    run_script('final_report_generator.py', [match_dir, report_path], timeout=3600)
        
        log('ORGANIZE', '整理文件结构')
        organize_data(date_str)
        
        # ============ 汇总核查结果 ============
        log('VERIFY_SUMMARY', '汇总所有比赛核查结果...')
        _summarize_verify_results(date_str)
        
        # 数据诊断
        log('DIAGNOSE', '开始数据完整性诊断...')
        run_script('diagnose.py', ['--quick', date_str], timeout=3600)
        
        # 触发反馈学习引擎 V2（自动分析历史反馈+组合模式+step25/26数据）
        log('LEARN', '触发反馈学习引擎 V2...')
        run_script('feedback_learner.py', [], timeout=3600)
        
        # 模式挖掘：从反馈数据提取历史模式
        log('PATTERN_MINER', '模式挖掘...')
        run_script('pattern_miner.py', [], timeout=7200)
        
        # 模式匹配：将历史模式匹配到今日比赛，生成 match_patterns_report.json
        log('PATTERN_MATCHER', '模式匹配...')
        run_script('pattern_matcher.py', [date_str], timeout=3600)
        
        # 更新Notion 4字段（含备注）：将模式匹配结果写入 Notion
        log('UPDATE_NOTION', '更新Notion 4字段（含备注）...')
        run_script('_update_notion_4fields.py', [date_str], timeout=3600)
        
        # 同步到 Notion
        log('NOTION', '同步到 Notion...')
        run_script('sync_notion_wrapper.py', ['add', date_str], timeout=3600)
        
        # 运行反馈机制（Node.js脚本，获取比分+终盘赔率+更新Notion）
        log('FEEDBACK', '运行反馈机制...')
        feedback_path = os.path.join(SCRIPT_DIR, 'feedback.js')
        if os.path.exists(feedback_path):
            import shutil
            node_exe = shutil.which('node')
            if node_exe:
                cmd = [node_exe, feedback_path, '--date', date_str]
                try:
                    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3600, encoding='utf-8', errors='replace')
                    if result.returncode != 0:
                        log('ERROR', 'feedback.js 返回码: {}'.format(result.returncode))
                        if result.stderr:
                            log('STDERR', result.stderr[:1000])
                    else:
                        if result.stdout:
                            for line in result.stdout.strip().split('\n'):
                                log('FEEDBACK', line.strip())
                        log('FEEDBACK', '反馈机制执行完成')
                except subprocess.TimeoutExpired:
                    log('ERROR', 'feedback.js 超时')
                except Exception as e:
                    log('ERROR', 'feedback.js 异常: {}'.format(e))
            else:
                log('ERROR', 'Node.js 未安装，无法运行 feedback.js')
        else:
            log('ERROR', 'feedback.js 不存在')
        
        log('DONE', '全部完成: {}/{} 场成功'.format(success_count, len(matches)))
        log('REPORTS', '最终报告位置: {}/'.format(os.path.join(TASKS_DIR, date_str)))
    

        # ============ 双引擎对比 ============
        try:
            import subprocess as subproc_mod
            task_dir = os.path.join(TASKS_DIR, date_str)
            for f in os.listdir(task_dir):
                if f.endswith('.md') and f not in ['sunday_matches.md','monday_matches.md','season_schedule.md']:
                    report_path = os.path.join(task_dir, f)
                    subproc_mod.run([sys.executable, 'dual_append.py', report_path], 
                                 cwd=SCRIPT_DIR, capture_output=True, timeout=30)
            # 追踪对比结果
            subproc_mod.run([sys.executable, 'dual_track.py', date_str],
                         cwd=SCRIPT_DIR, capture_output=True, timeout=30)
            log('DUAL', '双引擎对比已完成')
        except Exception as e:
            log('WARN', '双引擎对比异常: {}'.format(e))
        
    finally:
        _release_lock(lock_name)
        log('LOCK', '已释放 pipeline 锁 ({})'.format(date_str))

if __name__ == '__main__':
    main()
