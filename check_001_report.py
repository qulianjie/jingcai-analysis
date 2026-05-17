# -*- coding: utf-8 -*-
"""检查001报告内容"""
import os, re

d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10'
report_path = None
for f in os.listdir(d):
    if f.endswith('.md') and '001' in f:
        report_path = os.path.join(d, f)
        print('Report: %s' % f)
        break

if not report_path:
    print('No report found')
    import sys
    sys.exit(1)

with open(report_path, 'r', encoding='utf-8') as fh:
    content = fh.read()

# Check for summary table
print('\n=== Summary table lines ===')
for line in content.split('\n'):
    stripped = line.strip()
    if '欧赔' in stripped or 'IW' in stripped or '澳门' in stripped or '主队' in stripped or '客队' in stripped or '百家' in stripped or '欧赔组合' in stripped:
        print(stripped[:200])

# Check for dimension table
print('\n=== 各维度信号明细 ===')
in_dim = False
for line in content.split('\n'):
    if '各维度信号明细' in line:
        in_dim = True
    if in_dim:
        print(line[:200])
        if line.strip().startswith('---'):
            break

# Check for conclusion
print('\n=== 第九部分 ===')
in_nine = False
for line in content.split('\n'):
    if '第九' in line:
        in_nine = True
    if in_nine:
        print(line[:200])
        if line.strip().startswith('---'):
            break
