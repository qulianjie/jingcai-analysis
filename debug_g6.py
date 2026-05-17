# -*- coding: utf-8 -*-
import os, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIRS = [
    os.path.join(BASE, 'tasks', '2026-05-12', 'data', 'match6_圣旺红星__罗德兹'),
    os.path.join(BASE, 'tasks', '2026-05-12', 'data', 'match7_南安普敦__米堡'),
]

for d in DATA_DIRS:
    if os.path.isdir(d):
        name = os.path.basename(d)
        print(f'Testing: {name}')
        ret = subprocess.run(['python', 'step8_1923_extractor.py', d],
                            capture_output=True, text=True, timeout=300)
        print(f'  Exit: {ret.returncode}')
        if ret.stdout:
            print(f'  Stdout: {ret.stdout[:500]}')
        if ret.stderr:
            print(f'  Stderr: {ret.stderr[:500]}')
    else:
        print(f'Not found: {d}')
