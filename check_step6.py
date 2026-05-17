import os
task_dir = 'C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/2026-05-12/data'
for d in sorted(os.listdir(task_dir)):
    dp = os.path.join(task_dir, d)
    if os.path.isdir(dp):
        s6 = os.path.join(dp, 'group03_asian', 'step6_asian_base.txt')
        if os.path.exists(s6):
            with open(s6, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                print(f'=== {d} (lines={len(lines)}) ===')
                for i, line in enumerate(lines[:20]):
                    print(f'  {i}: {repr(line)}')
                break
