# -*- coding: utf-8 -*-
import os, requests

key_path = os.path.expanduser('~/.config/notion/api_key')
with open(key_path, 'rb') as f:
    token = f.read().decode('utf-16').strip()

url = 'https://api.notion.com/v1/databases/36191ad717ba80beb656cc7c0baaa33d'
headers = {
    'Authorization': 'Bearer %s' % token,
    'Notion-Version': '2025-09-03',
}

resp = requests.get(url, headers=headers, timeout=30)
print('Status: %d' % resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    print('Title: %s' % data.get('title', [{}])[0].get('plain_text', 'N/A'))
    props = data.get('properties', {})
    print('\nProperties:')
    for name, info in props.items():
        ptype = info.get('type', '?')
        print('  %s: %s' % (name, ptype))
else:
    print('Error: %s' % resp.text[:500])
