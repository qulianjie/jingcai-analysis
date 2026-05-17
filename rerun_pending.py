# -*- coding: utf-8 -*-
"""
只处理真正pending的match
"""
import os, sys, json, subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

pending = [
    ('2026-05-08', 'match11_赫尔城__米尔沃尔'),
    ('2026-05-09', 'match7_米堡__南安普敦'),
    ('2026-05-11', 'match6_米尔沃尔__赫尔城'),
    ('2026-05-12', 'match7_南安普敦__米堡'),
    ('2026-05-12', 'match17_南安普敦__米堡'),
]

for date, name in pending:
    match_dir = os.path.join(BASE_DIR, 'tasks', date, 'data', name)
    print('处理: %s/%s' % (date, name))
    
    # step8+19-23
    r1 = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, 'step8_1923_extractor.py'), match_dir],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=300
    )
    print('  step8+19-23: %s' % ('OK' if r1.returncode == 0 else 'FAIL'))
    
    # 生成报告
    r2 = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, 'final_report_generator.py'), date, name, match_dir],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=60
    )
    print('  报告: %s' % ('OK' if r2.returncode == 0 else 'FAIL'))

print('\n完成')
