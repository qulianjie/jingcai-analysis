#!/usr/bin/env python3
"""HTTP bridge for Notion/500.com API via curl with retries and GBK support."""
import json, subprocess, sys, time

def http_call(method, url, headers=None, body=None, retries=3):
    for attempt in range(retries):
        cmd = ['curl', '-s', '--max-time', '30', '-w', '\n%{http_code}\n', '-X', method, url]
        if headers:
            for k, v in headers.items():
                cmd += ['-H', '%s: %s' % (k, v)]
        if body:
            cmd += ['-d', body]
        try:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            if r.returncode == 0 and r.stdout:
                out = r.stdout.decode('utf-8', errors='replace')
                lines = out.strip().split('\n')
                if len(lines) >= 2:
                    http_code = lines[-1].strip()
                    response_body = '\n'.join(lines[:-1])
                    result = {'status': int(http_code) if http_code.isdigit() else 0}
                    if response_body:
                        try:
                            result['json'] = json.loads(response_body)
                        except:
                            result['raw'] = response_body[:500]
                    return result
        except:
            pass
        if attempt < retries - 1:
            time.sleep(2 ** attempt)
    return {'error': 'all retries failed', 'status': 0}

AUTH = 'Bearer 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'
NIV = '2022-06-28'

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else ''
    if action == 'query-db':
        db_id = sys.argv[2]
        flt = sys.argv[3] if len(sys.argv) > 3 else '{}'
        r = http_call('POST', 'https://api.notion.com/v1/databases/%s/query' % db_id,
                      {'Authorization': AUTH, 'Notion-Version': NIV, 'Content-Type': 'application/json'}, flt)
        print(json.dumps(r, ensure_ascii=False))
    elif action == 'patch-page':
        pid = sys.argv[2]
        props = sys.argv[3] if len(sys.argv) > 3 else '{}'
        r = http_call('PATCH', 'https://api.notion.com/v1/pages/%s' % pid,
                      {'Authorization': AUTH, 'Notion-Version': NIV, 'Content-Type': 'application/json'}, props)
        print(json.dumps(r, ensure_ascii=False))
    elif action == 'create-page':
        body = sys.argv[2] if len(sys.argv) > 2 else '{}'
        r = http_call('POST', 'https://api.notion.com/v1/pages',
                      {'Authorization': AUTH, 'Notion-Version': NIV, 'Content-Type': 'application/json'}, body)
        print(json.dumps(r, ensure_ascii=False))
    elif action == 'archive-page':
        pid = sys.argv[2]
        r = http_call('PATCH', 'https://api.notion.com/v1/pages/%s' % pid,
                      {'Authorization': AUTH, 'Notion-Version': NIV, 'Content-Type': 'application/json'}, '{"archived": true}')
        print(json.dumps(r, ensure_ascii=False))
    elif action == 'fetch-500':
        ds = sys.argv[2] if len(sys.argv) > 2 else ''
        cmd = ['curl', '-s', '--max-time', '30', '-w', '\nHTTP_CODE:%{http_code}',
               'https://trade.500.com/jczq/?playid=269&g=2&date=%s' % ds,
               '-H', 'User-Agent: Mozilla/5.0', '-H', 'Accept: text/html']
        try:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            if r.returncode == 0:
                raw = r.stdout
                parts = raw.rsplit(b'\nHTTP_CODE:', 1)
                body = parts[0] if len(parts) > 1 else raw
                http_code = parts[1].strip() if len(parts) > 1 else b'0'
                try:
                    decoded = body.decode('gbk', errors='replace')
                except:
                    decoded = body.decode('utf-8', errors='replace')
                print(json.dumps({'status': int(http_code), 'body': decoded}, ensure_ascii=False))
            else:
                print(json.dumps({'error': 'curl exit %d' % r.returncode}))
        except Exception as e:
            print(json.dumps({'error': str(e)[:200]}))
    else:
        print(json.dumps({'error': 'Unknown: %s' % action}))

if __name__ == '__main__':
    main()
