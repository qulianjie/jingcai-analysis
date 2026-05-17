# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

fb = json.load(open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\learnings\feedback.json', encoding='utf-8'))

unknown = []
for date_str, date_data in sorted(fb.get('dates', {}).items()):
    for item in date_data.get('feedback', []):
        league = item.get('league', '')
        if not league or league == '未知' or league.strip() == '':
            unknown.append({
                'date': date_str,
                'match_num': item.get('match_num', ''),
                'score': item.get('score', ''),
                'predicted': item.get('predicted', ''),
                'actual': item.get('actual', ''),
            })

print(f'=== 联赛未知 ({len(unknown)}条) ===\n')

# 按日期分组
from collections import defaultdict
by_date = defaultdict(list)
for u in unknown:
    by_date[u['date']].append(u)

for date_str in sorted(by_date.keys()):
    items = by_date[date_str]
    print(f'\n[{date_str}] {len(items)}条:')
    for u in items:
        mn = u['match_num']
        # 确保3位编号
        if len(mn) > 2 and mn[0:2] in ['周一','周二','周三','周四','周五','周六','周日']:
            num = mn[2:]
            if len(num) < 3:
                mn = mn[:2] + num.zfill(3)
        print(f'  {mn}  比分{u["score"]}  预测:{u["predicted"]}  实际:{u["actual"]}')
