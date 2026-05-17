import json

matches_file = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-16/matches_data.json'
with open(matches_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

for gn, gd in data['groups'].items():
    if isinstance(gd, dict) and 'matches' in gd:
        for i, m in enumerate(gd['matches']):
            num = m.get('matchnum', '')
            if '007' in num or '008' in num or '009' in num:
                print(f"=== {num} ===")
                print(json.dumps(m, ensure_ascii=False, indent=2))
                print()
