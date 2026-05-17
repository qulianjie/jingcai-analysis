# -*- coding: utf-8 -*-
"""探索精细化的模式数据"""
import os, sys, json, glob, re

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

def rd(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ''

# 1. 从报告头部提取澳门亚盘、让球
for date in ['2026-05-03', '2026-05-04', '2026-05-05']:
    date_dir = os.path.join(TASKS_DIR, date)
    for f in glob.glob(os.path.join(date_dir, '周*.md')):
        content = rd(f)
        lines = content.split('\n')[:15]
        for l in lines:
            if '澳门' in l or '亚盘' in l or '让球' in l or '竞彩编号' in l:
                print(f'{os.path.basename(f)}: {l.strip()[:80]}')
        break

print('\n' + '='*60)

# 2. 检查每个match目录的json数据
for date in ['2026-05-03']:
    data_dir = os.path.join(TASKS_DIR, date, 'data')
    for md in sorted(os.listdir(data_dir))[:5]:
        md_path = os.path.join(data_dir, md)
        if not os.path.isdir(md_path):
            continue
        
        # meta.json
        meta = json.loads(rd(os.path.join(md_path, 'meta.json')))
        print(f'\n{md}:')
        print(f'  meta.matchnum={meta.get("matchnum","")}, league={meta.get("league","")}')
        
        # step25
        s25_path = os.path.join(md_path, 'step25_zhuangjia.json')
        if os.path.exists(s25_path):
            s25 = json.loads(rd(s25_path))
            print(f'  step25 data keys: {list(s25.get("data", {}).keys())}')
            for k, v in s25.get("data", {}).items():
                print(f'    {k}: {json.dumps(v, ensure_ascii=False)}')
            print(f'  step25 labels: {json.dumps(s25.get("labels", {}), ensure_ascii=False)[:100]}')
        
        # step26
        s26_path = os.path.join(md_path, 'step26_profit_ratio.json')
        if os.path.exists(s26_path):
            s26 = json.loads(rd(s26_path))
            analysis = s26.get('analysis', {})
            print(f'  step26 analysis: {json.dumps(analysis, ensure_ascii=False)[:200]}')
