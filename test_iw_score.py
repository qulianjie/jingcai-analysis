# -*- coding: utf-8 -*-
"""直接测试analyze_same_odds函数"""
import os, sys

# Add jingcai dir to path
sys.path.insert(0, r'C:\Users\lianjie\.openclaw\workspace\jingcai')

# Import the function by exec'ing the file
with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\final_conclusion_generator.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Extract just the functions we need
import re

# Read s3 file
d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10\data'
for f in os.listdir(d):
    if f.startswith('match1_'):
        md = os.path.join(d, f)
        s3_path = os.path.join(md, 'group01_europe', 'step3_interwetten_same.txt')
        with open(s3_path, 'r', encoding='utf-8') as fh:
            s3 = fh.read()
        break

# Now exec the file with a modified MD to avoid errors
exec_globals = {}
# Replace sys.argv to avoid errors
code_modified = code.replace("MD = sys.argv[1] if len(sys.argv) > 1 else ''", "MD = ''")

# Just exec the analyze_same_odds function
# Find the function definition
func_start = code.find('def analyze_same_odds(')
func_end = code.find('\ndef ', func_start + 1)
func_code = code[func_start:func_end]

exec(func_code, exec_globals)
analyze_same_odds = exec_globals['analyze_same_odds']

# Call it
result = analyze_same_odds(s3, 'IW同赔')
print('Result: %s' % result)
print('Score: %.3f' % result['score'])
print('Total: %d' % result['total'])
print('Win rate: %.1f%%' % result['win_rate'])
