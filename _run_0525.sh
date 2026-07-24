#!/bin/bash
# 全流水线 bash直接调度，不走Python子进程
DATE="2026-05-25"
WIN_PY="/mnt/c/Python314/python.exe"
SD="C:/Users/lianjie/.openclaw/workspace/jingcai"
TD="${SD}/tasks/${DATE}"
DATA="${TD}/data"
CACHE="${DATA}/league_cache"

mkdir -p "$DATA" "$CACHE"

# Load match list from JSON (extract match info using Python)
MATCHES=$(/mnt/c/Python314/python.exe -c "
import json
with open('${TD}/matches_data.json', encoding='utf-8') as f:
    md = json.load(f)
for m in md['groups']['周一']['matches']:
    mn = m['matchnum']
    num = int(mn[-3:])
    home = m['home']
    away = m['away']
    fid = m['fid']
    league = m.get('league','')
    rq = m.get('rq','')
    macau = m.get('macau_line','')
    print(f'{mn}|{num}|{home}|{away}|{fid}|{league}|{rq}|{macau}')
" 2>&1)

echo "待处理: $(echo "$MATCHES" | wc -l) 场"
echo "============================================================"
echo "Phase 1: 并发跑比赛"
echo "============================================================"

# Create a temp dir for match directories first
# Process matches 3 at a time
MAX_WORKERS=3
COUNTER=0

process_match() {
    local IFS='|' read -r mn num home away fid league rq macau <<< "$1"
    local match_dir="${DATA}/match${num}_${home}__${away}"
    local win_md="C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/${DATE}/data/match${num}_${home}__${away}"
    local win_cache="C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/${DATE}/data/league_cache"
    
    mkdir -p "$match_dir"
    
    # Create meta.json
    /mnt/c/Python314/python.exe -c "
import json
meta = {'matchnum': '${mn}', 'match': '${mn} ${home} vs ${away}', 'fid': '${fid}', 'league': '${league}',
        'home': '${home}', 'away': '${away}', 'date': '${DATE}', 'status': 'processing', 'rq': '${rq}',
        'macau_line': '${macau}'}
with open('${win_md}/meta.json', 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
print('meta written')
" 2>&1
    
    # Step 1,4,6
    echo "  [${mn}] step146_extractor..."
    ${WIN_PY} "${SD}/step146_extractor.py" "${win_md}" 2>&1 | tail -1
    
    # Step 2,3,5
    echo "  [${mn}] step235_runner..."
    ${WIN_PY} "${SD}/step235_runner.py" "${win_md}" 2>&1 | tail -1
    
    # Step 7
    echo "  [${mn}] step7_runner..."
    ${WIN_PY} "${SD}/step7_runner.py" "${win_md}" 2>&1 | tail -1
    
    # Step 8 + 19-23
    echo "  [${mn}] step8_1923_extractor..."
    ${WIN_PY} "${SD}/step8_1923_extractor.py" "${win_md}" --cache "${win_cache}" 2>&1 | tail -1
    
    # Step 9-18
    echo "  [${mn}] step918_extractor..."
    ${WIN_PY} "${SD}/step918_extractor.py" "${win_md}" 2>&1 | tail -1
    
    # Step 24
    echo "  [${mn}] step24_extractor..."
    ${WIN_PY} "${SD}/step24_extractor.py" "${win_md}" 2>&1 | tail -1
    
    # Step 25
    echo "  [${mn}] step25_zhuangjia..."
    ${WIN_PY} "${SD}/step25_zhuangjia.py" --match-dir "${win_md}" 2>&1 | tail -1
    
    echo "  [${mn}] ✅ OK"
}

# Run matches sequentially (bash can't do easy threading)
# But we can background them with max 3 at a time
PIDS=()
MATCH_LIST=()
while IFS= read -r line; do
    MATCH_LIST+=("$line")
done <<< "$MATCHES"

for line in "${MATCH_LIST[@]}"; do
    # Extract just the match number for display
    IFS='|' read -r mn rest <<< "$line"
    echo "启动 ${mn}..."
    process_match "$line" &
    PIDS+=($!)
    COUNTER=$((COUNTER + 1))
    
    # Wait if we have MAX_WORKERS running
    if [ ${#PIDS[@]} -ge $MAX_WORKERS ]; then
        wait -n 2>/dev/null || true
        # Clean up completed PIDs
        NEW_PIDS=()
        for pid in "${PIDS[@]}"; do
            if kill -0 $pid 2>/dev/null; then
                NEW_PIDS+=($pid)
            fi
        done
        PIDS=("${NEW_PIDS[@]}")
    fi
done

# Wait for remaining
wait
echo ""
echo "Phase 1 完成"
echo ""

# Phase 2: 生成报告
echo "============================================================"
echo "Phase 2: 生成报告"
echo "============================================================"

while IFS= read -r line; do
    IFS='|' read -r mn num home away rest <<< "$line"
    match_dir="${DATA}/match${num}_${home}__${away}"
    win_md="C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/${DATE}/data/match${num}_${home}__${away}"
    
    if [ ! -f "${match_dir}/step25_zhuangjia.json" ]; then
        echo "  [跳过] ${mn} 无step25数据"
        continue
    fi
    
    out_name="${mn}_${home}vs${away}.md"
    out_path="${TD}/${out_name}"
    win_out="C:/Users/lianjie/.openclaw/workspace/jingcai/tasks/${DATE}/${out_name}"
    
    echo "  [报告] ${mn}..."
    ${WIN_PY} "${SD}/final_report_generator.py" "${win_md}" "${win_out}" 2>&1 | tail -1
    
    if [ -f "$out_path" ]; then
        sz=$(stat -c%s "$out_path")
        echo "    ${sz}B"
    fi
done <<< "$MATCHES"

# Phase 3: 模式匹配
echo ""
echo "============================================================"
echo "Phase 3: 模式匹配"
echo "============================================================"
${WIN_PY} "${SD}/pattern_matcher.py" "${DATE}" 2>&1

echo ""
echo "============================================================"
echo "Phase 4: 写入Notion备注"
echo "============================================================"

# Read pattern report and update Notion
/mnt/c/Python314/python.exe -c "
import json, subprocess, re

TOKEN = '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'
DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'
DATE_STR = '2026-05-25'

with open('${SD}/learnings/match_patterns_report.json', encoding='utf-8') as f:
    report = json.load(f)
matches = report['matches']

# Query Notion pages
query = json.dumps({'filter': {'property': '比赛日期', 'date': {'equals': DATE_STR}}})
r = subprocess.run(['curl', '-s', '-X', 'POST',
    'https://api.notion.com/v1/databases/' + DB_ID + '/query',
    '-H', 'Authorization: Bearer ' + TOKEN,
    '-H', 'Notion-Version: 2022-06-28',
    '-H', 'Content-Type: application/json',
    '-d', query], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
pages = json.loads(r.stdout).get('results', [])
page_map = {}
for p in pages:
    name = ''
    for prop_name, prop_val in p['properties'].items():
        if prop_val.get('type') == 'title':
            name = ''.join(t.get('plain_text','') for t in prop_val.get('title',[]))
            break
    m = re.match(r'(周[一二三四五六日]\d{3})', name)
    if m:
        page_map[m.group(1)] = p['id']

print(f'找到 {len(page_map)} 个Notion页面')

success = 0
for match in matches:
    mn = match['match_num']
    if mn not in page_map:
        print(f'  [跳过] {mn} 不在Notion')
        continue
    
    hits = match.get('hits', [])
    feat = match.get('features', {})
    zhuangjia = feat.get('综合盈亏方向', '')
    
    if not hits:
        text = '暂无匹配模式'
    else:
        from collections import defaultdict
        dirs = defaultdict(list)
        for h in hits:
            dirs[h['result']].append(h)
        lines = []
        sorted_dirs = sorted(dirs.keys(), key=lambda d: sum(h['pct']*h['lift'] for h in dirs[d]), reverse=True)
        for d in sorted_dirs[:3]:
            hs = dirs[d]
            best = max(hs, key=lambda h: h['pct'] * h['lift'])
            combo_str = ' + '.join(f'{k}={v}' for k,v in sorted(best['combo'].items()))
            lines.append(f'【{d}】{best[\"pct\"]*100:.0f}% (lift={best[\"lift\"]:.1f}, {best[\"correct\"]}/{best[\"total\"]})')
            lines.append(f'  → {combo_str}')
            for h in hs[1:3] if len(hs) > 1 else []:
                combo_str = ' + '.join(f'{k}={v}' for k,v in sorted(h['combo'].items()))
                lines.append(f'  + {h[\"pct\"]*100:.0f}% ({h[\"correct\"]}/{h[\"total\"]}) {combo_str}')
        
        scores = {}
        for d, hl in dirs.items():
            scores[d] = sum(h['pct'] * h['lift'] for h in hl[:3])
        sr = sorted(scores.items(), key=lambda x: -x[1])
        top_score = sr[0][1] if sr else 1
        sec_score = sr[1][1] if len(sr) >= 2 and sr[1][1] > 0 else 1
        dom = top_score / sec_score
        dom_tag = '🔥' if dom >= 3.0 else '💡' if dom >= 2.0 else '⚡' if dom >= 1.5 else '❓'
        lines.insert(0, f'{dom_tag} 命中{len(hits)}个模式 | dom={dom:.1f} | 庄家看好:{zhuangjia}')
        text = '\n'.join(lines)
    
    body = json.dumps({'properties': {'备注': {'rich_text': [{'type': 'text', 'text': {'content': text}}]}}})
    r = subprocess.run(['curl', '-s', '-X', 'PATCH',
        'https://api.notion.com/v1/pages/' + page_map[mn],
        '-H', 'Authorization: Bearer ' + TOKEN,
        '-H', 'Notion-Version: 2022-06-28',
        '-H', 'Content-Type: application/json',
        '-d', body], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
    res = json.loads(r.stdout)
    if res.get('object') != 'error':
        print(f'  ✅ {mn} 备注已更新')
        success += 1
    else:
        print(f'  ❌ {mn} 失败: {res.get(\"message\",\"?\")}')

print(f'\n备注更新完成: {success}/{len(matches)}')
" 2>&1

echo ""
echo "全流程完成！"
