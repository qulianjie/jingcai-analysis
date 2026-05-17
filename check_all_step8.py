# -*- coding: utf-8 -*-
import os

data_dir = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'
for x in sorted(os.listdir(data_dir)):
    if not os.path.isdir(os.path.join(data_dir, x)):
        continue
    step8_path = os.path.join(data_dir, x, 'group03_asian', 'step8_same_league.txt')
    step19_path = os.path.join(data_dir, x, 'group06_baijia', 'step19_baijia_compare.txt')
    
    s8_rows = 0
    s19_rows = 0
    
    if os.path.exists(step8_path):
        with open(step8_path, 'r', encoding='utf-8') as f:
            lines = [l for l in f.read().split('\n') if l.startswith('|') and '---' not in l and '序号' not in l]
            s8_rows = len(lines)
    
    if os.path.exists(step19_path):
        with open(step19_path, 'r', encoding='utf-8') as f:
            lines = [l for l in f.read().split('\n') if l.startswith('|') and '---' not in l and '赛事' not in l]
            s19_rows = len(lines)
    
    print(f'{x}: step8={s8_rows} rows, step19={s19_rows} rows')
