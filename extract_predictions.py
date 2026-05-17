# -*- coding: utf-8 -*-
"""
Extract predictions from match reports for Notion upload
"""
import os, json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

def extract_prediction(md_path):
    """Extract prediction info from a match report"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find prediction section
    # Look for 推荐/预测 pattern
    pred = ""
    confidence = ""
    score = ""
    
    # Try to find recommendation
    rec_patterns = [
        r'推荐[:\s]+(.+)',
        r'预测[:\s]+(.+)',
        r'竞彩推荐[:\s]+(.+)',
        r'竞彩让球推荐[:\s]+(.+)',
        r'亚盘推荐[:\s]+(.+)',
    ]
    
    for pattern in rec_patterns:
        m = re.search(pattern, content)
        if m:
            pred = m.group(1).strip()
            break
    
    # Find confidence
    conf_patterns = [
        r'信心[:\s]+(\d+%)',
        r'综合信心[:\s]+(\d+%)',
    ]
    for pattern in conf_patterns:
        m = re.search(pattern, content)
        if m:
            confidence = m.group(1)
            break
    
    # Find score prediction
    score_patterns = [
        r'比分预测[:\s]+(\S+)',
        r'预测比分[:\s]+(\S+)',
    ]
    for pattern in score_patterns:
        m = re.search(pattern, content)
        if m:
            score = m.group(1)
            break
    
    return pred, confidence, score

tasks_dir = r"C:\Users\lianjie\.openclaw\workspace\jingcai\tasks"

for date_str in ['2026-05-01', '2026-05-02', '2026-05-03', '2026-05-05']:
    date_dir = os.path.join(tasks_dir, date_str)
    if not os.path.isdir(date_dir):
        continue
    
    print(f"\n=== {date_str} ===")
    md_files = [f for f in os.listdir(date_dir) 
                if f.endswith('.md') and not f.startswith('sunday') and not f.startswith('TEMPLATE')]
    
    count = 0
    for md_file in sorted(md_files)[:5]:  # First 5
        md_path = os.path.join(date_dir, md_file)
        pred, conf, score = extract_prediction(md_path)
        
        # Extract match info from filename
        name = md_file.replace('.md', '')
        
        # Read meta.json if available
        data_dir = os.path.join(date_dir, 'data')
        meta_info = {}
        for d in os.listdir(data_dir):
            if d.startswith("match"):
                meta_path = os.path.join(data_dir, d, 'meta.json')
                if os.path.exists(meta_path):
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        m = json.load(f)
                        if m.get('matchnum') in md_file:
                            meta_info = m
                            break
        
        print(f"  {name}")
        print(f"    推荐: {pred}")
        print(f"    信心: {conf}")
        print(f"    比分: {score}")
        if meta_info:
            print(f"    联赛: {meta_info.get('league','')}")
            print(f"    主队: {meta_info.get('home','')} 客队: {meta_info.get('away','')}")
        count += 1
    
    print(f"  ... total {len(md_files)} reports")
