# -*- coding: utf-8 -*-
import os, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')

def check_date(date_str):
    task_dir = os.path.join(TASKS_DIR, date_str)
    results = []
    
    # Check via meta.json
    meta_path = os.path.join(task_dir, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        return meta
    
    # Check via data/ directory
    data_dir = os.path.join(task_dir, 'data')
    if not os.path.exists(data_dir):
        return {'total': 0, 'completed': 0, 'incomplete': []}
    
    matches = sorted([d for d in os.listdir(data_dir) if d.startswith('match') and os.path.isdir(os.path.join(data_dir, d))])
    completed = 0
    incomplete = []
    
    for m in matches:
        report_file = os.path.join(task_dir, '{}.md'.format(m.replace('_', '')))
        # Also check if final_report_generator was run
        report_exists = False
        for root, dirs, files in os.walk(task_dir):
            if m.replace('match', '周一', 1).replace('_', '') + '.md' in files:
                report_exists = True
                break
            # Simple check: does the match dir have step24 output?
            if os.path.exists(os.path.join(data_dir, m, 'step24_output.txt')):
                report_exists = True
                break
        
        if report_exists:
            completed += 1
        else:
            incomplete.append(m)
    
    return {'total': len(matches), 'completed': completed, 'incomplete': incomplete}

if __name__ == '__main__':
    dates = sorted([d for d in os.listdir(TASKS_DIR) 
                    if os.path.isdir(os.path.join(TASKS_DIR, d)) and d.count('-') == 2])
    
    print('=' * 60)
    print('  未完成场次详情')
    print('=' * 60)
    
    for date_str in dates:
        info = check_date(date_str)
        total = info.get('total', 0)
        completed = info.get('completed', 0)
        incomplete = info.get('incomplete', [])
        
        if incomplete:
            print('\n{}: {}/{} 完成, {} 未完成'.format(date_str, completed, total, len(incomplete)))
            for m in incomplete:
                # Try to get team names from dir name
                name = m.split('__', 1)[-1].replace('_', ' ') if '__' in m else m
                print('  - {}'.format(name))
