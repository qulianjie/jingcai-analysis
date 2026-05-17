"""批量加日志"""
import sys, os

def add_log_to_file(fp, log_name):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找合适的import行来插入log
    # 找 import bsoup 或 requests 或 json 等行
    import_markers = ['import json', 'import requests', 'import sys, os', 'import re, os']
    insert_pos = -1
    for marker in import_markers:
        pos = content.find('\n' + marker)
        if pos >= 0:
            insert_pos = pos + 1
            break
    
    if insert_pos < 0:
        print(f'{fp}: 未找到import行')
        return
    
    # 在import后加log
    log_block = """
from _log_util import setup_logger
LOG_DIR = None
if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    LOG_DIR = os.path.join(os.path.dirname(os.path.normpath(sys.argv[1])), 'logs')
log = setup_logger('{name}', LOG_DIR)
""".format(name=log_name)
    
    content = content[:insert_pos] + log_block + content[insert_pos:]
    
    # 替换 print( -> log.info(
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if ', file=' in stripped or ',file=' in stripped:
            new_lines.append(line)
            continue
        if stripped.startswith('print('):
            indent = line[:len(line) - len(line.lstrip())]
            inner = stripped[6:-1]
            new_lines.append(indent + 'log.info(' + inner + ')')
        else:
            new_lines.append(line)
    
    with open(fp, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f'{fp} -> OK')

# 批量处理
rd = r'C:\Users\lianjie\.openclaw\workspace\jingcai'
add_log_to_file(os.path.join(rd, 'step24_extractor.py'), 'step24')
add_log_to_file(os.path.join(rd, 'final_conclusion_generator.py'), 'final_concl')
add_log_to_file(os.path.join(rd, 'final_conclusion_generator_v2.py'), 'final_concl_v2')
add_log_to_file(os.path.join(rd, 'final_stats.py'), 'final_stats')
add_log_to_file(os.path.join(rd, 'step25_zhuangjia.py'), 'step25')
add_log_to_file(os.path.join(rd, 'step26_profit_ratio.py'), 'step26')
add_log_to_file(os.path.join(rd, 'step0_fetch_matches.py'), 'step0')
add_log_to_file(os.path.join(rd, 'step1_explore.py'), 'step1')
