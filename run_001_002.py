#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""竞彩流水线 — 跑周日001+002"""
import subprocess, sys, os

BASE = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
PY = r'C:\Python314\python.exe'
MATCH1 = BASE + r'\tasks\2026-05-24\data\match1_水户蜀葵__川崎前锋'
MATCH2 = BASE + r'\tasks\2026-05-24\data\match2_清水鼓动__大阪钢巴'

os.chdir(BASE)

def run(script, *args, label=''):
    cmd = [PY, os.path.join(BASE, script)] + list(args)
    print(f'\n[RUN] {label or script}')
    sys.stdout.flush()
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(timeout=180)
        if out:
            lines = out.decode('utf-8', errors='replace').strip().split('\n')
            for l in lines[-5:]:
                print(f'  {l}')
        if err:
            e = err.decode('utf-8', errors='replace').strip()
            if e: print(f'  [ERR] {e[:200]}')
        sys.stdout.flush()
    except subprocess.TimeoutExpired:
        print(f'  [TIMEOUT] {label}')
    except Exception as e:
        print(f'  [ERR] {e}')

print('=' * 50)
print('周日001: 水户蜀葵 vs 川崎前锋')
print('=' * 50)
run('step235_runner.py', MATCH1, label='step235(001)')
run('step7_runner.py', MATCH1, label='step7(001)')
run('step8_1923_extractor.py', MATCH1, label='step8_1923(001)')
run('step918_extractor.py', MATCH1, label='step918(001)')
run('step24_extractor.py', MATCH1, label='step24(001)')
run('step25_zhuangjia.py', '--match-dir', MATCH1, label='step25(001)')
run('final_report_generator.py', MATCH1, label='report(001)')
print('\nDone 001')

print('\n' + '=' * 50)
print('周日002: 清水鼓动 vs 大阪钢巴')
print('=' * 50)
run('step146_extractor.py', MATCH2, label='step146(002)')
run('step235_runner.py', MATCH2, label='step235(002)')
run('step7_runner.py', MATCH2, label='step7(002)')
run('step8_1923_extractor.py', MATCH2, label='step8_1923(002)')
run('step918_extractor.py', MATCH2, label='step918(002)')
run('step24_extractor.py', MATCH2, label='step24(002)')
run('step25_zhuangjia.py', '--match-dir', MATCH2, label='step25(002)')
run('final_report_generator.py', MATCH2, label='report(002)')
print('\nDone 002')
print('\n=== ALL DONE ===')
