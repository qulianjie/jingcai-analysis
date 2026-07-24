#!/usr/bin/env python3
"""模式库同步到Notion - 由pattern_miner.py自动调用"""
import json, subprocess, os, sys
from collections import Counter

TOKEN = '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'
DB_ID = '35491ad7-17ba-81cc-aa04-ce53f7234e17'

def nc(method, url, data=None):
    cmd = ['curl', '-s', '-X', method, url,
           '-H', 'Authorization: Bearer ' + TOKEN,
           '-H', 'Notion-Version: 2022-06-28',
           '-H', 'Content-Type: application/json']
    if data:
        cmd += ['-d', json.dumps(data, ensure_ascii=False)]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, universal_newlines=True)
    return json.loads(r.stdout) if r.stdout else {}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(SCRIPT_DIR, 'learnings', 'historical_patterns.json')) as f:
    pl = json.load(f)
patterns = pl.get('patterns', [])
print('Patterns: {}'.format(len(patterns)))

by_dim = Counter(p['dim_n'] for p in patterns)
by_res = Counter(p['result'] for p in patterns)
lift2 = sum(1 for p in patterns if p.get('lift', 0) >= 2.0)
top = sorted(patterns, key=lambda p: p.get('lift', 0) * p.get('pct', 0), reverse=True)[:50]

parts = ['# Pattern Library\n']
parts.append('Total: {} | Lift>=2: {} | 1D={} 2D={} 3D={}\n'.format(
    len(patterns), lift2, by_dim.get(1,0), by_dim.get(2,0), by_dim.get(3,0)))
parts.append('Results: Win={} Draw={} Loss={}\n'.format(by_res.get('胜',0), by_res.get('平',0), by_res.get('负',0)))
parts.append('Updated: {}\n'.format(pl.get('generated', '?')))
parts.append('\nTop 50:\n')
for i, p in enumerate(top, 1):
    cs = ' + '.join('{}={}'.format(k, v) for k, v in p['combo'].items())
    parts.append('{}. [{}] {:.0f}% lift={:.1f} ({}/{}) {}\n'.format(
        i, p['result'], p['pct']*100, p['lift'], p['correct'], p['total'], cs))

summary = ''.join(parts)

# Find existing
q = {'filter': {'property': 'Name', 'title': {'contains': 'PatternLib'}}}
existing = nc('POST', 'https://api.notion.com/v1/databases/' + DB_ID + '/query', q).get('results', [])

def build_blocks(text):
    blocks = []
    i = 0
    while i < len(text):
        end = min(i + 1900, len(text))
        if end < len(text):
            nl = text.rfind('\n', i, end + 30)
            if nl > i:
                end = nl + 1
        chunk = text[i:end].strip()
        if chunk:
            blocks.append({
                'object': 'block', 'type': 'code',
                'code': {'language': 'markdown',
                         'rich_text': [{'type': 'text', 'text': {'content': chunk[:2000]}}]}
            })
        i = end
    return blocks

if existing:
    pid = existing[0]['id']
    print('Updating pattern library page...')
    for b in nc('GET', 'https://api.notion.com/v1/blocks/' + pid + '/children?page_size=100').get('results', []):
        nc('DELETE', 'https://api.notion.com/v1/blocks/' + b['id'])
    blocks = build_blocks(summary)
    nc('PATCH', 'https://api.notion.com/v1/blocks/' + pid + '/children', {'children': blocks})
    print('Updated: {} blocks'.format(len(blocks)))
else:
    print('Creating pattern library page...')
    blocks = build_blocks(summary)
    body = {
        'parent': {'database_id': DB_ID},
        'properties': {
            'Name': {'title': [{'text': {'content': 'PatternLib {}p'.format(len(patterns))}}]},
            '比赛': {'rich_text': [{'text': {'content': 'Pattern Lib {}p'.format(len(patterns))}}]},
        },
        'children': blocks
    }
    r = nc('POST', 'https://api.notion.com/v1/pages', body)
    if 'id' in r:
        print('Created: {}'.format(r['id'][:30]))
    else:
        print('FAIL: {}'.format(r.get('message', '?')[:200]))
print('Pattern library sync to Notion done')
