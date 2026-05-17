# -*- coding: utf-8 -*-
content = open('jingcai/tasks/2026-05-12/周三005_布雷斯特vs斯特拉斯.md', encoding='utf-8').read()
lines = content.split('\n')

out = []
for i, line in enumerate(lines, 1):
    if line.startswith('#'):
        out.append('%d: %s' % (i, line))

with open('jingcai/report_headings.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print('Done - %d headings found' % len(out))
