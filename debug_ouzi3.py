# -*- coding: utf-8 -*-
"""Diagnose step2/step5 extraction failures for 05-08"""
import sys, os, json, re
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-08\data'
task_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-08'

# Find all match dirs
dirs = sorted([d for d in os.listdir(data_dir) if d.startswith('match') and os.path.isdir(os.path.join(data_dir, d))],
              key=lambda x: int(re.findall(r'match(\d+)', x)[0]))

# Build matchnum -> match_dir mapping
match_map = {}
for d in dirs:
    mp = os.path.join(data_dir, d, 'meta.json')
    if os.path.exists(mp):
        with open(mp, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        match_map[meta.get('matchnum', '')] = d

print('=== Step2/Step5 file sizes (all Friday) ===')
print()
for mn in ['周五001','周五002','周五003','周五004','周五005','周五006',
           '周五007','周五008','周五009','周五010','周五011','周五012']:
    d = match_map.get(mn)
    if not d:
        print('%s: (not found)' % mn)
        continue
    md = os.path.join(data_dir, d)
    
    # step2
    s2 = os.path.join(md, 'group01_europe', 'step2_jingcai_same.txt')
    s2_size = 0
    s2_stat = ''
    if os.path.exists(s2):
        s2_size = os.path.getsize(s2)
        with open(s2, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        m = re.search(r'所有赛事统计[：:][^0-9]*?胜(\d+)\s+平(\d+)\s+负(\d+)', c)
        if m:
            total = int(m.group(1))+int(m.group(2))+int(m.group(3))
            s2_stat = '胜%s 平%s 负%s (共%d场)' % (m.group(1), m.group(2), m.group(3), total)
        else:
            s2_stat = 'NO STAT FOUND'
    
    # step5
    s5 = os.path.join(md, 'group02_handicap', 'step5_handicap_same.txt')
    s5_size = 0
    s5_stat = ''
    if os.path.exists(s5):
        s5_size = os.path.getsize(s5)
        with open(s5, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        m = re.search(r'所有赛事统计[：:][^0-9]*?胜(\d+)\s+平(\d+)\s+负(\d+)', c)
        if m:
            total = int(m.group(1))+int(m.group(2))+int(m.group(3))
            s5_stat = '胜%s 平%s 负%s (共%d场)' % (m.group(1), m.group(2), m.group(3), total)
        else:
            s5_stat = 'NO STAT FOUND'
    
    print('%s: step2=%db [%s] | step5=%db [%s]' % (mn, s2_size, s2_stat, s5_size, s5_stat))

# Also check the report for step2/step5 data
print()
print('=== Report step2/step5 data (Friday 010-012) ===')
for mn in ['周五010','周五011','周五012']:
    d = match_map.get(mn)
    if not d: continue
    # Find report
    reports = [f for f in os.listdir(task_dir) if f.endswith('.md') and mn[:3] in f]
    if reports:
        rp = os.path.join(task_dir, reports[0])
        with open(rp, 'r', encoding='utf-8', errors='replace') as f:
            rc = f.read()
        # Find 竞彩 section
        m = re.search(r'(竞彩.*?同赔.*?(?:胜\d+\s+平\d+\s+负\d+))', rc, re.DOTALL)
        if m:
            print('%s report: %s' % (mn, m.group(1)[:200]))
        else:
            print('%s report: NO 竞彩同赔 section found' % mn)
            # Find what's there
            if '竞彩' in rc:
                idx = rc.find('竞彩')
                print('  Context: %s' % repr(rc[max(0,idx-50):idx+200]))
            else:
                print('  No 竞彩 keyword in report')
