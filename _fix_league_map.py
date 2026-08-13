#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 league_map.json 的跨级别/跨赛事污染别名（v2：只显式删除，不做自动反向清理）
"""
import json, os, shutil, time

SD = os.path.dirname(os.path.abspath(__file__))
LM_PATH = os.path.join(SD, 'league_map.json')

with open(LM_PATH, 'r', encoding='utf-8') as f:
    lm = json.load(f)

# (键, [要删除的别名]) — 显式白名单式删除
REMOVE = [
    ('沙特职业联赛', ['沙特甲', '沙特乙', '沙特U17']),
    ('沙特甲', ['沙特职业联赛']),
    ('沙特乙', ['沙特职业联赛']),
    ('沙特U17', ['沙特职业联赛']),
    ('解放者杯', ['女解放者杯', '解放者杯U20']),
    ('女解放者杯', ['解放者杯']),
    ('解放者杯U20', ['解放者杯']),
    ('欧罗巴', ['欧联U23']),
    ('欧联U23', ['欧罗巴']),
    ('亚冠', ['亚洲冠军乙级联赛', '女亚冠联']),
    ('亚洲冠军乙级联赛', ['亚冠']),
    ('女亚冠联', ['亚冠']),
    ('葡超', ['葡超杯']),
    ('葡超杯', ['葡超']),
    ('瑞超', ['瑞超杯']),
    ('瑞超杯', ['瑞超']),
    ('英足总杯', ['足总杯']),
    ('足总杯', ['英足总杯']),
]

removed = []
for k, aliases in REMOVE:
    if k in lm and isinstance(lm[k], list):
        before = list(lm[k])
        lm[k] = [a for a in lm[k] if a not in aliases]
        for a in aliases:
            if a in before and a not in lm[k]:
                removed.append(f'{k} → {a}')

bak = LM_PATH + '.bak_' + str(int(time.time()))
shutil.copy2(LM_PATH, bak)
with open(LM_PATH, 'w', encoding='utf-8') as f:
    json.dump(lm, f, ensure_ascii=False, indent=2)

print(f'备份: {os.path.basename(bak)}')
print(f'删除 {len(removed)} 条污染别名:')
for r in removed:
    print('  -', r)

# 验证合理简称保留
with open(LM_PATH, 'r', encoding='utf-8') as f:
    lm2 = json.load(f)
checks = {
    '西甲La Liga': ['西甲'],
    '德甲Bundesliga': ['德甲'],
    '意甲Serie A': ['意甲'],
    '法甲Ligue 1': ['法甲'],
    '哥伦甲': ['哥伦比亚甲级联赛'],
    '哥伦比亚甲级联赛': ['哥伦甲'],
    '英足总杯': ['英格兰足总杯'],
}
print()
print('=== 合理简称保留验证 ===')
for k, must_have in checks.items():
    ok = k in lm2 and all(a in lm2[k] for a in must_have)
    print(f'  {"✅" if ok else "❌"} {k}: {lm2.get(k)}')
