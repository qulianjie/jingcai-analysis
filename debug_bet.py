import json

with open(r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-04-29\data\step25_zhuangjia.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(json.dumps(data.get('data'), indent=2, ensure_ascii=False))
