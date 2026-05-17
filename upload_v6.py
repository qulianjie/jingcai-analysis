# -*- coding: utf-8 -*-
"""
Delete all entries and re-upload with corrected format:
- Name: 周日011 意甲 萨索洛vsAC米兰
- 让球预测: extracted from **让球预测** | 让球平（信心45%）
- 让球预测正确: rich_text
"""
import os, sys, json, re, time, requests

if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

NOTION_KEY = "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"
DB_ID = "7ee379c2f4364d558b6b5b8c48d1b00b"
DS_ID = "a5575563-f29c-4224-b6e8-1b804bf04ba6"
TASKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks")

h = {
    "Authorization": f"Bearer {NOTION_KEY}",
    "Notion-Version": "2025-09-03"
}

def notion_post(path, data):
    for attempt in range(3):
        r = requests.post(f"https://api.notion.com/v1{path}", json=data, headers=h)
        if r.status_code == 429:
            time.sleep(float(r.headers.get("Retry-After", "1")))
            continue
        if r.status_code == 200:
            return r.json()
        print(f"  [WARN] {r.status_code}: {r.text[:200]}")
        return None
    return None

def notion_patch(path, data):
    for attempt in range(3):
        r = requests.patch(f"https://api.notion.com/v1{path}", json=data, headers=h)
        if r.status_code == 429:
            time.sleep(float(r.headers.get("Retry-After", "1")))
            continue
        if r.status_code == 200:
            return r.json()
        print(f"  [WARN] {r.status_code}: {r.text[:200]}")
        return None
    return None

# ── Step 1: Delete all existing entries ─────────────────────────

print("Step 1: Deleting existing entries...")
r = requests.post(f"https://api.notion.com/v1/data_sources/{DS_ID}/query", json={}, headers=h)
items = r.json().get('results', [])
print(f"  Found {len(items)} entries")

deleted = 0
for item in items:
    eid = item.get('id')
    name = item.get('properties', {}).get('Name', {}).get('title', [{}])[0].get('plain_text', '')
    result = notion_patch(f"/pages/{eid}", {"archived": True})
    if result:
        deleted += 1
    time.sleep(0.1)

print(f"  Deleted {deleted} entries")
time.sleep(1)

# ── Step 2: Parse reports ───────────────────────────────────────

def parse_match_report(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    pred = ""
    handicap_pred = ""
    confidence = ""
    
    # Find 推荐
    m = re.search(r'\*\*推荐\*\*\s*\|\s*([\u4e00-\u9fff]{2,5})', text)
    if m:
        pred = m.group(1)
    
    # Find 让球预测 - format: | **让球预测** | 让球平（信心45%） |
    m = re.search(r'\*\*让球预测\*\*\s*\|\s*(.+)', text)
    if m:
        handicap_pred = m.group(1).strip()
    
    # Confidence
    m = re.search(r'\*\*信心\*\*\s*\|\s*(.+?)\s*\|', text)
    if m:
        confidence = m.group(1).strip()[:50]
    
    if not confidence:
        m = re.search(r'信心[:：]\s*(\d+%[\u4e00-\u9fff\(\)\（\）a-zA-Z-]*)', text)
        if m:
            confidence = m.group(1).strip()[:50]
    
    return pred, handicap_pred, confidence

# ── Step 3: Upload all dates ────────────────────────────────────

total_uploaded = 0

for date_str in sorted(os.listdir(TASKS_DIR)):
    if not date_str.startswith("2026-05"):
        continue
    
    date_dir = os.path.join(TASKS_DIR, date_str)
    if not os.path.isdir(date_dir):
        continue
    
    md_files = [f for f in sorted(os.listdir(date_dir))
                if f.endswith(".md") and f not in ("sunday_matches.md", "TEMPLATE.md")]
    
    if not md_files:
        continue
    
    print(f"\n[{date_str}] {len(md_files)} matches")
    
    # Load meta
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
    
    for md_file in md_files:
        num_match = re.match(r'([^\d_]*\d{3})', md_file)
        match_num = num_match.group(1) if num_match else ""
        
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
        
        md_path = os.path.join(date_dir, md_file)
        pred, handicap_pred, confidence = parse_match_report(md_path)
        
        # Format: 周日011 意甲 萨索洛vsAC米兰
        name = f"{match_num} {league} {match_name}"
        
        properties = {
            "Name": {"title": [{"text": {"content": name}}]},
            "反馈日期": {"date": {"start": date_str}},
        }
        if league:
            properties["联赛"] = {"select": {"name": league}}
        if pred:
            properties["预测"] = {"select": {"name": pred}}
        if handicap_pred:
            properties["让球预测"] = {"rich_text": [{"text": {"content": handicap_pred}}]}
        if confidence:
            properties["信心"] = {"rich_text": [{"text": {"content": confidence}}]}
        if match_name:
            properties["对阵"] = {"rich_text": [{"text": {"content": match_name}}]}
        
        properties["反馈总结"] = {"rich_text": [{"text": {"content": f"预测{pred or '未知'}→待确认"}}]}
        properties["预测正确"] = {"checkbox": False}
        properties["让球预测正确"] = {"rich_text": [{"text": {"content": "待确认"}}]}
        
        result = notion_post("/pages", {"parent": {"database_id": DB_ID}, "properties": properties})
        if result:
            total_uploaded += 1
            print(f"  [{match_num}] {name} - OK (pred={pred}, handicap={handicap_pred})")
        else:
            print(f"  [{match_num}] {name} - FAILED")
        time.sleep(0.5)

print(f"\n{'='*60}")
print(f"Total uploaded: {total_uploaded}")
print(f"{'='*60}")
