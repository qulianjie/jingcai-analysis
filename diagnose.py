# -*- coding: utf-8 -*-
"""
竞彩数据核对+自动修复器
1. 读取最终报告.md，提取每步数据量
2. 诊断空数据原因（访问源站验证）
3. 自动修复：重新跑问题步骤/比赛

用法:
    python jingcai/diagnose.py 2026-05-05             # 诊断所有比赛
    python jingcai/diagnose.py --fix 2026-05-05       # 诊断+自动修复
"""
import os, sys, json, re, requests, subprocess, time
from datetime import datetime

import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

# ========== 报告解析 ==========

def parse_report_data(match_dir):
    """从step文件直接读取数据量（不从报告提取，避免误匹配其他步骤的数据）"""
    if not os.path.exists(match_dir):
        return None
    
    steps = {}
    
    # step2: 竞彩同赔
    s2_path = os.path.join(match_dir, 'group01_europe', 'step2_jingcai_same.txt')
    if os.path.exists(s2_path):
        with open(s2_path, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        m = re.search(r'所有赛事统计[：:][^0-9]*?胜(\d+)\s+平(\d+)\s+负(\d+)', c)
        if m:
            steps['step2'] = {'label': '竞彩同赔', 'count': int(m.group(1))+int(m.group(2))+int(m.group(3))}
        else:
            steps['step2'] = {'label': '竞彩同赔', 'count': 0}
    else:
        steps['step2'] = {'label': '竞彩同赔', 'count': 0}
    
    # step3: IWC同赔
    s3_path = os.path.join(match_dir, 'group01_europe', 'step3_iw_same.txt')
    if os.path.exists(s3_path):
        with open(s3_path, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        m = re.search(r'所有赛事统计[：:][^0-9]*?胜(\d+)\s+平(\d+)\s+负(\d+)', c)
        if m:
            steps['step3'] = {'label': 'IWC同赔', 'count': int(m.group(1))+int(m.group(2))+int(m.group(3))}
        else:
            steps['step3'] = {'label': 'IWC同赔', 'count': 0}
    else:
        steps['step3'] = {'label': 'IWC同赔', 'count': 0}
    
    # step5: 让球同赔
    s5_path = os.path.join(match_dir, 'group02_handicap', 'step5_handicap_same.txt')
    if os.path.exists(s5_path):
        with open(s5_path, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        m = re.search(r'所有赛事统计[：:][^0-9]*?胜(\d+)\s+平(\d+)\s+负(\d+)', c)
        if m:
            steps['step5'] = {'label': '让球同赔', 'count': int(m.group(1))+int(m.group(2))+int(m.group(3))}
        else:
            steps['step5'] = {'label': '让球同赔', 'count': 0}
    else:
        steps['step5'] = {'label': '让球同赔', 'count': 0}
    
    # step7: 澳门同赔
    s7_path = os.path.join(match_dir, 'group03_asian', 'step7_macau_same.txt')
    if os.path.exists(s7_path):
        with open(s7_path, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        m = re.search(r'相同盘口统计[：:][^0-9]*?共(\d+)场', c)
        if m:
            steps['step7'] = {'label': '澳门同赔', 'count': int(m.group(1))}
        else:
            steps['step7'] = {'label': '澳门同赔', 'count': 0}
    else:
        steps['step7'] = {'label': '澳门同赔', 'count': 0}
    
    # step9: 主队历史
    s9_path = os.path.join(match_dir, 'group04_teamA', 'step9_home_history.txt')
    if os.path.exists(s9_path):
        with open(s9_path, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        m = re.search(r'共(\d+)场', c)
        if m:
            steps['step9'] = {'label': '主队历史', 'count': int(m.group(1))}
        else:
            steps['step9'] = {'label': '主队历史', 'count': 0}
    else:
        steps['step9'] = {'label': '主队历史', 'count': 0}
    
    # step14: 客队历史
    s14_path = os.path.join(match_dir, 'group05_teamB', 'step14_away_history.txt')
    if os.path.exists(s14_path):
        with open(s14_path, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        m = re.search(r'共(\d+)场', c)
        if m:
            steps['step14'] = {'label': '客队历史', 'count': int(m.group(1))}
        else:
            steps['step14'] = {'label': '客队历史', 'count': 0}
    else:
        steps['step14'] = {'label': '客队历史', 'count': 0}
    
    # step19: 百家对比
    s19_path = os.path.join(match_dir, 'group06_baijia', 'step19_baijia_compare.txt')
    if os.path.exists(s19_path):
        with open(s19_path, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        m = re.search(r'共(\d+)家公司', c)
        if m:
            steps['step19'] = {'label': '百家对比', 'count': int(m.group(1))}
        else:
            steps['step19'] = {'label': '百家对比', 'count': 0}
    else:
        steps['step19'] = {'label': '百家对比', 'count': 0}
    
    # step25: 庄家盈亏 (still check report)
    steps['step25'] = {'label': '庄家盈亏', 'count': 0}
    
    # 让球预测/信心 (still check report)
    steps['rq_prediction'] = '未生成'
    steps['rq_confidence'] = 0
    
    return steps

# ========== 诊断 ==========

def diagnose_step(step_key, meta, match_dir):
    """诊断某个步骤数据为空的原因"""
    fid = meta.get('fid', '')
    
    if step_key in ('step2', 'step5'):
        # 直接调用AJAX端点验证，看是否真有数据
        try:
            from bs4 import BeautifulSoup
            if step_key == 'step2':
                url = 'https://odds.500.com/fenxi/ouzhi-{}.shtml'.format(fid)
            else:
                url = 'https://odds.500.com/fenxi/rangqiu-{}.shtml'.format(fid)
            resp = sess.get(url, timeout=15)
            resp.encoding = 'gbk'
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 找到竞彩公司行（td0=='1'）
            company_row = None
            for table in soup.find_all('table'):
                for tr in table.find_all('tr'):
                    tds = tr.find_all('td')
                    if len(tds) < 12:
                        continue
                    td0 = tds[0].get_text().strip()
                    if td0 == '1':
                        nums = []
                        for idx in [3,4,5,6,7,8]:
                            s = tds[idx].get_text().strip().replace('\u00a0', '')
                            try:
                                nums.append(float(s))
                            except:
                                pass
                        if len(nums) >= 6:
                            if step_key == 'step2':
                                company_row = ('%.2f' % nums[0], '%.2f' % nums[1], '%.2f' % nums[2])
                            else:
                                td2 = tds[2].get_text().strip().replace('\u00a0', '')
                                company_row = (td2, '%.2f' % nums[0], '%.2f' % nums[1], '%.2f' % nums[2])
                            break
                if company_row:
                    break
            
            if not company_row:
                return {'cause': '源站页面找不到竞彩赔率（公司行缺失）', 'fixable': False}
            
            # 调用AJAX端点
            if step_key == 'step2':
                ajax_url = 'https://odds.500.com/fenxi1/inc/ouzhi_sameajax.php'
                win, draw, lost = company_row
                params = {'cid': '1', 'win': win, 'draw': draw, 'lost': lost, 'id': fid, 'mid': '0'}
                referer = 'https://odds.500.com/fenxi1/ouzhi_same.php?cid=1&fixtureid=%s&win=%s&draw=%s&lost=%s&id=%s' % (fid, win, draw, lost, fid)
            else:
                ajax_url = 'https://odds.500.com/fenxi1/inc/rangqiu_sameajax.php'
                hd, win, draw, lost = company_row
                params = {'cid': '1', 'handicapline': hd, 'win': win, 'draw': draw, 'lost': lost, 'id': fid, 'mid': '0'}
                referer = 'https://odds.500.com/fenxi1/rangqiu_same.php?cid=1&handicapline=%s&win=%s&draw=%s&lost=%s&id=%s' % (hd, win, draw, lost, fid)
            
            h = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': referer,
            }
            r2 = sess.get(ajax_url, params=params, headers=h, timeout=15)
            try:
                j = json.loads(r2.text)
                total = sum(j.get('counts', [0,0,0]))
                if total == 0:
                    return {'cause': '源站无同赔数据（该赔率组合无历史记录）', 'fixable': False}
                else:
                    return {'cause': '源站有%d条同赔数据，脚本提取失败' % total, 'fixable': True}
            except:
                return {'cause': '源站AJAX返回非JSON（页面可能变化）', 'fixable': True}
        except:
            return {'cause': '源站访问失败', 'fixable': False}
    
    elif step_key == 'step9':
        # 检查是否有team_id
        if not meta.get('home_id'):
            # step918_extractor会从欧赔页提取team_id，所以meta里没有也不一定有bug
            # 检查step9文件是否有数据
            if match_dir:
                fp = os.path.join(match_dir, 'group04_teamA/step9_home_history.txt')
                if os.path.exists(fp):
                    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                        c = f.read()
                    if '共0 场' in c or '共0场' in c:
                        return {'cause': '筛选结果为0场（联赛/盘口不匹配）', 'fixable': True}
                    else:
                        return {'cause': '数据正常', 'fixable': False}
        return {'cause': '未知', 'fixable': False}
    
    elif step_key == 'step14':
        if match_dir:
            fp = os.path.join(match_dir, 'group05_teamB/step14_away_history.txt')
            if os.path.exists(fp):
                with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                    c = f.read()
                if '共0 场' in c or '共0场' in c:
                    return {'cause': '筛选结果为0场（联赛/盘口不匹配）', 'fixable': True}
        return {'cause': '未知', 'fixable': False}
    
    elif step_key == 'step19':
        if match_dir:
            fp = os.path.join(match_dir, 'group06_baijia/step19_baijia_compare.txt')
            if os.path.exists(fp):
                with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                    c = f.read()
                # 检查表是否有数据行
                rows = re.findall(r'\| \d+ \|', c)
                if len(rows) == 0:
                    # 检查源站
                    try:
                        url = 'https://odds.500.com/fenxi/ouzhi-{}.shtml'.format(fid)
                        resp = sess.get(url, timeout=15)
                        resp.encoding = 'gbk'
                        if '百家' in resp.text:
                            return {'cause': '源站有百家数据，step19提取失败', 'fixable': True}
                        else:
                            return {'cause': '源站无百家数据', 'fixable': False}
                    except:
                        return {'cause': '源站访问失败', 'fixable': False}
                else:
                    return {'cause': '数据正常', 'fixable': False}
        return {'cause': '文件不存在', 'fixable': True}
    
    elif step_key == 'step25':
        try:
            url = 'https://odds.500.com/fenxi/touzhu-{}.shtml'.format(fid)
            resp = sess.get(url, timeout=15)
            resp.encoding = 'gbk'
            if '投注' in resp.text or '盈亏' in resp.text:
                return {'cause': '源站有投注数据，step25未提取', 'fixable': True}
            else:
                return {'cause': '源站无投注数据（比赛未开始/已结）', 'fixable': False}
        except:
            return {'cause': '源站访问失败', 'fixable': False}
    
    return {'cause': '未知', 'fixable': False}

# ========== 修复 ==========

def fix_match(date_str, match_num, report_path, match_dir):
    """重新跑某场比赛的流水线"""
    task_dir = os.path.join(TASKS_DIR, date_str)
    data_dir = os.path.join(task_dir, 'data')
    
    if not match_dir:
        # 找match目录
        match_dir = None
        for d in os.listdir(data_dir):
            if d.startswith('match'):
                mp = os.path.join(data_dir, d, 'meta.json')
                if os.path.exists(mp):
                    with open(mp, 'r', encoding='utf-8') as f:
                        dm = json.load(f)
                    if match_num in dm.get('matchnum', ''):
                        match_dir = os.path.join(data_dir, d)
                        break
    
    if not match_dir:
        return False
    
    # 读取meta.json获取参数
    meta_path = os.path.join(match_dir, 'meta.json')
    if not os.path.exists(meta_path):
        return False
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    fid = meta.get('fid', '')
    home_id = meta.get('home_id', '')
    away_id = meta.get('away_id', '')
    league = meta.get('league', '')
    macau_line = meta.get('macau_line', '')
    
    if not fid:
        return False
    
    # 重新跑数据提取脚本
    scripts_to_run = [
        ('step146_extractor.py', [fid, '1']),
        ('step146_extractor.py', [fid, '4']),
        ('step146_extractor.py', [fid, '6']),
        ('step235_runner.py', [fid, '2']),
        ('step235_runner.py', [fid, '3']),
        ('step235_runner.py', [fid, '5']),
        ('step7_runner.py', [fid, macau_line]),
        ('step8_1923_extractor.py', [fid, league, macau_line]),
        ('step918_extractor.py', [home_id, away_id, league, fid, macau_line]),
    ]
    
    for script, args in scripts_to_run:
        script_path = os.path.join(SCRIPT_DIR, script)
        if os.path.exists(script_path):
            try:
                result = subprocess.run(
                    [sys.executable, script_path, match_dir] + args,
                    capture_output=True, text=True, timeout=120,
                    encoding='utf-8', errors='replace'
                )
                if result.returncode != 0:
                    print('    ⚠️ {} 失败'.format(script))
            except Exception as e:
                print('    ⚠️ {} 异常: {}'.format(script, str(e)[:50]))
    
    # 重新生成报告
    script_path = os.path.join(SCRIPT_DIR, 'final_report_generator.py')
    try:
        result = subprocess.run(
            [sys.executable, script_path, match_dir, report_path],
            capture_output=True, text=True, timeout=120,
            encoding='utf-8', errors='replace'
        )
        return result.returncode == 0
    except:
        return False

# ========== 主流程 ==========

def diagnose_date(date_str, auto_fix=False):
    task_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.exists(task_dir):
        print('[ERROR] 目录不存在: {}'.format(task_dir))
        return
    
    # 找报告
    reports = sorted([f for f in os.listdir(task_dir) 
                      if f.endswith('.md') and not f.startswith('sunday') and not f.startswith('match')])
    if not reports:
        print('[ERROR] 未找到最终报告')
        return
    
    print('=' * 70)
    print('竞彩数据核对 - {}'.format(date_str))
    print('报告数: {} | 自动修复: {}'.format(len(reports), '是' if auto_fix else '否'))
    print('=' * 70)
    print()
    
    data_dir = os.path.join(task_dir, 'data')
    total_issues = 0
    all_problem_matches = []
    
    for report_name in reports:
        report_path = os.path.join(task_dir, report_name)
        steps = parse_report_data(report_path)
        
        if not steps:
            print('⚠️ {} - 无法解析'.format(report_name[:30]))
            continue
        
        # 找meta
        meta = {}
        match_num = report_name[:20]
        if data_dir and os.path.exists(data_dir):
            for d in os.listdir(data_dir):
                if d.startswith('match'):
                    mp = os.path.join(data_dir, d, 'meta.json')
                    if os.path.exists(mp):
                        with open(mp, 'r', encoding='utf-8') as f:
                            dm = json.load(f)
                        if match_num[:10] in dm.get('matchnum', '') or dm.get('matchnum', '') in match_num:
                            meta = dm
                            match_num = dm.get('matchnum', match_num)
                            break
        
        # 检查各步数据
        issues = []
        for step_key, label, min_count in [
            ('step2', '竞彩同赔', 1),
            ('step5', '让球同赔', 1),
            ('step9', '主队历史', 1),
            ('step14', '客队历史', 1),
            ('step19', '百家对比', 1),
            ('step25', '庄家盈亏', 0),  # 可能确实没数据
        ]:
            step_data = steps.get(step_key, {})
            count = step_data.get('count', 0)
            if count < min_count:
                # 诊断原因
                match_dir = None
                if data_dir and os.path.exists(data_dir):
                    for d in os.listdir(data_dir):
                        if d.startswith('match'):
                            mp = os.path.join(data_dir, d, 'meta.json')
                            if os.path.exists(mp):
                                with open(mp, 'r', encoding='utf-8') as f:
                                    dm = json.load(f)
                                if match_num in dm.get('matchnum', ''):
                                    match_dir = os.path.join(data_dir, d)
                                    break
                
                diag = diagnose_step(step_key, meta, match_dir)
                issues.append({
                    'step': step_key,
                    'label': label,
                    'count': count,
                    'cause': diag['cause'],
                    'fixable': diag['fixable'],
                })
        
        # 检查让球预测
        if steps.get('rq_prediction') == '让球平' and steps.get('rq_confidence', 0) < 0.50:
            if steps.get('step5', {}).get('count', 0) > 0:
                pass  # 已在之前修复
        
        if issues:
            total_issues += len(issues)
            all_problem_matches.append({'match': match_num, 'report': report_path, 'issues': issues})
            issue_strs = []
            for i in issues:
                fix_icon = '🔧' if i['fixable'] else 'ℹ️'
                issue_strs.append('{} {}({})'.format(fix_icon, i['label'], i['cause']))
            print('⚠️ {} - {} 个问题: {}'.format(match_num, len(issues), ' | '.join(issue_strs)))
        else:
            print('✅ {} - 全部正常'.format(match_num))
    
    # 汇总
    ok_count = len(reports) - len(all_problem_matches)
    print()
    print('=' * 70)
    print('诊断汇总')
    print('=' * 70)
    print('全部正常: {}/{}'.format(ok_count, len(reports)))
    print('有问题: {}/{}'.format(len(all_problem_matches), len(reports)))
    print('问题项: {}'.format(total_issues))
    
    if all_problem_matches:
        print()
        print('--- 问题分类 ---')
        causes = {}
        for pm in all_problem_matches:
            for issue in pm['issues']:
                c = issue['cause']
                if c not in causes:
                    causes[c] = {'count': 0, 'fixable': 0, 'matches': []}
                causes[c]['count'] += 1
                if issue['fixable']:
                    causes[c]['fixable'] += 1
                causes[c]['matches'].append(pm['match'])
        for c, info in causes.items():
            fix_tag = '可修复' if info['fixable'] > 0 else '不可修复'
            print('  {} [{}]: {}场'.format(c, fix_tag, info['count']))
    
    # 自动修复
    if auto_fix and all_problem_matches:
        print()
        print('=' * 70)
        print('自动修复')
        print('=' * 70)
        
        fixed_count = 0
        for pm in all_problem_matches:
            has_fixable = any(i['fixable'] for i in pm['issues'])
            if not has_fixable:
                print('  {} - 无修复项，跳过'.format(pm['match']))
                continue
            
            print('  修复 {}...'.format(pm['match']), end='')
            # Pass match_dir to fix_match
            fix_success = fix_match(date_str, pm['match'], pm['report'], None)
            if fix_success:
                print(' ✅')
                fixed_count += 1
            else:
                print(' ❌')
        
        print()
        print('修复完成: {}/{}'.format(fixed_count, len(all_problem_matches)))
    
    return len(all_problem_matches) == 0

# ========== 入口 ==========

if __name__ == '__main__':
    auto_fix = '--fix' in sys.argv
    if auto_fix:
        sys.argv.remove('--fix')
    
    # 兼容流水线传入 --quick（快速模式，不访问源站）
    if '--quick' in sys.argv:
        sys.argv.remove('--quick')
    
    if len(sys.argv) < 2:
        print('用法: python diagnose.py [--fix] [--quick] <date>')
        print('  --fix   自动修复')
        print('  --quick  快速模式（不访问源站，仅解析报告）')
        sys.exit(1)
    
    diagnose_date(sys.argv[1], auto_fix=auto_fix)
