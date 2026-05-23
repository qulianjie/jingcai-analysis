# -*- coding: utf-8 -*-
"""批量赛果反馈脚本 - 处理所有5/7+的历史比赛"""
import subprocess, os, sys, json, time
from datetime import datetime, timedelta

CWD = r"C:\Users\lianjie\.openclaw\workspace\jingcai"
START_DATE = "2026-05-07"
END_DATE = "2026-05-21"
LOG_FILE = os.path.join(CWD, "learnings", "batch_feedback_log.json")

results_log = []

def run_feedback(target_date):
    """对某天跑 feedback.js (需要传 date+1，因为脚本内自动减1)"""
    dt = datetime.strptime(target_date, "%Y-%m-%d")
    date_arg = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"\n{'='*60}")
    print(f"[BATCH] 处理 {target_date} (传参 --date {date_arg})")
    print(f"{'='*60}")
    
    r = subprocess.run(
        ["node", "feedback.js", "--date", date_arg],
        cwd=CWD, capture_output=True, text=True, timeout=180
    )
    
    # Parse output
    scores_found = 0
    matches_updated = 0
    errors = []
    
    for line in r.stdout.split('\n'):
        if '获取到' in line and '场比分' in line:
            try:
                scores_found = int(line.split('获取到')[1].split('场')[0].strip())
            except: pass
        if '已更新:' in line:
            try:
                matches_updated = int(line.split('已更新:')[1].split()[0])
            except: pass
        if 'Parse error' in line or 'ERROR' in line:
            errors.append(line.strip())
    
    entry = {
        'date': target_date,
        'scores_found': scores_found,
        'matches_updated': matches_updated,
        'exit_code': r.returncode,
        'errors': errors,
        'has_output': len(r.stdout) > 100,
    }
    
    print(f"  → 比分: {scores_found}场, 更新: {matches_updated}场, 退出码: {r.returncode}")
    if errors:
        for e in errors:
            print(f"  ⚠️ {e}")
    
    return entry


# Main batch process
print("=" * 60)
print("竞彩批量反馈处理")
print(f"范围: {START_DATE} ~ {END_DATE}")
print(f"工作目录: {CWD}")
print("=" * 60)

# First check: what dates are in Notion?
start = datetime.strptime(START_DATE, "%Y-%m-%d")
end = datetime.strptime(END_DATE, "%Y-%m-%d")

total_dates = (end - start).days + 1
print(f"\n共 {total_dates} 个日期待处理\n")

for i in range(total_dates):
    target = (start + timedelta(days=i)).strftime("%Y-%m-%d")
    entry = run_feedback(target)
    results_log.append(entry)
    
    # Save progress after each run
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(results_log, f, ensure_ascii=False, indent=2)
    
    time.sleep(2)  # 礼貌间隔

# Summary
print(f"\n{'='*60}")
print(f"📊 批量反馈处理完成!")
print(f"{'='*60}")

total_scores = sum(e['scores_found'] for e in results_log)
total_updates = sum(e['matches_updated'] for e in results_log)
dates_with_data = sum(1 for e in results_log if e['scores_found'] > 0)
dates_with_errors = sum(1 for e in results_log if e['errors'])

print(f"  处理日期: {len(results_log)} 天")
print(f"  有比分数据: {dates_with_data} 天")
print(f"  总比分场次: {total_scores} 场")
print(f"  总更新场次: {total_updates} 场")
print(f"  有错误: {dates_with_errors} 天")

if dates_with_errors:
    print(f"\n⚠️ 以下日期有错误:")
    for e in results_log:
        if e['errors']:
            print(f"  {e['date']}: {e['errors'][:2]}")

print(f"\n日志已保存: {LOG_FILE}")
