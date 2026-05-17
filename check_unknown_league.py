# -*- coding: utf-8 -*-
"""Check which dates/leagues are missing from feedback.json"""
import json, os

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

dates = data.get('dates', {})

unknown_count = 0
unknown_dates = {}
total_by_date = {}

for date, date_data in sorted(dates.items()):
    feedback_list = date_data.get('feedback', [])
    total_by_date[date] = len(feedback_list)
    unknown_in_date = 0
    for item in feedback_list:
        league = item.get('league', '')
        if not league or league == '-' or league == '未知' or league == '':
            unknown_in_date += 1
            unknown_count += 1
    if unknown_in_date > 0:
        unknown_dates[date] = '%d/%d' % (unknown_in_date, len(feedback_list))

print('Total feedback entries: %d' % sum(total_by_date.values()))
print('Unknown league count: %d' % unknown_count)
print()
print('Dates with unknown leagues:')
for d, c in sorted(unknown_dates.items()):
    print('  %s: %s' % (d, c))

# Also check actual league values distribution
print()
print('League value distribution:')
league_counts = {}
for date, date_data in dates.items():
    for item in date_data.get('feedback', []):
        league = item.get('league', '')
        if not league:
            league = '(empty string)'
        league_counts[league] = league_counts.get(league, 0) + 1

for league, count in sorted(league_counts.items(), key=lambda x: -x[1]):
    print('  "%s": %d' % (league, count))
