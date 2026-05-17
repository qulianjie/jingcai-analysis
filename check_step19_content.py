import os

matches = [
    ('2026-05-08', 'match11_赫尔城__米尔沃尔'),
    ('2026-05-09', 'match7_米堡__南安普敦'),
    ('2026-05-11', 'match6_米尔沃尔__赫尔城'),
    ('2026-05-12', 'match7_南安普敦__米堡'),
    ('2026-05-12', 'match17_南安普敦__米堡'),
]

for date, name in matches:
    step19 = 'jingcai/tasks/%s/data/%s/group06_baijia/step19_baijia_compare.txt' % (date, name)
    print('='*50)
    print('%s/%s' % (date, name))
    
    if os.path.exists(step19):
        with open(step19, 'r', encoding='utf-8') as f:
            content = f.read()
        print('  size: %d bytes' % len(content))
        print('  content:')
        print('  ' + '\n  '.join(content[:1000].split('\n')[:10]))
    else:
        print('  MISSING')
