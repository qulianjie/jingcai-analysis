# -*- coding: utf-8 -*-
"""竞彩反馈机制 - 使用本地赛果文件"""
import os, sys, re, json
from datetime import datetime

TASKS_DIR = os.path.join(os.path.dirname(__file__), 'tasks')
RESULTS_FILE = os.path.join(os.path.dirname(__file__), 'results_2026-04-29.json')
FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), 'learnings', 'feedback.json')

def load_results(date_str):
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            all_results = json.loads(f.read())
        return all_results.get(date_str, {})
    return {}

def _parse_prediction(filename, content):
    """从报告内容中提取预测结论（公共解析逻辑）"""
    match_num_match = re.search(r'(周[一二三四五六日])(\d{3})', filename)
    if not match_num_match:
        return None, None
    match_num = match_num_match.group(2)
    
    pred = ''
    rec_match = re.search(r'\*\*推荐\*\*\s*\|\s*([^\|]+)', content)
    if rec_match:
        rec_text = rec_match.group(1).strip()
        if '主胜' in rec_text or ('胜' in rec_text and '客' not in rec_text and '平' not in rec_text):
            pred = '胜'
        elif '客胜' in rec_text:
            pred = '负'
        elif '平局' in rec_text or '平' in rec_text:
            pred = '平'
        elif '不败' in rec_text:
            pred = '胜/平'
        elif '分胜负' in rec_text:
            pred = '胜/负'
    
    confidence_match = re.search(r'\*\*信心\*\*\s*\|\s*([^\|]+)', content)
    confidence = ''
    if confidence_match:
        confidence = confidence_match.group(1).strip()
    
    return match_num, {
        'predicted': pred,
        'confidence': confidence,
        'match_name': filename,
    }


def load_predictions(date_str):
    task_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.exists(task_dir):
        return {}
    
    predictions = {}
    
    # 搜索路径：根目录 + data/ 子目录（pipeline 整理后 match 目录在 data/ 下）
    search_dirs = [task_dir]
    data_dir = os.path.join(task_dir, 'data')
    if os.path.exists(data_dir):
        search_dirs.append(data_dir)
        # 还要搜索 data/ 下的 match 子目录
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
            match_num, pred_data = _parse_prediction(f, '')
            if match_num and match_num in predictions:
                continue
            
            try:
                with open(fpath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
            except Exception:
                continue
            
            match_num, pred_data = _parse_prediction(f, content)
            if match_num and match_num not in predictions:
                predictions[match_num] = pred_data
    
    return predictions

def run_feedback(date_str):
    print(f'=== 竞彩反馈：{date_str} ===')
    
    results = load_results(date_str)
    print(f'找到 {len(results)} 场比赛')
    
    predictions = load_predictions(date_str)
    print(f'找到 {len(predictions)} 个预测')
    
    feedback = []
    total_correct = 0
    total_checked = 0
    
    for match_num, result_data in results.items():
        pred_data = predictions.get(match_num, {})
        
        actual = result_data.get('result', '待查')
        predicted = pred_data.get('predicted', '-')
        confidence = pred_data.get('confidence', '-')
        
        is_correct = (predicted == actual) and actual != '待查'
        if actual != '待查':
            total_checked += 1
            if is_correct:
                total_correct += 1
        
        item = {
            'match_num': match_num,
            'match_name': f"{result_data.get('home', '')}vs{result_data.get('away', '')}",
            'score': result_data.get('score', ''),
            'actual': actual,
            'predicted': predicted,
            'confidence': confidence,
            'correct': is_correct,
        }
        feedback.append(item)
    
    # 输出到文件
    output_lines = []
    output_lines.append('=== 比赛结果对比 ===')
    output_lines.append(f'{"场次":<6} {"对阵":<25} {"比分":<8} {"预测":<8} {"信心":<15} {"实际":<6} {"结果"}')
    output_lines.append('-' * 80)
    
    for item in feedback:
        status = '[OK]' if item['correct'] else ('[?]' if item['actual'] == '待查' else '[X]')
        output_lines.append(f'{item["match_num"]:<6} {item["match_name"]:<25} {item["score"]:<8} {item["predicted"]:<8} {item["confidence"]:<15} {item["actual"]:<6} {status}')
    
    output_lines.append('')
    output_lines.append('=== 统计 ===')
    output_lines.append(f'总场次：{len(feedback)}')
    output_lines.append(f'已赛：{total_checked}')
    output_lines.append(f'待查：{len(feedback) - total_checked}')
    
    if total_checked > 0:
        accuracy = total_correct / total_checked * 100
        output_lines.append(f'正确：{total_correct}/{total_checked} ({accuracy:.1f}%)')
    
    # 按信心度分组
    high_correct, high_total = 0, 0
    mid_correct, mid_total = 0, 0
    low_correct, low_total = 0, 0
    
    for item in feedback:
        if item['actual'] == '待查':
            continue
        conf = item.get('confidence', '').lower()
        if '强' in conf or '高' in conf:
            high_total += 1
            if item['correct']: high_correct += 1
        elif '中' in conf:
            mid_total += 1
            if item['correct']: mid_correct += 1
        else:
            low_total += 1
            if item['correct']: low_correct += 1
    
    output_lines.append('')
    output_lines.append('=== 按信心度分组 ===')
    if high_total > 0:
        output_lines.append(f'强信心：{high_correct}/{high_total} ({high_correct/high_total*100:.0f}%)')
    if mid_total > 0:
        output_lines.append(f'中信心：{mid_correct}/{mid_total} ({mid_correct/mid_total*100:.0f}%)')
    if low_total > 0:
        output_lines.append(f'弱信心：{low_correct}/{low_total} ({low_correct/low_total*100:.0f}%)')
    
    # 错误分析
    errors = [item for item in feedback if not item['correct'] and item['actual'] != '待查']
    if errors:
        output_lines.append('')
        output_lines.append('=== 错误分析 ===')
        for item in errors:
            output_lines.append(f'{item["match_num"]} {item["match_name"]}: 预测{item["predicted"]} 实际{item["actual"]} (信心:{item["confidence"]})')
    
    # 保存
    output_path = os.path.join(os.path.dirname(__file__), f'feedback_{date_str}.txt')
    with open(output_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(output_lines))
    
    print(f'反馈结果已保存：{output_path}')
    
    # 保存 JSON
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, 'r', encoding='utf-8') as fh:
            all_feedback = json.loads(fh.read())
    else:
        all_feedback = {'dates': {}}
    
    all_feedback['dates'][date_str] = {
        'feedback_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'feedback': feedback,
        'total_matches': len(feedback),
        'total_checked': total_checked,
        'total_correct': total_correct,
        'accuracy': total_correct / max(total_checked, 1) * 100,
        'high_stats': {'total': high_total, 'correct': high_correct},
        'mid_stats': {'total': mid_total, 'correct': mid_correct},
        'low_stats': {'total': low_total, 'correct': low_correct},
    }
    
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as fh:
        json.dump(all_feedback, fh, ensure_ascii=False, indent=2)
    
    print(f'JSON 已保存：{FEEDBACK_FILE}')
    
    # 打印摘要
    print('')
    print('=== 快速摘要 ===')
    if total_checked > 0:
        print(f'总准确率：{total_correct}/{total_checked} ({total_correct/total_checked*100:.1f}%)')
        if high_total > 0:
            print(f'强信心：{high_correct}/{high_total} ({high_correct/high_total*100:.0f}%)')
        if mid_total > 0:
            print(f'中信心：{mid_correct}/{mid_total} ({mid_correct/mid_total*100:.0f}%)')
        if low_total > 0:
            print(f'弱信心：{low_correct}/{low_total} ({low_correct/low_total*100:.0f}%)')

if __name__ == '__main__':
    date_str = sys.argv[1] if len(sys.argv) > 1 else '2026-04-29'
    print(f'反馈日期：{date_str}')
    run_feedback(date_str)
