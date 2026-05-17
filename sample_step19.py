# -*- coding: utf-8 -*-
import os, glob, sys

sys.stdout = open('jingcai/step19_sample.txt', 'w', encoding='utf-8')

files = glob.glob('jingcai/tasks/2026-05-12/data/match*/group06_baijia/step19_baijia_compare.txt')
print('Found: %d files\n' % len(files))

for i, f in enumerate(sorted(files)[:5]):
    size = os.path.getsize(f)
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    print('=== %s (%d bytes) ===' % (f, size))
    print(content[:2000])
    print('')

sys.stdout.close()
print('Done')
