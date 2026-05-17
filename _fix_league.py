# -*- coding: utf-8 -*-
import json, sys, re, os
sys.stdout.reconfigure(encoding='utf-8')

# 1. 先看看 feedback.json 里"联赛:未知"的反馈项，能不能反推出联赛名
fb = json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json', encoding='utf-8'))
tasks_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

unknown_count = 0
unknown_dates = set()
all_leagues_seen = set()

for date_str, date_data in fb.get('dates', {}).items():
    for item in date_data.get('feedback', []):
        league = item.get('league', '')
        match_num = item.get('match_num', '')
        if not league or league == '未知' or league == '':
            unknown_count += 1
            unknown_dates.add(date_str)
        else:
            all_leagues_seen.add(league)

print(f'联赛未知的反馈: {unknown_count} 条')
print(f'涉及日期: {len(unknown_dates)} 天')
print(f'已知联赛: {len(all_leagues_seen)} 个')
print()

# 2. 看看未知联赛涉及哪些日期
print('=== 需要查找联赛的日期 ===')
for d in sorted(unknown_dates)[:10]:
    print(f'  {d}')

# 3. 尝试从 tasks 目录读取 meta.json 补全联赛名
print()
print('=== 尝试从 meta.json 补全联赛名 ===')
fixed = 0
total_unknown = 0

for date_str, date_data in fb.get('dates', {}).items():
    for item in date_data.get('feedback', []):
        league = item.get('league', '')
        match_num = item.get('match_num', '')
        if not league or league == '未知' or league == '':
            total_unknown += 1
            # 尝试从 tasks 目录找 meta.json
            meta_paths = []
            task_dir = os.path.join(tasks_dir, date_str, 'data')
            if os.path.exists(task_dir):
                for d in os.listdir(task_dir):
                    if d.startswith('match') and os.path.isdir(os.path.join(task_dir, d)):
                        mp = os.path.join(task_dir, d, 'meta.json')
                        if os.path.exists(mp):
                            meta_paths.append(mp)
            
            # 在 meta 中找匹配的 matchnum
            found = False
            for mp in meta_paths:
                try:
                    with open(mp, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    mnum = meta.get('matchnum', '')
                    if match_num in mnum or mnum in match_num:
                        league_from_meta = meta.get('league', '')
                        if league_from_meta and league_from_meta != '未知':
                            item['league'] = league_from_meta
                            # 也更新 combos 中的联赛
                            if 'combos' in item:
                                item['combos']['league'] = league_from_meta
                            fixed += 1
                            found = True
                            print(f'  [{date_str}] {match_num}: 未知 → {league_from_meta}')
                            break
                except:
                    continue
            
            if not found:
                # 也试试在 date 根目录找
                task_root = os.path.join(tasks_dir, date_str)
                for fname in os.listdir(task_root):
                    if fname.endswith('.md') and match_num in fname:
                        # 从报告文件名提取联赛？不行，报告里没有联赛名
                        # 试试找同目录下其他文件
                        pass

print(f'\n可修复: {fixed}/{total_unknown}')
print(f'剩余: {total_unknown - fixed}')
