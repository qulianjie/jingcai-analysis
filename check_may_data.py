# -*- coding: utf-8 -*-
"""
Check what's in jingcai tasks for May and compare with Notion
"""
import os, json, sys
sys.stdout.reconfigure(encoding='utf-8')

tasks_dir = r"C:\Users\lianjie\.openclaw\workspace\jingcai\tasks"

# Check each May date
for date_str in sorted(os.listdir(tasks_dir)):
    if not date_str.startswith("2026-05"):
        continue
    date_path = os.path.join(tasks_dir, date_str)
    if not os.path.isdir(date_path):
        continue
    
    # Count match reports (md files excluding sunday_matches)
    md_files = [f for f in os.listdir(date_path) 
                if f.endswith('.md') and not f.startswith('sunday')]
    
    # Check if there's a data directory with match data
    data_path = os.path.join(date_path, 'data')
    has_data = os.path.isdir(data_path)
    
    print(f"{date_str}: {len(md_files)} reports, data_dir={has_data}")
    
    if md_files:
        for f in sorted(md_files)[:3]:
            print(f"  - {f}")
        if len(md_files) > 3:
            print(f"  ... and {len(md_files)-3} more")
