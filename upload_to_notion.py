# -*- coding: utf-8 -*-
"""
Upload jingcai daily match reports to Notion database
Database: 7ee379c2f4364d558b6b5b8c48d1b00b (竞彩比赛反馈)

Usage:
    python upload_to_notion.py                    # Upload all May data
    python upload_to_notion.py 2026-05-02         # Upload specific date
    python upload_to_notion.py --dry-run           # Preview only
"""
import os
import sys
import json
import re
import time
import requests

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

NOTION_KEY = "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"
DB_ID = "7ee379c2f4364d558b6b5b8c48d1b00b"
BASE_URL = "https://api.notion.com/v1"

TASKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks")

# ── Notion helpers ──────────────────────────────────────────────

def notion_get(path, params=None):
    r = requests.get(f"{BASE_URL}{path}", params=params,
                     headers={"Authorization": f"Bearer {NOTION_KEY}",
                              "Notion-Version": "2025-09-03"})
    r.raise_for_status()
    return r.json()

def notion_post(path, data):
    for attempt in range(3):
        r = requests.post(f"{BASE_URL}{path}", json=data,
                         headers={"Authorization": f"Bearer {NOTION_KEY}",
                                  "Notion-Version": "2025-09-03"})
        if r.status_code == 429:
            time.sleep(float(r.headers.get("Retry-After", "1")))
            continue
        if r.status_code == 200:
            return r.json()
        print(f"  [WARN] API {r.status_code}: {r.text[:200]}")
        return None
    return None

def notion_patch(path, data):
    for attempt in range(3):
        r = requests.patch(f"{BASE_URL}{path}", json=data,
                         headers={"Authorization": f"Bearer {NOTION_KEY}",
                                  "Notion-Version": "2025-09-03"})
        if r.status_code == 429:
            time.sleep(float(r.headers.get("Retry-After", "1")))
            continue
        if r.status_code == 200:
            return r.json()
        print(f"  [WARN] API {r.status_code}: {r.text[:200]}")
        return None
    return None

# ── Report parsing ──────────────────────────────────────────────

def parse_match_report(md_path):
    """Extract prediction and match info from a report file"""
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    # Extract recommendation from 盘路推荐 section
    # Pattern: 推荐 | XXX
    pred = ""
    confidence = ""
    
    # Try to find 盘路推荐 section
    sections = re.split(r'\n-{3,}\n', text)
    
    # Look for recommendation table
    rec_pattern = re.compile(
        r'(?:盘路推荐|最终盘路推荐).*?'
        r'(?:推荐|推荐结果)[|：:]\s*([\u4e00-\u9fff]{2,5})',
        re.DOTALL
    )
    m = rec_pattern.search(text)
    if m:
        pred = m.group(1)
    
    # Also try to find in 信心 section
    conf_pattern = re.compile(
        r'信心[|：:]\s*([\d]+%[^\n]*)',
        re.DOTALL
    )
    m = conf_pattern.search(text)
    if m:
        confidence = m.group(1).strip()
    
    # Fallback: look for 推荐 line anywhere
    if not pred:
        # Pattern: | **推荐** | 胜/平/负 |
        m = re.search(r'\*\*推荐\*\*\s*\|\s*([\u4e00-\u9fff]{2,5})', text)
        if m:
            pred = m.group(1)
    
    if not confidence:
        m = re.search(r'\*\*信心\*\*\s*\|\s*(.+?)\s*\|?', text)
        if m:
            confidence = m.group(1).strip()[:50]
    
    # Also try simpler patterns
    if not pred:
        m = re.search(r'推荐[:：]\s*([\u4e00-\u9fff]{2,5})', text)
        if m:
            pred = m.group(1)
    
    if not confidence:
        m = re.search(r'信心[:：]\s*(\d+%[\u4e00-\u9fff\(\)\（\）a-zA-Z-]*)', text)
        if m:
            confidence = m.group(1).strip()[:50]
    
    return pred, confidence

# ── Main upload flow ────────────────────────────────────────────

def upload_date(date_str, dry_run=False):
    """Upload all match reports for a given date"""
    date_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.isdir(date_dir):
        print(f"[SKIP] {date_str} - directory not found")
        return
    
    # Find all match report MD files
    md_files = []
    for f in sorted(os.listdir(date_dir)):
        if f.endswith(".md") and f not in ("sunday_matches.md", "TEMPLATE.md"):
            md_files.append(f)
    
    if not md_files:
        print(f"[SKIP] {date_str} - no match reports")
        return
    
    print(f"\n{'='*60}")
    print(f"[{date_str}] {len(md_files)} matches")
    print(f"{'='*60}")
    
    # Load meta.json for each match
    data_dir = os.path.join(date_dir, "data")
    all_meta = {}
    if os.path.isdir(data_dir):
        for d in sorted(os.listdir(data_dir)):
            meta_path = os.path.join(data_dir, d, "meta.json")
            if os.path.isfile(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    match_num = meta.get("matchnum", "")
                    if match_num:
                        all_meta[match_num] = meta
    
    total = 0
    
    for md_file in md_files:
        # Extract match number from filename
        num_match = re.match(r'([^\d_]*\d{3})', md_file)
        match_num = num_match.group(1) if num_match else ""
        
        # Get meta
        meta = all_meta.get(match_num, {})
        if not meta:
            for mn, m in all_meta.items():
                if m.get("home", "") in md_file or m.get("away", "") in md_file:
                    meta = m
                    break
        
        league = meta.get("league", "")
        home = meta.get("home", "")
        away = meta.get("away", "")
        match_name = f"{home}vs{away}" if home and away else md_file.replace('.md','')
        
        # Parse prediction
        md_path = os.path.join(date_dir, md_file)
        pred, confidence = parse_match_report(md_path)
        
        print(f"  [{match_num}] {league} {match_name} -> pred={pred}, conf={confidence}")
        
        if not dry_run:
            properties = {
                "Name": {"title": [{"text": {"content": f"第{match_num[-3:]}场 {league} {match_name}"}}]},
                "反馈日期": {"date": {"start": date_str}},
            }
            if league:
                properties["联赛"] = {"select": {"name": league}}
            if pred:
                properties["预测"] = {"select": {"name": pred}}
            if confidence:
                properties["信心"] = {"rich_text": [{"text": {"content": confidence}}]}
            if match_name:
                properties["对阵"] = {"rich_text": [{"text": {"content": match_name}}]}
            
            # 实际结果/比分留空 - Notion select不能传空值
            properties["反馈总结"] = {"rich_text": [{"text": {"content": f"预测{pred or '未知'}→待确认"}}]}
            properties["预测正确"] = {"checkbox": False}
            
            result = notion_post("/pages", {"parent": {"database_id": DB_ID}, "properties": properties})
            if result:
                total += 1
                print(f"    OK: {result.get('id', '')[:8]}")
            else:
                print(f"    FAILED")
            time.sleep(0.5)
        else:
            total += 1
    
    print(f"\n  Summary: {total} matches")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry_run = "--dry-run" in sys.argv
    
    if args:
        upload_date(args[0], dry_run)
    else:
        if os.path.isdir(TASKS_DIR):
            dates = sorted([d for d in os.listdir(TASKS_DIR)
                          if d.startswith("2026-05") and os.path.isdir(os.path.join(TASKS_DIR, d))])
            for date_str in dates:
                upload_date(date_str, dry_run)
                time.sleep(1)


if __name__ == "__main__":
    main()
