# -*- coding: utf-8 -*-
"""调试analyze_same_odds函数"""
import os, re

d = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10\data'
for f in os.listdir(d):
    if f.startswith('match1_'):
        md = os.path.join(d, f)
        s3 = os.path.join(md, 'group01_europe', 'step3_interwetten_same.txt')
        if os.path.exists(s3):
            with open(s3, 'r', encoding='utf-8') as fh:
                text = fh.read()
            
            # Try to find current league
            league_match = re.search(r'当前联赛：\s*(.+)', text)
            if league_match:
                print('Current league: %s' % league_match.group(1).strip())
            else:
                print('No current league found')
            
            # Count table rows
            rows_found = 0
            for line in text.split('\n'):
                if '|' not in line or '---' in line or '赛事' in line:
                    continue
                cells = [c.strip() for c in line.split('|') if c.strip()]
                if len(cells) < 8:
                    continue
                rows_found += 1
                if rows_found <= 3:
                    print('Row %d cells=%d: %s' % (rows_found, len(cells), ' | '.join([str(c) for c in cells[:8]])))
            
            print('\nTotal rows found: %d' % rows_found)
            
            # Try stats fallback regex
            stats_match = re.search(r'胜(\d+)\s+平(\d+)\s+负(\d+)', text)
            if stats_match:
                print('Fallback stats: 胜%s 平%s 负%s' % (stats_match.group(1), stats_match.group(2), stats_match.group(3)))
            else:
                print('Fallback regex did not match')
                # Try to find the stats line
                for line in text.split('\n'):
                    if '胜' in line and '平' in line and '负' in line and '场' in line:
                        print('Stats line: %s' % ''.join(c if ord(c) < 128 else '?' for c in line)[:150])
            break
