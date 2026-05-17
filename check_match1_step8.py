# -*- coding: utf-8 -*-
import os, json

data_dir = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/data'

# Find match1
for d in sorted(os.listdir(data_dir)):
    if d.startswith('match1_') and not d.startswith('match10') and not d.startswith('match11'):
        match_dir = os.path.join(data_dir, d)
        
        step6_path = os.path.join(match_dir, 'group03_asian', 'step6_asian_base.txt')
        step8_path = os.path.join(match_dir, 'group03_asian', 'step8_same_league.txt')
        
        with open(step8_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Write to file to avoid encoding issues
        with open('C:/Users/lianjie/.openclaw/workspace/jingcai/step8_debug.txt', 'w', encoding='utf-8') as f:
            f.write(content[:2000])
        
        print(f'Wrote step8 debug to file ({len(content)} bytes)')
        
        # Check if it has 盘口匹配 info
        for line in content.split('\n'):
            if '匹配' in line or '盘口' in line:
                with open('C:/Users/lianjie/.openclaw/workspace/jingcai/step8_debug.txt', 'a', encoding='utf-8') as f:
                    f.write(f'\nMATCH: {line}')
        
        break
