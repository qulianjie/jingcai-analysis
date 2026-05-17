# -*- coding: utf-8 -*-
"""重新生成所有比赛报告的结论部分"""
import os, sys, re, subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, 'tasks')
DATE = '2026-05-02'
TASK_PATH = os.path.join(TASKS_DIR, DATE)
DATA_PATH = os.path.join(TASK_PATH, 'data')

if not os.path.exists(DATA_PATH):
    print(f'数据目录不存在: {DATA_PATH}')
    sys.exit(1)

match_dirs = [d for d in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, d))]
print(f'找到 {len(match_dirs)} 个match目录')

conclusion_script = os.path.join(SCRIPT_DIR, 'final_conclusion_generator.py')
success = 0

for md_name in sorted(match_dirs):
    md_path = os.path.join(DATA_PATH, md_name)
    
    # 检查是否有必要的目录
    if not os.path.exists(os.path.join(md_path, 'group01_europe')):
        continue
    
    # 运行结论生成器
    try:
        result = subprocess.run(
            [sys.executable, conclusion_script, md_path],
            capture_output=True, text=True, timeout=60,
            encoding='utf-8', errors='replace'
        )
        
        if result.returncode == 0 and result.stdout:
            # 提取match编号
            match_num = md_name.split('_')[0] if '_' in md_name else ''
            
            # 找到对应的md报告（match编号如 match001 -> 周六001）
            num = match_num.replace('match', '')
            md_file = None
            for f in os.listdir(TASK_PATH):
                if f.endswith('.md') and num in f:
                    md_file = os.path.join(TASK_PATH, f)
                    break
            
            if md_file:
                content = open(md_file, 'r', encoding='utf-8', errors='replace').read()
                
                # 替换结论部分
                new_conclusion = result.stdout
                # 从"## 最终预测分析"到文件末尾
                idx = content.find('## 最终预测分析')
                if idx >= 0:
                    content = content[:idx] + new_conclusion + '\n\n---\n\n*提示：以上分析基于数据驱动规则引擎 + 历史模式学习，每个结论均可追溯到具体数据。投资有风险，请结合实战判断。*'
                    open(md_file, 'w', encoding='utf-8').write(content)
                    success += 1
                    print(f'  OK {os.path.basename(md_file)}')
                else:
                    print(f'  WARN {os.path.basename(md_file)}: no conclusion found')
            else:
                print(f'  WARN {md_name}: no matching md file')
        else:
            print(f'  FAIL {md_name}: generation failed')
    except subprocess.TimeoutExpired:
        print(f'  TIMEOUT {md_name}')
    except Exception as e:
        print(f'  ERROR {md_name}: {str(e)[:100]}')

print(f'\n完成！成功重新生成 {success}/{len(match_dirs)} 份报告')
