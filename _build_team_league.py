# -*- coding: utf-8 -*-
import json, os, sys, glob, re
sys.stdout.reconfigure(encoding='utf-8')

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

# Strategy: from ALL dates that HAVE league data in feedback.json,
# extract team names from md report filenames, build team->league map

fb = json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json', encoding='utf-8'))

# Step 1: Build match_num -> league from feedback entries that HAVE league
num_to_league = {}  # "001" -> "英超"
for date_str, date_data in fb.get('dates', {}).items():
    for item in date_data.get('feedback', []):
        league = item.get('league', '')
        mn = item.get('match_num', '')
        if league and league != '未知' and league.strip() and mn:
            if mn not in num_to_league:
                num_to_league[mn] = set()
            num_to_league[mn].add(league)

print(f'编号→联赛映射: {len(num_to_league)}个编号')

# Step 2: Build match_num -> teams from md report filenames
num_to_teams = {}  # "001" -> "曼城vs曼联"
for date in sorted(os.listdir(TASKS_DIR)):
    date_dir = os.path.join(TASKS_DIR, date)
    if not os.path.isdir(date_dir):
        continue
    for f in glob.glob(os.path.join(date_dir, '周*.md')):
        m = re.match(r'周[一二三四五六日](\d+)[_~](.+)\.md', os.path.basename(f))
        if m:
            num = m.group(1).strip()
            teams = m.group(2).strip()
            num_to_teams[num] = teams

print(f'编号→球队映射: {len(num_to_teams)}个编号')

# Step 3: Build team -> league map
team_to_league = {}
for num, league_set in num_to_league.items():
    teams_str = num_to_teams.get(num, '')
    if not teams_str or 'vs' not in teams_str:
        continue
    parts = teams_str.split('vs')
    if len(parts) != 2:
        continue
    home = parts[0].strip()
    away = parts[1].strip()
    for league in league_set:
        if home not in team_to_league:
            team_to_league[home] = set()
        team_to_league[home].add(league)
        if away not in team_to_league:
            team_to_league[away] = set()
        team_to_league[away].add(league)

print(f'球队→联赛映射: {len(team_to_league)}支球队')

# Sample
print('\n球队→联赛 样本:')
count = 0
for team, leagues in sorted(team_to_league.items()):
    if count < 15:
        print(f'  {team}: {", ".join(sorted(leagues))}')
        count += 1
