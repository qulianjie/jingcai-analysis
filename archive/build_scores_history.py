# -*- coding: utf-8 -*-
"""
从所有meta.json + 最终报告 提取完整的 比分+预测+结果 对照数据
输出 scores_history.json
"""
import os, sys, json, re, glob
from datetime import datetime

TASKS_DIR = os.path.join(os.path.dirname(__file__), 'tasks')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'learnings', 'scores_history.json')

def rd(path):
    if not os.path.exists(path):
        return ''
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def extract_prediction_from_report(report_content):
    """从最终报告提取预测信息"""
    pred = ''
    confidence = ''
    rq_pred = ''
    handicap = 0
    
    # 竞彩预测
    m = re.search(r'竞彩预测[：:\s]*([^\n]+)', report_content)
    if m:
        pred = m.group(1).strip()
    
    # 竞彩信心
    m = re.search(r'竞彩信心[：:\s]*([^\n]+)', report_content)
    if m:
        confidence = m.group(1).strip()
    
    # 让球预测
    m = re.search(r'让球预测[：:\s]*([^\n|]+)', report_content)
    if m:
        rq_pred = m.group(1).strip()
    
    # 让球数
    m = re.search(r'竞彩官方\s*\|\s*([+-]?\d+(?:\.\d+)?)\s*\|', report_content)
    if m:
        handicap = float(m.group(1))
    
    return pred, confidence, rq_pred, handicap

def extract_s26_data(match_dir):
    """从step26提取盘口和盈亏方向"""
    pan_kou = ''
    profit_dir = ''
    
    s26_file = os.path.join(match_dir, 'step26_profit_ratio.json')
    if os.path.exists(s26_file):
        raw = rd(s26_file)
        if raw:
            try:
                s26 = json.loads(raw)
                pan_kou = s26.get('pan_kou', '')
                profit_dir = s26.get('profit_direction', '')
            except:
                pass
    
    # Fallback: try step25
    if not profit_dir:
        s25_file = os.path.join(match_dir, 'step25_zhuangjia.json')
        if os.path.exists(s25_file):
            raw = rd(s25_file)
            if raw:
                try:
                    s25 = json.loads(raw)
                    s25_data = s25.get('data', {})
                    # Build profit direction from s25
                    parts = []
                    for key in ['主胜', '平局', '客胜']:
                        info = s25_data.get(key, {})
                        if isinstance(info, dict):
                            profit = info.get('profit', '')
                            parts.append(profit if profit else '未知')
                    profit_dir = ''.join(parts)
                except:
                    pass
    
    return pan_kou, profit_dir

def main():
    print('从meta.json和最终报告提取比分+预测+结果对照数据...\n')
    
    all_records = []
    dates_processed = []
    
    # Get all date directories
    date_dirs = sorted([d for d in os.listdir(TASKS_DIR) if re.match(r'\d{4}-\d{2}-\d{2}', d)])
    
    for date in date_dirs:
        date_dir = os.path.join(TASKS_DIR, date)
        data_dir = os.path.join(date_dir, 'data')
        
        if not os.path.exists(data_dir):
            continue
        
        # Find match directories
        match_dirs = glob.glob(os.path.join(data_dir, 'match*'))
        
        date_records = []
        for match_dir in match_dirs:
            meta_file = os.path.join(match_dir, 'meta.json')
            if not os.path.exists(meta_file):
                continue
            
            raw = rd(meta_file)
            if not raw:
                continue
            
            try:
                meta = json.loads(raw)
            except:
                continue
            
            match_num = meta.get('matchnum', '')
            home = meta.get('home', '')
            away = meta.get('away', '')
            league = meta.get('league', '')
            score = meta.get('score', '')
            
            if not match_num or not score:
                continue  # Skip if no score
            
            # Parse score
            score_parts = score.split(':')
            if len(score_parts) != 2:
                continue
            
            home_score = int(score_parts[0])
            away_score = int(score_parts[1])
            
            if home_score > away_score:
                actual_result = '胜'
            elif home_score < away_score:
                actual_result = '负'
            else:
                actual_result = '平'
            
            # Extract prediction from report
            pred = ''
            confidence = ''
            rq_pred = ''
            handicap = 0
            
            # Find report file
            report_files = glob.glob(os.path.join(date_dir, '*.md'))
            report_content = ''
            for rf in report_files:
                if match_num in os.path.basename(rf) or (home in os.path.basename(rf) and away in os.path.basename(rf)):
                    report_content = rd(rf)
                    if report_content:
                        break
            
            if report_content:
                pred, confidence, rq_pred, handicap = extract_prediction_from_report(report_content)
            
            # Extract s26 data
            pan_kou, profit_dir = extract_s26_data(match_dir)
            
            # Determine if prediction is correct
            is_correct = None
            if pred:
                pred_result = ''
                if '主胜' in pred or '3' in pred:
                    pred_result = '胜'
                elif '客胜' in pred or '0' in pred:
                    pred_result = '负'
                elif '平' in pred or '1' in pred:
                    pred_result = '平'
                is_correct = pred_result == actual_result
            
            # RQ prediction
            rq_correct = None
            if rq_pred and handicap != 0:
                adj_home = home_score - handicap
                if adj_home > away_score:
                    rq_actual = '胜'
                elif adj_home < away_score:
                    rq_actual = '负'
                else:
                    rq_actual = '平'
                rq_pred_result = ''
                if '主胜' in rq_pred or '3' in rq_pred:
                    rq_pred_result = '胜'
                elif '客胜' in rq_pred or '0' in rq_pred:
                    rq_pred_result = '负'
                elif '平' in rq_pred or '1' in rq_pred:
                    rq_pred_result = '平'
                rq_correct = rq_pred_result == rq_actual
            
            record = {
                'date': date,
                'match_num': match_num,
                'league': league,
                'home': home,
                'away': away,
                'score': score,
                'actual_result': actual_result,
                'predicted': pred,
                'confidence': confidence,
                'is_correct': is_correct,
                'rq_pred': rq_pred,
                'handicap': handicap,
                'rq_correct': rq_correct,
                'pan_kou': pan_kou,
                'profit_dir': profit_dir,
            }
            
            date_records.append(record)
        
        if date_records:
            dates_processed.append(date)
            all_records.extend(date_records)
            print(f'{date}: {len(date_records)}场有比分')
    
    # Save
    output = {
        'updated': datetime.now().isoformat(),
        'total': len(all_records),
        'dates': len(dates_processed),
        'records': all_records,
    }
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'\n✅ 共提取 {len(all_records)} 场有比分的记录')
    print(f'📄 已保存: {OUTPUT_FILE}')
    
    # Stats
    correct = sum(1 for r in all_records if r['is_correct'] == True)
    wrong = sum(1 for r in all_records if r['is_correct'] == False)
    print(f'\n竞彩预测准确率: {correct}/{correct+wrong} = {correct/max(correct+wrong,1)*100:.1f}%')
    
    rq_correct = sum(1 for r in all_records if r['rq_correct'] == True)
    rq_wrong = sum(1 for r in all_records if r['rq_correct'] == False)
    if rq_correct + rq_wrong > 0:
        print(f'让球预测准确率: {rq_correct}/{rq_correct+rq_wrong} = {rq_correct/(rq_correct+rq_wrong)*100:.1f}%')

if __name__ == '__main__':
    main()
