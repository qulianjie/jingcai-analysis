# -*- coding: utf-8 -*-
"""重新生成05-10所有比赛的预测报告"""
import os, sys, subprocess

BASE = r"C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10\data"
GENERATOR = r"C:\Users\lianjie\.openclaw\workspace\jingcai\final_report_generator.py"

matches = sorted([n for n in os.listdir(BASE) if n.startswith("match") and os.path.isdir(os.path.join(BASE, n))])

for m in matches:
    mpath = os.path.join(BASE, m)
    print(f"\n{'='*50}")
    print(f"生成: {m}")
    print(f"{'='*50}")
    result = subprocess.run(
        [sys.executable, GENERATOR, mpath],
        capture_output=True, text=True, timeout=60
    )
    # 提取关键预测行
    for line in result.stdout.split('\n'):
        if '竞彩预测' in line or '综合分值' in line or '信心' in line:
            print(f"  {line.strip()}")
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[:200]}")

print("\n✅ 全部完成")
