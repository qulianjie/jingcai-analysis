# -*- coding: utf-8 -*-
import os, sys, json

TASKS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
LEARNINGS_DIR = r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings'

# Read feedback
fb_path = os.path.join(LEARNINGS_DIR, 'feedback.json')
with open(fb_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

dates_data = data.get('dates', data)

# Find a match with league info
sample_count = 0
for date, date_info in list(dates_data.items())[:3]:
    matches = date_info.get('feedback', [])
    for m in matches[:2]:
        score = m.get('score', '')
        predicted = m.get('predicted', '')
        actual = m.get('actual', '')
        correct = m.get('correct', False)
        league = m.get('league', '')
        match_num = m.get('match_num', '')
        combos = m.get('combos', {})
        print(f'[{date}] {match_num} league={league} pred={predicted} actual={actual} correct={correct} score={score} combos={combos}')
        sample_count += 1
        if sample_count >= 6:
            break
    if sample_count >= 6:
        break

# Check total
total = 0
has_score = 0
for date, date_info in dates_data.items():
    matches = date_info.get('feedback', [])
    total += len(matches)
    has_score += sum(1 for x in matches if x.get('score'))

print(f'\nTotal: {total}, Has score: {has_score}, No score: {total - has_score}')

# Check how many have combos
has_combos = 0
for date, date_info in dates_data.items():
    matches = date_info.get('feedback', [])
    for m in matches:
        if m.get('combos') and len(m.get('combos', {})) > 0:
            has_combos += 1

print(f'Has combos: {has_combos}/{total}')
