# -*- coding: utf-8 -*-
import json, os, sys, glob, re
sys.stdout.reconfigure(encoding='utf-8')

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'

# Step 1: Build date -> {match_num -> league} from feedback
fb = json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json', encoding='utf-8'))

date_num_league = {}
for date_str, date_data in fb.get('dates', {}).items():
    mapping = {}
    for item in date_data.get('feedback', []):
        league = item.get('league', '')
        mn = item.get('match_num', '')
        if league and league != '未知' and league.strip() and mn:
            mapping[mn] = league
    if mapping:
        date_num_league[date_str] = mapping

# Step 2: Build date -> {match_num -> teams} from match directories
# Old format: match001__teamA_teamB (parse from dirname)
# New format: data/match*/meta.json (parse from meta.json)

date_num_teams = {}
for date in sorted(os.listdir(TASKS_DIR)):
    date_dir = os.path.join(TASKS_DIR, date)
    if not os.path.isdir(date_dir):
        continue
    
    mapping = {}
    
    # Old format: match001__teamA_teamB (directly in date folder)
    for d in os.listdir(date_dir):
        if not d.startswith('match'):
            continue
        # Parse "match001__teamA_teamB"
        m = re.match(r'match(\d+)__(.+)', d)
        if m:
            num = m.group(1)
            teams_raw = m.group(2)
            # Teams are separated by underscore, but team names can have multiple chars
            # The format is: teamA_teamB where _ is the separator
            # Since team names don't contain _, split on first _
            # Actually looking at examples: match001__阿德莱德_奥克兰FC
            # The double __ separates number from teams, single _ separates teams
            # But team names like "墨尔本胜利" don't have underscores
            # So split on _ and take first part as home, rest as away
            parts = teams_raw.split('_')
            if len(parts) >= 2:
                home = parts[0]
                away = '_'.join(parts[1:])  # in case away team has _ in name
                mapping[num] = f'{home}vs{away}'
    
    # New format: data/match*/meta.json
    data_dir = os.path.join(date_dir, 'data')
    if os.path.isdir(data_dir):
        for d in os.listdir(data_dir):
            if not d.startswith('match'):
                continue
            meta_file = os.path.join(data_dir, d, 'meta.json')
            if os.path.exists(meta_file):
                try:
                    meta = json.load(open(meta_file, encoding='utf-8'))
                    home = meta.get('home_team', '')
                    away = meta.get('away_team', '')
                    num_match = re.search(r'match(\d+)', d)
                    if num_match and home and away:
                        num = num_match.group(1)
                        mapping[num] = f'{home}vs{away}'
                except:
                    pass
    
    if mapping:
        date_num_teams[date] = mapping

print(f'有球队数据的日期: {len(date_num_teams)}个')
# Sample
for d in sorted(date_num_teams.keys())[:3]:
    teams = date_num_teams[d]
    print(f'  {d}: {len(teams)}场')
    for num, t in list(teams.items())[:2]:
        print(f'    {num}: {t}')

# Step 3: Build team -> league map
team_to_league = {}
for date in sorted(date_num_league.keys()):
    league_map = date_num_league[date]
    teams_map = date_num_teams.get(date, {})
    
    for num, league in league_map.items():
        teams_str = teams_map.get(num, '')
        if not teams_str or 'vs' not in teams_str:
            continue
        parts = teams_str.split('vs')
        if len(parts) != 2:
            continue
        home = parts[0].strip()
        away = parts[1].strip()
        if home not in team_to_league:
            team_to_league[home] = set()
        team_to_league[home].add(league)
        if away not in team_to_league:
            team_to_league[away] = set()
        team_to_league[away].add(league)

print(f'球队→联赛映射: {len(team_to_league)}支球队')

# Sample
print('\n球队→联赛 样本 (前20):')
count = 0
for team, leagues in sorted(team_to_league.items()):
    if count < 20:
        print(f'  {team}: {", ".join(sorted(leagues))}')
        count += 1

# Step 4: Auto-tag unknown entries
unknown_dates = [
    '2026-04-03', '2026-04-04', '2026-04-05', '2026-04-06', '2026-04-07',
    '2026-04-08', '2026-04-09', '2026-04-10', '2026-04-11', '2026-04-12',
    '2026-04-13', '2026-04-14', '2026-04-15', '2026-04-16', '2026-04-17',
    '2026-04-18', '2026-04-19', '2026-04-20', '2026-04-21', '2026-04-22',
    '2026-04-29',
]

auto_tagged = []
cannot_tag = []

for date_str in unknown_dates:
    date_data = fb.get('dates', {}).get(date_str, {})
    if not date_data:
        continue
    
    teams_map = date_num_teams.get(date_str, {})
    
    for item in date_data.get('feedback', []):
        league = item.get('league', '')
        if not league or league == '未知' or league.strip() == '':
            mn = item.get('match_num', '')
            teams_str = teams_map.get(mn, '')
            
            if not teams_str or 'vs' not in teams_str:
                cannot_tag.append({
                    'date': date_str,
                    'num': mn,
                    'teams': teams_str or '???',
                    'score': item.get('score', ''),
                })
                continue
            
            parts = teams_str.split('vs')
            if len(parts) != 2:
                cannot_tag.append({
                    'date': date_str,
                    'num': mn,
                    'teams': teams_str,
                    'score': item.get('score', ''),
                })
                continue
            
            home_team = parts[0].strip()
            away_team = parts[1].strip()
            
            home_leagues = team_to_league.get(home_team, set())
            away_leagues = team_to_league.get(away_team, set())
            
            common = home_leagues & away_leagues
            
            if len(common) == 1:
                auto_tagged.append({
                    'date': date_str,
                    'num': mn,
                    'teams': teams_str,
                    'league': list(common)[0],
                    'score': item.get('score', ''),
                })
            elif len(common) > 1:
                auto_tagged.append({
                    'date': date_str,
                    'num': mn,
                    'teams': teams_str,
                    'league': ', '.join(sorted(common)),
                    'score': item.get('score', ''),
                })
            else:
                cannot_tag.append({
                    'date': date_str,
                    'num': mn,
                    'teams': teams_str,
                    'home_leagues': ', '.join(sorted(home_leagues)) if home_leagues else '无记录',
                    'away_leagues': ', '.join(sorted(away_leagues)) if away_leagues else '无记录',
                    'score': item.get('score', ''),
                })

print(f'\n=== 结果 ===')
print(f'自动标记: {len(auto_tagged)}场')
print(f'无法标记: {len(cannot_tag)}场')

# Show auto-tagged sample
print(f'\n=== 自动标记 (前10) ===')
for t in auto_tagged[:10]:
    print(f'  [{t["date"]}] {t["num"]} {t["teams"]} → {t["league"]} ({t["score"]})')
if len(auto_tagged) > 10:
    print(f'  ... 还有{len(auto_tagged)-10}场')

# Show cannot-tagged grouped by date
print(f'\n=== 需要你确认 ({len(cannot_tag)}场) ===')
by_date = {}
for c in cannot_tag:
    d = c['date']
    if d not in by_date:
        by_date[d] = []
    by_date[d].append(c)

for d in sorted(by_date.keys()):
    items = by_date[d]
    print(f'\n[{d}] {len(items)}场:')
    for c in items:
        hl = c.get('home_leagues', '')
        al = c.get('away_leagues', '')
        if hl or al:
            print(f'  {c["num"]}  {c["teams"]}  {c["score"]}  |  主:{hl}  客:{al}')
        else:
            print(f'  {c["num"]}  {c["teams"]}  {c["score"]}')
