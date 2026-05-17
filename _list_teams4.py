# -*- coding: utf-8 -*-
import json, os, sys, glob, re
sys.stdout.reconfigure(encoding='utf-8')

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

# Unknown dates
unknown_dates = [
    '2026-04-03', '2026-04-04', '2026-04-05', '2026-04-06', '2026-04-07',
    '2026-04-08', '2026-04-09', '2026-04-10', '2026-04-11', '2026-04-12',
    '2026-04-13', '2026-04-14', '2026-04-15', '2026-04-16', '2026-04-17',
    '2026-04-18', '2026-04-19', '2026-04-20', '2026-04-21', '2026-04-22',
    '2026-04-29',
]

# Build match_num (3-digit) -> teams from report files
match_teams = {}
for date in unknown_dates:
    date_dir = os.path.join(TASKS_DIR, date)
    if not os.path.isdir(date_dir):
        continue
    # From md reports: "周五001_阿德莱德vs奥克兰FC.md"
    for f in glob.glob(os.path.join(date_dir, '周*.md')):
        m = re.match(r'周[一二三四五六日](\d+)[_~](.+)\.md', os.path.basename(f))
        if m:
            num = m.group(1).strip()  # "001"
            teams = m.group(2).strip()  # "阿德莱德vs奥克兰FC"
            match_teams[num] = teams
    
    # From data/match*/meta.json
    data_dir = os.path.join(date_dir, 'data')
    if os.path.isdir(data_dir):
        for d in os.listdir(data_dir):
            if not d.startswith('match'):
                continue
            meta_file = os.path.join(data_dir, d, 'meta.json')
            if os.path.exists(meta_file):
                try:
                    meta = json.load(open(meta_file, encoding='utf-8'))
                    mn = meta.get('matchnum', '')  # "周五001"
                    # Extract number from "周五001" -> "001"
                    num_match = re.search(r'(\d+)$', mn)
                    if num_match:
                        num = num_match.group(1)
                        home = meta.get('home_team', '')
                        away = meta.get('away_team', '')
                        if home and away:
                            match_teams[num] = f'{home}vs{away}'
                except:
                    pass

# Now build output
fb = json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json', encoding='utf-8'))

for date_str in unknown_dates:
    date_data = fb.get('dates', {}).get(date_str, {})
    if not date_data:
        continue
    
    items = []
    for item in date_data.get('feedback', []):
        league = item.get('league', '')
        if not league or league == '未知' or league.strip() == '':
            mn = item.get('match_num', '')
            teams = match_teams.get(mn, '???')
            items.append(f'  {mn}  {teams}  {item.get("score", "")}')
    
    if items:
        print(f'\n=== [{date_str}] {len(items)}场 ===')
        for it in items:
            print(it)
