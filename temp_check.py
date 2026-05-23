# -*- coding: utf-8 -*-
import os

tasks_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
fpath = os.path.join(tasks_dir, '2026-05-03', '周日001_大阪樱花vs福冈黄蜂.md')

with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到"各维度信号"部分
start = content.find('各维度信号')
if start > 0:
    # 找到下一段 ---
    end = content.find('---', start + 10)
    section = content[start:end] if end > start else content[start:start+800]
    # 只输出安全字符
    for line in section.split('\n'):
        safe = ''.join(c for c in line if ord(c) < 128 or c in '\t')
        print(safe)
else:
    print('Not found')
