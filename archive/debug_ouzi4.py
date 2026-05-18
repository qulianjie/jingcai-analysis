# -*- coding: utf-8 -*-
"""Debug: check why step2 files are short for 周五001 and 周五009"""
import sys, os, json, re
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-08\data'

# Check 周五001 and 周五009
for mn in ['match1_TPS图尔__赫尔辛基', 'match9_都灵__萨索洛']:
    md = os.path.join(data_dir, mn)
    mp = os.path.join(md, 'meta.json')
    if not os.path.exists(mp): continue
    with open(mp, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    fid = meta['fid']
    print('=== %s (FID=%s) ===' % (mn, fid))
    
    s2 = os.path.join(md, 'group01_europe', 'step2_jingcai_same.txt')
    if os.path.exists(s2):
        with open(s2, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        print('Step2 length: %d' % len(c))
        print('Content:')
        print(c)
    else:
        print('Step2 not found')
    
    s5 = os.path.join(md, 'group02_handicap', 'step5_handicap_same.txt')
    if os.path.exists(s5):
        with open(s5, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        print('Step5 length: %d' % len(c))
        print('Content:')
        print(c)
    print()

# Check report for 周五001
task_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-08'
reports = [f for f in os.listdir(task_dir) if f.endswith('.md') and '001_TPS' in f]
if reports:
    rp = os.path.join(task_dir, reports[0])
    with open(rp, 'r', encoding='utf-8', errors='replace') as f:
        rc = f.read()
    print('=== Report: %s ===' % reports[0])
    print('Length: %d' % len(rc))
    # Find all sections
    sections = re.findall(r'^## (.+)$', rc, re.MULTILINE)
    print('Sections: %s' % str(sections))
    # Find 竞彩 section
    idx = rc.find('竞彩')
    if idx >= 0:
        print('Context around first 竞彩: %s' % repr(rc[max(0,idx-50):idx+200]))
    # Search for 竞彩同赔 pattern
    m = re.search(r'竞彩.*?同赔.*?胜(\d+)\s+平(\d+)\s+负(\d+)', rc, re.DOTALL)
    if m:
        print('Step2 match: 胜%s 平%s 负%s' % (m.group(1), m.group(2), m.group(3)))
    else:
        print('Step2 NOT MATCHED by diagnose regex')
        # Try broader
        m2 = re.search(r'竞彩.*?胜(\d+)\s+平(\d+)\s+负(\d+)', rc, re.DOTALL)
        if m2:
            print('Broader match: 胜%s 平%s 负%s' % (m2.group(1), m2.group(2), m2.group(3)))
        else:
            print('No 竞彩 stats in report')

# Check reports for 周五003/004 (0场 case)
for mn in ['match3_帕德博恩__卡斯鲁厄', 'match4_凯泽__比勒菲']:
    md = os.path.join(data_dir, mn)
    mp = os.path.join(md, 'meta.json')
    if not os.path.exists(mp): continue
    with open(mp, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    matchnum = meta['matchnum']
    
    s2 = os.path.join(md, 'group01_europe', 'step2_jingcai_same.txt')
    if os.path.exists(s2):
        with open(s2, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        # Check if the file contains the 竞彩 section header
        has_header = '竞彩官网' in c or '相同赔率' in c
        has_stat = '共0场' in c or '胜0' in c
        print('%s: step2 header=%s stat=%s' % (matchnum, has_header, has_stat))
        # Show first 600 chars
        print(c[:600])
