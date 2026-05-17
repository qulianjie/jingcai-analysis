# -*- coding: utf-8 -*-
"""
Step 1: Add new columns to database
Step 2: Re-upload all May data with corrected Name format and handicap prediction
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
        print(f"  [WARN] API {r.status_code}: {r.text[:300]}")
        return None
    return None

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
        print(f"  [WARN] API {r.status_code}: {r.text[:300]}")
        return None
    return None

# ── Step 1: Add columns to database ─────────────────────────────

def add_columns():
    """Add 让球预测 and 让球预测正确 columns"""
    print("=" * 60)
    print("Adding new columns...")
    print("=" * 60)
    
    # Build the PATCH payload with all existing properties + new ones
    # From earlier exploration, existing columns are:
    # 反馈日期 (date), 信心 (rich_text), 对阵 (rich_text), 联赛 (select),
    # 实际结果 (select), 预测 (select), 实际比分 (rich_text), 
    # 反馈总结 (rich_text), 预测正确 (checkbox)
    
    result = notion_patch(f"/databases/{DB_ID}", {
        "properties": {
            "让球预测": {
                "select": {
                    "options": [
                        {"name": "主胜"},
                        {"name": "平局"},
                        {"name": "客胜"},
                    ]
                }
            },
            "让球预测正确": {
                "checkbox": {}
            },
        }
    })
    
    if result:
        print("  Columns added successfully")
        # Verify
        r = requests.get(f"{BASE_URL}/databases/{DB_ID}",
                         headers={"Authorization": f"Bearer {NOTION_KEY}",
                                  "Notion-Version": "2025-09-03"})
        d = r.json()
        props = d.get('properties', {})
        print(f"  Current columns: {list(props.keys())}")
    else:
        print("  FAILED to add columns - will retry after upload")


# ── Report parsing ──────────────────────────────────────────────

def parse_match_report(md_path):
    """Extract prediction and handicap prediction from report"""
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    pred = ""
    handicap_pred = ""
    confidence = ""
    handicap_confidence = ""
    
    # Find 盘路推荐 section
    # Pattern: | **推荐** | 胜/平/负 |
    m = re.search(r'\*\*推荐\*\*\s*\|\s*([\u4e00-\u9fff]{2,5})', text)
    if m:
        pred = m.group(1)
    
    # Find 让球推荐 section
    m = re.search(r'让球推荐\s*\|\s*([\u4e00-\u9fff]{2,5})', text)
    if m:
        handicap_pred = m.group(1)
    
    # Also try 竞彩让球推荐
    if not handicap_pred:
        m = re.search(r'竞彩让球推荐\s*\|\s*([\u4e00-\u9fff]{2,5})', text)
        if m:
            handicap_pred = m.group(1)
    
    # Try 盘路推荐 section patterns
    if not pred:
        m = re.search(r'盘路推荐.*?推荐[|：:]\s*([\u4e00-\u9fff]{2,5})', text, re.DOTALL)
        if m:
            pred = m.group(1)
    
    if not handicap_pred:
        m = re.search(r'让球盘路.*?推荐[|：:]\s*([\u4e00-\u9fff]{2,5})', text, re.DOTALL)
        if m:
            handicap_pred = m.group(1)
    
    # Find confidence
    m = re.search(r'\*\*信心\*\*\s*\|\s*(.+?)\s*\|', text)
    if m:
        confidence = m.group(1).strip()[:50]
    
    if not confidence:
        m = re.search(r'信心[:：]\s*(\d+%[\u4e00-\u9fff\(\)\（\）a-zA-Z-]*)', text)
        if m:
            confidence = m.group(1).strip()[:50]
    
    # Find handicap confidence
    m = re.search(r'让球信心\s*\|\s*(.+?)\s*\|', text)
    if m:
        handicap_confidence = m.group(1).strip()[:50]
    
    return pred, handicap_pred, confidence, handicap_confidence


# ── Upload flow ─────────────────────────────────────────────────

def upload_date(date_str):
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
        pred, handicap_pred, confidence, handicap_confidence = parse_match_report(md_path)
        
        # Format: 周日011 意甲 萨索洛vsAC米兰
        name = f"{match_num} {league} {match_name}"
        
        print(f"  [{match_num}] {name}")
        print(f"    pred={pred}, handicap={handicap_pred}")
        
        properties = {
            "Name": {"title": [{"text": {"content": name}}]},
            "反馈日期": {"date": {"start": date_str}},
        }
        if league:
            properties["联赛"] = {"select": {"name": league}}
        if pred:
            properties["预测"] = {"select": {"name": pred}}
        if handicap_pred:
            properties["让球预测"] = {"select": {"name": handicap_pred}}
        if confidence:
            properties["信心"] = {"rich_text": [{"text": {"content": confidence}}]}
        if match_name:
            properties["对阵"] = {"rich_text": [{"text": {"content": match_name}}]}
        
        properties["反馈总结"] = {"rich_text": [{"text": {"content": f"预测{pred or '未知'}→待确认"}}]}
        properties["预测正确"] = {"checkbox": False}
        properties["让球预测正确"] = {"checkbox": False}
        
        result = notion_post("/pages", {"parent": {"database_id": DB_ID}, "properties": properties})
        if result:
            total += 1
            print(f"    OK")
        else:
            print(f"    FAILED")
        time.sleep(0.5)
    
    print(f"\n  Summary: {total} matches uploaded")


def main():
    # Step 1: Add columns
    add_columns()
    time.sleep(1)
    
    # Step 2: Upload all May data
    if os.path.isdir(TASKS_DIR):
        dates = sorted([d for d in os.listdir(TASKS_DIR)
                      if d.startswith("2026-05") and os.path.isdir(os.path.join(TASKS_DIR, d))])
        for date_str in dates:
            upload_date(date_str)
            time.sleep(1)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
