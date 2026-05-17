# -*- coding: utf-8 -*-
"""竞彩反馈机制 - 拉取赛果，对比预测，统计准确率"""
import os, sys, re, json
from datetime import datetime

import urllib.request
import urllib.error

TASKS_DIR = os.path.join(os.path.dirname(__file__), 'tasks')
FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), 'learnings', 'feedback.json')

def fetch_results(date_str):
    """从sporttery.cn获取比赛结果"""
    # 竞彩足球赛果页面
    url = f"https://info.sporttery.cn/jc/jczq/jczq_1.php"
    
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.sporttery.cn/jc/jczq/result/index.shtml',
    })
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('gbk', errors='replace')
    except Exception as e:
        print(f'获取赛果失败: {e}')
        return {}
    
    results = {}
    
    # 从HTML表格中提取比赛数据
    # 匹配: 期号、序号、主队、客队、比分、结果
    import re
    
    # 方法1: 查找JSON数据
    json_pattern = r'var\s+matchList\s*=\s*(\[.*?\]);'
    json_match = re.search(json_pattern, html, re.DOTALL)
    
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            for item in data:
                match_num = str(item.get('matchNum', item.get('id', '')))
                home = item.get('homeTeamName', item.get('home', ''))
                away = item.get('awayTeamName', item.get('away', ''))
                score = item.get('result', item.get('score', ''))
                
                if ':' in str(score):
                    parts = str(score).split(':')
                    if len(parts) == 2:
                        try:
                            h_score = int(parts[0])
                            a_score = int(parts[1])
                            if h_score > a_score:
                                result = '胜'
                            elif h_score == a_score:
                                result = '平'
                            else:
                                result = '负'
                            results[match_num] = {
                                'match_name': f'{home}vs{away}',
                                'score': str(score),
                                'actual': result,
                            }
                        except ValueError:
                            pass
        except json.JSONDecodeError:
            pass
    
    # 方法2: 正则解析HTML表格
    if not results:
        # 匹配 <td>内容</td> 模式
        td_pattern = r'<td[^>]*>([^<]*)</td>'
        tds = re.findall(td_pattern, html)
        
        i = 0
        while i < len(tds) - 5:
            cell = tds[i].strip()
            if cell.isdigit() and len(cell) >= 3:
                match_num = cell
                home = tds[i+1].strip() if i+1 < len(tds) else ''
                away = tds[i+2].strip() if i+2 < len(tds) else ''
                score = tds[i+3].strip() if i+3 < len(tds) else ''
                
                if ':' in score:
                    parts = score.split(':')
                    if len(parts) == 2:
                        try:
                            h_score = int(parts[0])
                            a_score = int(parts[1])
                            if h_score > a_score:
                                result = '胜'
                            elif h_score == a_score:
                                result = '平'
                            else:
                                result = '负'
                            results[match_num] = {
                                'match_name': f'{home}vs{away}',
                                'score': score,
                                'actual': result,
                            }
                        except ValueError:
                            pass
            i += 1
    
    return results

def load_predictions(date_str):
    """从报告文件中加载预测结论（搜索根目录 + data/ 子目录）"""
    task_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.exists(task_dir):
        return {}
    
    predictions = {}
    
    # 搜索路径：根目录（organize_data 后报告仍在根目录）
    # + data/ 子目录（pipeline 整理后 match 目录在 data/ 下）
    search_dirs = [task_dir]
    data_dir = os.path.join(task_dir, 'data')
    if os.path.exists(data_dir):
        search_dirs.append(data_dir)
        for d in os.listdir(data_dir):
            dp = os.path.join(data_dir, d)
            if os.path.isdir(dp):
                search_dirs.append(dp)
    
    for search_dir in search_dirs:
        for f in os.listdir(search_dir):
            if not f.endswith('.md'):
                continue
            
            fpath = os.path.join(search_dir, f)
            if not os.path.isfile(fpath):
                continue
            
            # 跳过已解析的（根目录优先）
            tmp_match = re.search(r'(周[一二三四五六日])(\d{3})', f)
            if tmp_match and tmp_match.group(2) in predictions:
                continue
            
            try:
                with open(fpath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
            except Exception:
                continue
            
            match_num_match = re.search(r'(周[一二三四五六日])(\d{3})', f)
            if not match_num_match:
                continue
            match_num = match_num_match.group(2)
            
            pred = ''
            rec_match = re.search(r'\*\*推荐\*\*\s*\|\s*([^\|]+)', content)
            if rec_match:
                rec_text = rec_match.group(1).strip()
                if '主胜' in rec_text or '胜' in rec_text and '客' not in rec_text:
                    pred = '胜'
                elif '客胜' in rec_text:
                    pred = '负'
                elif '平' in rec_text:
                    pred = '平'
                elif '不败' in rec_text:
                    pred = '胜/平'
                elif '分胜负' in rec_text:
                    pred = '胜/负'
            
            if match_num not in predictions:
                predictions[match_num] = {
                    'predicted': pred,
                    'match_name': f,
                }
    
    return predictions

def compare_methods(match_data, date_str):
    """对比各方法的准确率"""
    task_dir = os.path.join(TASKS_DIR, date_str)
    data_dir = os.path.join(task_dir, 'data')
    
    # 搜索路径：data/ 子目录（pipeline整理后） + 根目录（整理前）
    search_dirs = []
    if os.path.exists(data_dir):
        search_dirs.append(data_dir)
    if os.path.exists(task_dir):
        search_dirs.append(task_dir)
    
    match_num = str(match_data.get('match_num', ''))
    match_name = match_data.get('match_name', '').replace('vs', '_')
    
    # 查找对应的match目录
    match_dir = None
    for sd in search_dirs:
        for d in os.listdir(sd):
            if not d.startswith('match'):
                continue
            dp = os.path.join(sd, d)
            if not os.path.isdir(dp):
                continue
            # 按match_num匹配
            if match_num and match_num in d:
                match_dir = dp
                break
            # 按名称匹配
            if match_name and match_name in d:
                match_dir = dp
                break
        if match_dir:
            break
    
    if not match_dir or not os.path.exists(match_dir):
        return {'comparisons': [], 'combos': {}}
    
    actual = match_data.get('actual', '')
    
    # 读取各步骤结果
    comparisons = []
    
    # step5: 让球同赔
    s5_path = os.path.join(match_dir, 'group02_handicap', 'step05_handicap_same.md')
    if os.path.exists(s5_path):
        with open(s5_path, 'r', encoding='utf-8') as fh:
            s5 = fh.read()
        
        # 提取同赔胜/平/负统计
        win = re.findall(r'胜(\d+)', s5)
        draw = re.findall(r'平(\d+)', s5)
        loss = re.findall(r'负(\d+)', s5)
        
        if win or draw or loss:
            pred = '胜' if sum(int(x) for x in win) > sum(int(x) for x in draw) else \
                   '平' if sum(int(x) for x in draw) > sum(int(x) for x in win) else '负'
            comparisons.append({
                'method': '让球同赔',
                'predicted': pred,
                'actual': actual,
                'correct': pred == actual,
            })
    
    # step2: 竞彩同赔
    s2_path = os.path.join(match_dir, 'group01_europe', 'step02_europe_same.md')
    if os.path.exists(s2_path):
        with open(s2_path, 'r', encoding='utf-8') as fh:
            s2 = fh.read()
        
        win = re.findall(r'主胜.*?(\d+)', s2)
        draw = re.findall(r'平.*?(\d+)', s2)
        loss = re.findall(r'客胜.*?(\d+)', s2)
        
        if win or draw or loss:
            pred = '胜' if sum(int(x) for x in win) >= sum(int(x) for x in draw) + sum(int(x) for x in loss) else \
                   '平' if sum(int(x) for x in draw) > sum(int(x) for x in win) else '负'
            comparisons.append({
                'method': '竞彩同赔',
                'predicted': pred,
                'actual': actual,
                'correct': pred == actual,
            })
    
    # step24: 盘路匹配
    s24_path = os.path.join(match_dir, 'step24_panlu_match.json')
    if os.path.exists(s24_path):
        try:
            with open(s24_path, 'r', encoding='utf-8') as fh:
                raw = fh.read().strip()
            if raw:
                s24 = json.loads(raw)
                
                pred = s24.get('main_result', s24.get('recommended', ''))
                if pred:
                    comparisons.append({
                        'method': '盘路匹配24',
                        'predicted': pred,
                        'actual': actual,
                        'correct': pred == actual,
                    })
        except (json.JSONDecodeError, ValueError):
            pass
    
    # 计算组合
    combos = {}
    methods_by_name = {c['method']: c for c in comparisons}
    
    # 两两组合
    method_names = list(methods_by_name.keys())
    for i, m1 in enumerate(method_names):
        for m2 in method_names[i+1:]:
            key = f'{m1}+{m2}'
            if methods_by_name[m1]['correct'] and methods_by_name[m2]['correct']:
                combos[f'一致_{key}'] = {'total': 1, 'correct': 1}
            else:
                combos[f'一致_{key}'] = {'total': 1, 'correct': 0}
    
    return {'comparisons': comparisons, 'combos': combos}

def run_feedback(date_str):
    """执行反馈流程"""
    print(f'=== 竞彩反馈: {date_str} ===')
    
    # 1. 获取赛果
    print('获取赛果...')
    results = fetch_results(date_str)
    
    if not results:
        # Fallback: 使用本地数据
        print('网络赛果获取失败，使用本地数据...')
        results = {}
        # 从报告文件中提取比分信息
        task_dir = os.path.join(TASKS_DIR, date_str)
        if os.path.exists(task_dir):
            for f in os.listdir(task_dir):
                if not f.endswith('.md'):
                    continue
                match_num_match = re.search(r'(周[一二三四五六日])(\d{3})', f)
                if match_num_match:
                    match_num = match_num_match.group(2)
                    results[match_num] = {
                        'match_name': f,
                        'score': '待查',
                        'actual': '待查',
                    }
    
    print(f'找到 {len(results)} 场比赛')
    
    # 2. 加载预测
    print('加载预测...')
    predictions = load_predictions(date_str)
    
    # 3. 对比
    print('对比预测 vs 实际...')
    feedback = []
    
    for match_num, result_data in results.items():
        pred_data = predictions.get(match_num, {})
        
        # 对比各方法
        method_data = compare_methods(result_data, date_str)
        
        item = {
            'match_num': match_num,
            'match_name': result_data.get('match_name', ''),
            'score': result_data.get('score', ''),
            'actual': result_data.get('actual', ''),
            'predicted': pred_data.get('predicted', ''),
            'comparisons': method_data['comparisons'],
            'combos': method_data['combos'],
        }
        feedback.append(item)
    
    # 4. 统计
    print('统计准确率...')
    total_matches = len(feedback)
    
    # 方法准确率统计
    method_stats = {}
    combo_stats = {}
    
    for item in feedback:
        for c in item['comparisons']:
            m = c['method']
            if m not in method_stats:
                method_stats[m] = {'total': 0, 'correct': 0}
            method_stats[m]['total'] += 1
            if c['correct']:
                method_stats[m]['correct'] += 1
        
        for combo_key, combo_data in item['combos'].items():
            if combo_key not in combo_stats:
                combo_stats[combo_key] = {'total': 0, 'correct': 0}
            combo_stats[combo_key]['total'] += combo_data['total']
            combo_stats[combo_key]['correct'] += combo_data['correct']
    
    # 输出结果
    print(f'\n=== 比赛结果 ===')
    for item in feedback:
        pred = item.get('predicted', '-')
        actual = item.get('actual', '-')
        status = '✅' if pred == actual else ('⚠️' if actual == '待查' else '❌')
        print(f'{item["match_num"]} {item["match_name"]} | 预测:{pred} 实际:{actual} {status} | 比分:{item["score"]}')
    
    print(f'\n=== 方法准确率 ===')
    for method, stats in sorted(method_stats.items(), key=lambda x: x[1]['correct']/max(x[1]['total'],1), reverse=True):
        rate = stats['correct'] / max(stats['total'], 1) * 100
        print(f'{method}: {stats["correct"]}/{stats["total"]} ({rate:.0f}%)')
    
    print(f'\n=== 组合准确率 ===')
    for combo, stats in sorted(combo_stats.items(), key=lambda x: x[1]['correct']/max(x[1]['total'],1), reverse=True):
        if stats['total'] >= 1:
            rate = stats['correct'] / stats['total'] * 100
            print(f'{combo}: {stats["correct"]}/{stats["total"]} ({rate:.0f}%)')
    
    # 5. 保存
    print(f'\n保存反馈数据...')
    
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, 'r', encoding='utf-8') as fh:
            all_feedback = json.loads(fh.read())
    else:
        all_feedback = {'dates': {}}
    
    all_feedback['dates'][date_str] = {
        'feedback_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'feedback': feedback,
        'method_stats': method_stats,
        'combo_stats': combo_stats,
        'total_matches': total_matches,
    }
    
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as fh:
        json.dump(all_feedback, fh, ensure_ascii=False, indent=2)
    
    print(f'OK: {FEEDBACK_FILE}')
    
    # 6. 生成摘要
    print(f'\n=== 摘要 ===')
    print(f'总场次: {total_matches}')
    
    if method_stats:
        best_method = max(method_stats.items(), key=lambda x: x[1]['correct']/max(x[1]['total'],1))
        best_rate = best_method[1]['correct'] / best_method[1]['total'] * 100
        print(f'最佳方法: {best_method[0]} ({best_rate:.0f}%)')
    
    if combo_stats:
        best_combo = max(combo_stats.items(), key=lambda x: x[1]['correct']/max(x[1]['total'],1))
        best_rate = best_combo[1]['correct'] / best_combo[1]['total'] * 100
        print(f'最佳组合: {best_combo[0]} ({best_rate:.0f}%)')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        from datetime import datetime, timedelta
        date_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f'反馈日期: {date_str}')
    run_feedback(date_str)
