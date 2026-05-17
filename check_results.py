# -*- coding: utf-8 -*-
import glob, json, os, sys

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
for d in glob.glob(os.path.join(base, 'tasks\\2026-05-15\\data\\match4*')):
    meta_path = os.path.join(d, 'meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        if meta.get('fid') == '1411377':
            print(f"目录: {d}")
            print(f"meta: league={repr(meta.get('league'))}, macau_line={repr(meta.get('macau_line'))}")
            
            step8 = os.path.join(d, 'group03_asian', 'step8_same_league.txt')
            step19 = os.path.join(d, 'group06_baijia', 'step19_baijia_compare.txt')
            
            print()
            print("=== Step 8 ===")
            if os.path.exists(step8):
                with open(step8, encoding='utf-8') as f:
                    content = f.read()
                content = content.replace('\U0001f4c5', '[date]').replace('\U0001f517', '[link]').replace('\u00b7', '.')
                print(content[:3000])
            else:
                print("文件不存在")
            
            print()
            print("=== Step 19-23 ===")
            if os.path.exists(step19):
                with open(step19, encoding='utf-8') as f:
                    content = f.read()
                content = content.replace('\U0001f4c5', '[date]').replace('\U0001f517', '[link]').replace('\u00b7', '.')
                print(content[:3000])
            else:
                print("文件不存在")
