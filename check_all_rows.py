# -*- coding: utf-8 -*-
"""检查报告里所有表格行"""
import os

d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10'
for f in os.listdir(d):
    if f.endswith('.md') and '001' in f:
        path = os.path.join(d, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        
        print('=== All table rows (first 3 cols) ===')
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('|') and len(stripped) > 10:
                parts = [p.strip() for p in stripped.split('|') if p.strip()]
                if len(parts) >= 3:
                    safe = ''.join(c if ord(c) < 128 else '?' for c in stripped)
                    print('  %s' % safe[:150])
        break
