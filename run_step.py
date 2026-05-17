# -*- coding: utf-8 -*-
"""步骤脚本统一包装器 - 从 meta.json 读取参数后调用实际脚本

用法: python run_step.py <step_name> <match_dir>

支持的 step_name:
  step146 -> step146_extractor.py
  step235 -> step235_runner.py
  step7   -> step7_runner.py
  step8   -> step8_1923_extractor.py
  step918 -> step918_extractor.py
  step24  -> step24_extractor.py
"""
import sys, os, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MATCH_DIR = sys.argv[2] if len(sys.argv) > 2 else ''
STEP_NAME = sys.argv[1] if len(sys.argv) > 1 else ''

if not os.path.isdir(MATCH_DIR):
    print('[ERROR] match_dir 不存在: {}'.format(MATCH_DIR))
    sys.exit(1)

# 读取 meta.json
meta_path = os.path.join(MATCH_DIR, 'meta.json')
if not os.path.exists(meta_path):
    print('[ERROR] meta.json 不存在: {}'.format(meta_path))
    sys.exit(1)

with open(meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)

FID = meta.get('fid', '')
LEAGUE = meta.get('league', '')
HOME = meta.get('home', '')
AWAY = meta.get('away', '')
HOME_ID = meta.get('home_id', '')
AWAY_ID = meta.get('away_id', '')
MACAU_LINE = meta.get('macau_line', '')

def run(script, args):
    script_path = os.path.join(SCRIPT_DIR, script)
    cmd = [sys.executable, script_path] + args
    import subprocess
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, encoding='utf-8', errors='replace')
    if result.stdout:
        print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, end='', file=sys.stderr)
    return result.returncode

# 构建输出路径
def out_path(group, name):
    return os.path.join(MATCH_DIR, group, name)

if STEP_NAME == 'step146':
    run('step146_extractor.py', [
        FID, LEAGUE,
        out_path('group01_europe', 'step1_europe_base.txt'),
        out_path('group02_handicap', 'step4_handicap_base.txt'),
        out_path('group03_asian', 'step6_asian_base.txt'),
    ])

elif STEP_NAME == 'step235':
    run('step235_runner.py', [
        FID, LEAGUE,
        out_path('group01_europe', 'step2_jingcai_same.txt'),
        out_path('group01_europe', 'step3_interwetten_same.txt'),
        out_path('group02_handicap', 'step5_handicap_same.txt'),
    ])

elif STEP_NAME == 'step7':
    run('step7_runner.py', [
        FID, LEAGUE,
        out_path('group03_asian', 'step7_macau_same.txt'),
    ])

elif STEP_NAME == 'step8':
    run('step8_1923_extractor.py', [
        HOME_ID, AWAY_ID, LEAGUE, FID, MACAU_LINE,
        out_path('group03_asian', 'step8_same_league.txt'),
    ])

elif STEP_NAME == 'step918':
    os.makedirs(os.path.join(MATCH_DIR, 'group04_teamA'), exist_ok=True)
    os.makedirs(os.path.join(MATCH_DIR, 'group05_teamB'), exist_ok=True)
    run('step918_extractor.py', [
        HOME_ID, AWAY_ID, LEAGUE, FID, MACAU_LINE,
        MATCH_DIR,
    ])

elif STEP_NAME == 'step24':
    run('step24_extractor.py', [
        HOME_ID, AWAY_ID, LEAGUE, FID,
        os.path.join(MATCH_DIR, 'step24_panlu_match.json'),
    ])

elif STEP_NAME == 'report':
    run('final_report_generator.py', [MATCH_DIR])

else:
    print('[ERROR] 未知 step: {}'.format(STEP_NAME))
    sys.exit(1)
