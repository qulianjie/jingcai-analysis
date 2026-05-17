# -*- coding: utf-8 -*-
"""从报告+step数据中提取05-09 预测=平+庄家看好=平的比赛"""
import os, sys, json, glob, re

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
LEARNINGS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings'

def rd(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ''

# Build match map for 05-09
date = '2026-05-09'
date_dir = os.path.join(TASKS_DIR, date)
data_dir = os.path.join(date_dir, 'data')

# 1. Get md reports
md_files = glob.glob(os.path.join(date_dir, '周*.md'))
report_map = {}
for f in md_files:
    m = re.match(r'(周[一二三四五六日]\d+)[_]', os.path.basename(f))
    if m:
        mn = m.group(1)
        report_map[mn] = f
        content = rd(f)
        
        # Extract prediction
        pred_m = re.search(r'\*\*竞彩预测\*\*\s*\|\s*([^（|]+)', content)
        conf_m = re.search(r'\*\*信心\*\*\s*\|\s*(\d+)%', content)
        league_m = re.search(r'🔗 比赛: ([^·]+)', content)
        
        # Extract conclusion table for score info
        score_m = re.search(r'让球预测.*?(\d+:\d+)', content)
        
        pred = pred_m.group(1).strip() if pred_m else ''
        conf = conf_m.group(1) + '%' if conf_m else ''
        league = league_m.group(1).strip() if league_m else ''
        
        # Check if prediction is 平
        if pred in ['平', '平局']:
            print(f'=== {mn} 预测=平 ===')
            print(f'  联赛: {league}')
            print(f'  信心: {conf}')
            print(f'  报告内容(前500): {content[:500]}')
            print()

# 2. Get step data from match directories
if os.path.exists(data_dir):
    for md in sorted(os.listdir(data_dir)):
        md_path = os.path.join(data_dir, md)
        if not os.path.isdir(md_path) or not md.startswith('match'):
            continue
        
        meta = json.loads(rd(os.path.join(md_path, 'meta.json'))) if os.path.exists(os.path.join(md_path, 'meta.json')) else {}
        mn = meta.get('matchnum', '')
        
        s25 = json.loads(rd(os.path.join(md_path, 'step25_zhuangjia.json'))) if os.path.exists(os.path.join(md_path, 'step25_zhuangjia.json')) else {}
        s26 = json.loads(rd(os.path.join(md_path, 'step26_profit_ratio.json'))) if os.path.exists(os.path.join(md_path, 'step26_profit_ratio.json')) else {}
        
        zhuangjia_dir = s25.get('conclusion', {}).get('庄家方向', '')
        s26_best = s26.get('analysis', {}).get('庄家最看好', '')
        s26_analysis = s26.get('analysis', {})
        
        # Check if 庄家看好=平
        if zhuangjia_dir in ['平局', '平'] or s26_best in ['平局', '平']:
            print(f'=== {md} ({mn}) 庄家看好=平 ===')
            print(f'  step25 庄家方向: {zhuangjia_dir}')
            print(f'  step26 庄家最看好: {s26_best}')
            print(f'  step26 analysis: {json.dumps(s26_analysis, ensure_ascii=False)[:300]}')
            print()
