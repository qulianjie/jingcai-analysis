# -*- coding: utf-8 -*-
import glob, json, os

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

for d in glob.glob(os.path.join(base, 'tasks\\2026-05-15\\data\\match*')):
    mp = os.path.join(d, 'meta.json')
    if not os.path.exists(mp):
        continue
    with open(mp, 'rb') as f:
        raw = f.read()
    meta = json.loads(raw.decode('utf-8'))
    if meta.get('fid') == '1411377':
        print(f"目录: {d}")
        print(f"Raw bytes (first 200): {raw[:200]}")
        print(f"Meta: {json.dumps(meta, ensure_ascii=False, indent=2)}")
        
        # 检查 league 字段
        league = meta.get('league', '')
        print(f"\nleague length: {len(league)}")
        print(f"league repr: {repr(league)}")
        print(f"league bytes: {league.encode('utf-8') if league else 'EMPTY'}")
