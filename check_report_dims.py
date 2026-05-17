# -*- coding: utf-8 -*-
"""检查报告中维度信号部分"""
import os

tasks_dir = r'C:\Users\lianjie\.openclaw\workspace\jingcai\tasks'
fpath = os.path.join(tasks_dir, '2026-05-03', '周日001_大阪樱花vs福冈黄蜂.md')

with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到"各维度信号"部分
start = content.find('各维度信号')
if start > 0:
    section = content[start:start+1000]
    # 只输出ASCII安全的内容
    safe_chars = []
    for ch in section:
        if ord(ch) < 128 or ch in '\n\r\t':
            safe_chars.append(ch)
        else:
            safe_chars.append('?')
    print(''.join(safe_chars))
else:
    print('Not found')
