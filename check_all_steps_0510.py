import os, json, sys

# Fix stdout encoding
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r"C:\Users\lianjie\.openclaw\workspace\jingcai\tasks\2026-05-10\data"

match_dirs = sorted([n for n in os.listdir(BASE) if n.startswith("match") and os.path.isdir(os.path.join(BASE, n))])

print(f"共 {len(match_dirs)} 个match目录: {match_dirs}\n")

# Step mapping
step_num_name = {
    1: "欧赔基础", 2: "竞彩同赔", 3: "IW同赔",
    4: "让球基础", 5: "让球同赔",
    6: "亚盘基础", 7: "澳门同赔", 8: "历史亚盘",
    9: "主队历史", 10: "主队近况", 11: "主队伤停", 12: "主队战意", 13: "主队分析",
    14: "客队历史", 15: "客队近况", 16: "客队伤停", 17: "客队战意", 18: "客队分析",
    19: "百家对比", 20: "百家竞彩", 21: "百家IW", 22: "百家亚盘", 23: "百家让球",
}

groups_steps = {
    "group01_europe": [1, 2, 3],
    "group02_handicap": [4, 5],
    "group03_asian": [6, 7, 8],
    "group04_teamA": [9, 10, 11, 12, 13],
    "group05_teamB": [14, 15, 16, 17, 18],
    "group06_baijia": [19, 20, 21, 22, 23],
}

file_names = {
    1: "step1_europe_base.txt",
    2: "step2_jingcai_same.txt",
    3: "step3_interwetten_same.txt",
    4: "step4_handicap_base.txt",
    5: "step5_handicap_same.txt",
    6: "step6_asian_base.txt",
    7: "step7_macau_same.txt",
    8: "step8_same_league.txt",
    9: "step9_home_history.txt",
    14: "step14_away_history.txt",
    19: "step19_baijia_compare.txt",
}

# Steps 10-13, 15-18, 20-23 are generated inline by final_report_generator.py
# They don't exist as separate files. The base files (step9, step14, step19)
# contain all data needed for the report to derive these sub-steps.
inline_steps = {
    10: (9, "从step9_home_history.txt提取"),
    11: (9, "从step9_home_history.txt提取"),
    12: (9, "从step9_home_history.txt提取"),
    13: (9, "从step9_home_history.txt提取"),
    15: (14, "从step14_away_history.txt提取"),
    16: (14, "从step14_away_history.txt提取"),
    17: (14, "从step14_away_history.txt提取"),
    18: (14, "从step14_away_history.txt提取"),
    20: (19, "从step19_baijia_compare.txt提取"),
    21: (19, "从step19_baijia_compare.txt提取"),
    22: (19, "从step19_baijia_compare.txt提取"),
    23: (19, "从step19_baijia_compare.txt提取"),
}

# Build reverse: filename -> step_num
filename_to_step = {v: k for k, v in file_names.items()}

# Group to step mapping
step_to_group = {}
for g, steps in groups_steps.items():
    for s in steps:
        step_to_group[s] = g

all_problems = []  # (match_dir, step_num, step_name, issue)

for md in match_dirs:
    md_path = os.path.join(BASE, md)
    print(f"{'='*60}")
    print(f"📁 {md}")
    print(f"{'='*60}")
    
    for step_num in range(1, 24):
        sname = step_num_name.get(step_num, f"Step{step_num}")
        group = step_to_group[step_num]
        
        # Check if this is an inline step
        if step_num in inline_steps:
            parent_step, desc = inline_steps[step_num]
            parent_group = step_to_group[parent_step]
            parent_file = file_names[parent_step]
            parent_path = os.path.join(md_path, parent_group, parent_file)
            if os.path.isfile(parent_path) and os.path.getsize(parent_path) > 0:
                print(f"  ✅ Step {step_num:2d} ({sname:10s}): 内联生成({desc})")
            else:
                print(f"  ❌ Step {step_num:2d} ({sname:10s}): 父文件{parent_file}缺失/为空")
                all_problems.append((md, step_num, sname, "父文件缺失/为空"))
            continue
        
        fname = file_names[step_num]
        fpath = os.path.join(md_path, group, fname)
        
        if not os.path.isdir(os.path.join(md_path, group)):
            print(f"  ❌ Step {step_num:2d} ({sname:10s}): 目录 {group}/ 不存在")
            all_problems.append((md, step_num, sname, "目录不存在"))
            continue
        
        if not os.path.isfile(fpath):
            print(f"  ❌ Step {step_num:2d} ({sname:10s}): 文件不存在")
            all_problems.append((md, step_num, sname, "文件不存在"))
            continue
        
        size = os.path.getsize(fpath)
        
        # Read content
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            with open(fpath, 'r', encoding='gbk') as f:
                content = f.read()
        
        # Count meaningful lines
        lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('=') and not l.startswith('#')]
        
        if size == 0:
            print(f"  ❌ Step {step_num:2d} ({sname:10s}): 空文件 (0 bytes)")
            all_problems.append((md, step_num, sname, "空文件"))
        elif len(lines) <= 2:
            preview = lines[0][:60] if lines else ''
            print(f"  ⚠️  Step {step_num:2d} ({sname:10s}): 数据极少 ({size}B, {len(lines)}行) - {preview}")
            all_problems.append((md, step_num, sname, f"数据极少({size}B,{len(lines)}行)"))
        else:
            # Extract key info from the file
            # Look for data line count patterns
            data_count = 0
            for l in lines:
                if '场' in l or '数据' in l:
                    try:
                        parts = l.split()
                        for p in parts:
                            if p.isdigit():
                                data_count = int(p)
                                break
                    except:
                        pass
            
            status = f"✅ {size}B/{len(lines)}行"
            if data_count:
                status += f" 数据:{data_count}场"
            print(f"  {status}  Step {step_num:2d} ({sname})")
    
    # Check step24 (note: .json extension but actually markdown text)
    s24_path = os.path.join(md_path, "step24_panlu_match.json")
    if os.path.isfile(s24_path):
        size = os.path.getsize(s24_path)
        try:
            with open(s24_path, 'r', encoding='utf-8') as f:
                s24_content = f.read()
        except:
            with open(s24_path, 'r', encoding='gbk') as f:
                s24_content = f.read()
        
        if size == 0:
            print(f"  ❌ Step 24 (盘路匹配): 空文件")
            all_problems.append((md, 24, "盘路匹配", "空文件"))
        else:
            # Count match lines (lines with "vs" in them)
            match_count = sum(1 for l in s24_content.split('\n') if 'vs' in l and '|' in l)
            print(f"  ✅ Step 24 (盘路匹配): {size}B, {match_count}条记录")
    else:
        print(f"  ❌ Step 24 (盘路匹配): 文件不存在")
        all_problems.append((md, 24, "盘路匹配", "文件不存在"))
    
    print()

# Summary
print(f"\n💡 注：Step 10-13, 15-18, 20-23 由final_report_generator.py从基础文件内联生成，不单独存文件")
print(f"\n{'='*60}")
print(f"📊 汇总: {len(match_dirs)}场 × 24步 = {len(match_dirs)*24}个步骤")
print(f"{'='*60}")

if all_problems:
    print(f"\n⚠️  发现问题: {len(all_problems)}个")
    print(f"\n明细:")
    for md, step_num, sname, issue in all_problems:
        print(f"  {md} → Step {step_num:2d} ({sname:10s}): {issue}")
    
    # Group by issue type
    print(f"\n按类型分组:")
    from collections import Counter
    issue_counts = Counter()
    for md, step_num, sname, issue in all_problems:
        key = f"Step {step_num:2d} ({sname})"
        issue_counts[key] += 1
    
    for k, v in sorted(issue_counts.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}场比赛有问题")
else:
    print(f"\n✅ 全部正常！所有{len(match_dirs)*24}个步骤都有数据")
