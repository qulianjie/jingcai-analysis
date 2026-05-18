# -*- coding: utf-8 -*-
"""Direct fix for 5/16 match30 using glob"""
import os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'tasks', '2026-05-16', 'data')

# Find all match directories
match_dirs = sorted(glob.glob(os.path.join(DATA_DIR, 'match*')))
print(f'Found {len(match_dirs)} match directories')

# Find match30 by directory name pattern
target = None
for d in match_dirs:
    if 'match30' in d:
        target = d
        print(f'Found: {d}')
        break

if not target:
    print('Match30 not found!')
    exit(1)

# Fix g4/g5
print('  Running step918...')
ret = os.system(f'python step918_extractor.py "{target}"')

# Check result
g4 = os.path.isdir(os.path.join(target, 'group04_teamA'))
g5 = os.path.isdir(os.path.join(target, 'group05_teamB'))
print(f'  g4={g4}, g5={g5}')

# Fix g6
print('  Running step8_1923...')
ret = os.system(f'python step8_1923_extractor.py "{target}"')
g6 = os.path.isdir(os.path.join(target, 'group06_baijia'))
print(f'  g6={g6}')
