"""批量给 step918_extractor.py 加日志"""
import sys, os

sys.stdout = open(1, 'w', encoding='utf-8')

fp = r'C:\Users\lianjie\.openclaw\workspace\jingcai\step918_extractor.py'
with open(fp, 'r', encoding='utf-8') as f:
    content = f.read()

# 头部加 log
old = 'import sys, os, json, io, re, requests, time, copy'
new = """import sys, os, json, io, re, requests, time, copy
from _log_util import setup_logger
LOG_DIR = None
if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
    LOG_DIR = os.path.join(os.path.dirname(os.path.normpath(sys.argv[1])), 'logs')
log = setup_logger('step918', LOG_DIR)
"""
content = content.replace(old, new, 1)

# 替换所有 print( -> log.info(
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

print('Done - step918_extractor.py 加日志完成')
