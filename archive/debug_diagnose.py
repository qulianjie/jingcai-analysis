# -*- coding: utf-8 -*-
"""Verify: diagnose false positive - step2 empty but report has data from step20/21/23"""
import sys, os, json, re
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

task_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-08'
data_dir = os.path.join(task_dir, 'data')

# Build matchnum -> report mapping
reports = {}
for f in os.listdir(task_dir):
    if f.endswith('.md'):
        with open(os.path.join(task_dir, f), 'r', encoding='utf-8', errors='replace') as fh:
            rc = fh.read()
        # Find matchnum from report
        m = re.search(r'竞彩编号:\s*(\S+)', rc)
        if m:
            reports[m.group(1)] = (f, rc)

# Build matchnum -> step2 mapping
step2_map = {}
for d in os.listdir(data_dir):
    if not d.startswith('match'): continue
    md = os.path.join(data_dir, d)
    mp = os.path.join(md, 'meta.json')
    if not os.path.exists(mp): continue
    with open(mp, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    mn = meta.get('matchnum', '')
    s2 = os.path.join(md, 'group01_europe', 'step2_jingcai_same.txt')
    if os.path.exists(s2):
        with open(s2, 'r', encoding='utf-8', errors='replace') as f:
            sc = f.read()
        m2 = re.search(r'所有赛事统计[：:][^0-9]*?胜(\d+)\s+平(\d+)\s+负(\d+)', sc)
        if m2:
            total = int(m2.group(1))+int(m2.group(2))+int(m2.group(3))
            step2_map[mn] = total
        else:
            step2_map[mn] = 0

# Compare
print('=== Step2 vs Report comparison ===')
print()
for mn in sorted(step2_map.keys()):
    s2_total = step2_map.get(mn, 0)
    if mn in reports:
        rname, rc = reports[mn]
        # Diagnose regex (matches FIRST occurrence)
        m = re.search(r'竞彩.*?同赔.*?胜(\d+)\s+平(\d+)\s+负(\d+)', rc, re.DOTALL)
        report_total = int(m.group(1))+int(m.group(2))+int(m.group(3)) if m else 0
        
        status = 'OK' if s2_total == report_total else 'MISMATCH'
        if status == 'MISMATCH':
            print('%s: step2=%d, report=%d [%s]' % (mn, s2_total, report_total, status))
            # Find where report matched
            if m:
                start = max(0, m.start() - 100)
                context = rc[start:m.end()]
                print('  Report context: ...%s' % repr(context))
    else:
        print('%s: step2=%d, report=(not found)' % (mn, s2_total))
