# -*- coding: utf-8 -*-
"""批量反馈 - 04-03 到 04-22"""
import os, sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from batch_feedback import run_feedback_for_date
from datetime import datetime, timedelta

dates = []
d = datetime(2026, 4, 3)
end = datetime(2026, 4, 22)
while d <= end:
    dates.append(d.strftime('%Y-%m-%d'))
    d += timedelta(days=1)

print('=' * 60)
print('  批量反馈: {} ~ {}'.format(dates[0], dates[-1]))
print('  共 {} 天'.format(len(dates)))
print('=' * 60)

total_correct = 0
total_check = 0
for ds in dates:
    try:
        run_feedback_for_date(ds)
    except Exception as e:
        print('[ERR] {} {}'.format(ds, e))

print('\n' + '=' * 60)
print('  反馈完成')
print('=' * 60)
