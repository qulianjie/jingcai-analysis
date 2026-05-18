# -*- coding: utf-8 -*-
import os, sys, re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATE_DIR = os.path.join(SCRIPT_DIR, 'tasks', '2026-05-01')

for f in os.listdir(DATE_DIR):
    if not f.endswith('.md') or re.match(r'周[一二三四五六日]\d{3}_', f):
        continue
    
    path = os.path.join(DATE_DIR, f)
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    
    m = re.search(r'周[一二三四五六日]\d{3}_[^\s#\\/:*?"<>]+', content)
    if not m:
        print('SKIP: ' + f)
        continue
    
    new_fn = m.group(0) + '.md'
    if new_fn == f:
        continue
    
    new_path = os.path.join(DATE_DIR, new_fn)
    if os.path.exists(new_path):
        print('SKIP: {} -> {} exists'.format(f, new_fn))
        continue
    
    os.rename(path, new_path)
    print('{} -> {}'.format(f, new_fn))
