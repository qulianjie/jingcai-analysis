# -*- coding: utf-8 -*-
import json, os, sys, glob, re
sys.stdout.reconfigure(encoding='utf-8')

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

# Unknown dates
unknown_dates = {
    '2026-04-03', '2026-04-04', '2026-04-05', '2026-04-06', '2026-04-07',
    '2026-04-08', '2026-04-09', '2026-04-10', '2026-04-11', '2026-04-12',
    '2026-04-13', '2026-04-14', '2026-04-15', '2026-04-16', '2026-04-17',
    '2026-04-18', '2026-04-19', '2026-04-20', '2026-04-21', '2026-04-22',
    '2026-04-29',
}

# Get match_num -> match_name from report files
match_map = {}
for date in unknown_dates:
    date_dir = os.path.join(TASKS_DIR, date)
    if not os.path.isdir(date_dir):
        continue
    # Try md reports
    for f in glob.glob(os.path.join(date_dir, '周*.md')):
        m = re.match(r'([^_]+)[_~](.+)\.md', os.path.basename(f))
        if m:
            match_num = m.group(1).strip()
            teams = m.group(2).strip()
            if match_num not in match_map:
                match_map[match_num] = {}
            match_map[match_num][date] = teams
    
    # Try from feedback.json
    fb_file = os.path.join(date_dir, 'feedback.json')
    if os.path.exists(fb_file):
        pass  # feedback.json doesn't have team names directly

# Build output by date with team names
unknown_unknown_dates = []
fb = json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json', encoding='utf-8'))

by_date = {}
for date_str, date_data in sorted(fb.get('dates', {}).items()):
    if date_str not in unknown_dates:
        continue
    items = []
    for item in date_data.get('feedback', []):
        league = item.get('league', '')
        if not league or league == '未知' or league.strip() == '':
            mn = item.get('match_num', '')
            # Normalize to 3-digit
            if mn and not mn.startswith('周'):
                try:
                    from datetime import datetime as dt
                    dt_obj = dt.strptime(date_str, '%Y-%m-%d')
                    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
                    mn = weekday_names[dt_obj.weekday()] + mn[2:]
                except:
                    pass
            if mn and len(mn) >= 3 and mn[0] == '周':
                prefix = mn[:2] if len(mn) >= 2 and mn[:2] in ['周一','周二','周三','周四','周五','周六','周日'] else mn[:3]
                num_part = mn[2:] if len(prefix) == 2 else mn[3:]
                if num_part.isdigit() and len(num_part) < 3:
                    mn = prefix + num_part.zfill(3)
            
            teams = ''
            if mn in match_map and date_str in match_map[mn]:
                teams = match_map[mn][date_str]
            
            items.append({
                'num': mn,
                'teams': teams,
                'score': item.get('score', ''),
            })
    if items:
        by_date[date_str] = items

# Output
for date_str in sorted(by_date.keys()):
    items = by_date[date_str]
    # Extract weekday from first item
    print(f'\n=== [{date_str}] {len(items)}场 ===')
    for it in items:
        num = it['num']
        teams = it['teams'] if it['teams'] else '???（无报告文件）'
        print(f'  {num}  {teams}  {it["score"]}')
