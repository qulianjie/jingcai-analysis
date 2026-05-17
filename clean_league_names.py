# -*- coding: utf-8 -*-
"""Clean league names: remove trailing （x场）patterns from both keys and values"""
import json, re, os

base = r'C:\Users\lianjie\.openclaw\workspace\jingcai'

# \uff08 = fullwidth (, \uff09 = fullwidth )
CLEAN_PATTERN = re.compile(u'[\uff08(]\d+\u573a\uff09')

def clean(s):
    return CLEAN_PATTERN.sub('', s).strip()

# Process league_map.json
lm_path = os.path.join(base, 'league_map.json')
with open(lm_path, encoding='utf-8') as f:
    lm = json.load(f)

key_changed = 0
val_changed = 0
new_lm = {}
for key, vals in lm.items():
    clean_key = clean(key)
    if clean_key != key:
        key_changed += 1
        print('KEY: {} -> {}'.format(repr(key), repr(clean_key)))
    
    clean_vals = []
    for v in vals:
        cv = clean(v)
        if cv != v:
            val_changed += 1
            print('VAL: {} -> {}'.format(repr(v), repr(cv)))
        if cv:
            clean_vals.append(cv)
    
    # Deduplicate
    if clean_key in new_lm:
        existing = new_lm[clean_key]
        for v in clean_vals:
            if v not in existing:
                existing.append(v)
    else:
        new_lm[clean_key] = clean_vals

print('\nleague_map.json:')
print('  Keys changed: {}'.format(key_changed))
print('  Values changed: {}'.format(val_changed))
print('  Total keys: {} -> {}'.format(len(lm), len(new_lm)))

with open(lm_path, 'w', encoding='utf-8') as f:
    json.dump(new_lm, f, ensure_ascii=False, indent=2)
print('  Saved')

# Process leagues_all.json
la_path = os.path.join(base, 'leagues_all.json')
with open(la_path, encoding='utf-8') as f:
    la = json.load(f)

la_changed = 0
for item in la:
    old_name = item['name']
    new_name = clean(old_name)
    if new_name != old_name:
        la_changed += 1
        print('  {} -> {}'.format(repr(old_name), repr(new_name)))
        item['name'] = new_name

print('\nleagues_all.json:')
print('  Changed: {}'.format(la_changed))

with open(la_path, 'w', encoding='utf-8') as f:
    json.dump(la, f, ensure_ascii=False, indent=2)
print('  Saved')

# Verify
total_vals = sum(len(v) for v in new_lm.values())
remaining = 0
for k in new_lm:
    if CLEAN_PATTERN.search(k):
        remaining += 1
for v_list in new_lm.values():
    for v in v_list:
        if CLEAN_PATTERN.search(v):
            remaining += 1

print('\nVerification: {} patterns remaining in league_map.json'.format(remaining))
