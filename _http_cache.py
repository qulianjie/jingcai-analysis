# -*- coding: utf-8 -*-
"""
HTTP 缓存层 — 文件级缓存，替代 requests.Session
缓存策略：按 URL 存储原始 HTML，TTL 可配置
缓存路径：data/http_cache/{md5}.html + {md5}.meta.json

使用方式：
    from _http_cache import CachedSession
    sess = CachedSession(ttl=3600)  # 1小时缓存
    resp = sess.get(url)  # 自动走缓存/回源
"""

import os, json, hashlib, time, requests
from datetime import datetime

# 脚本目录（与各 step 脚本同级）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPT_DIR, 'data', 'http_cache')
DEFAULT_TTL = 3600  # 1小时

_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def _url_to_key(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()

def _cache_paths(url):
    key = _url_to_key(url)
    html_path = os.path.join(CACHE_DIR, key + '.html')
    meta_path = os.path.join(CACHE_DIR, key + '.meta.json')
    return html_path, meta_path

def _is_fresh(meta_path, ttl):
    if not os.path.exists(meta_path):
        return False
    try:
        with open(meta_path, 'r') as f:
            meta = json.load(f)
        age = time.time() - meta['cached_at']
        return age < ttl
    except:
        return False

def clear_cache(ttl=None):
    """清理过期缓存；ttl=None 清所有"""
    if not os.path.isdir(CACHE_DIR):
        return 0
    count = 0
    now = time.time()
    for fname in os.listdir(CACHE_DIR):
        if fname.endswith('.meta.json'):
            fpath = os.path.join(CACHE_DIR, fname)
            try:
                with open(fpath, 'r') as f:
                    meta = json.load(f)
                if ttl is None or (now - meta['cached_at']) > ttl:
                    base = fname.replace('.meta.json', '')
                    for ext in ['.html', '.meta.json']:
                        p = os.path.join(CACHE_DIR, base + ext)
                        if os.path.exists(p):
                            os.remove(p)
                            count += 1
            except:
                pass
    return count


class CachedSession:
    """Drop-in replacement for requests.Session with file-level HTTP caching"""

    def __init__(self, ttl=None, headers=None):
        self.ttl = ttl if ttl is not None else DEFAULT_TTL
        os.makedirs(CACHE_DIR, exist_ok=True)
        self._session = requests.Session()
        self._session.headers.update(headers or _headers)

    @property
    def headers(self):
        return self._session.headers

    def get(self, url, **kwargs):
        # 构建完整URL（params参数拼入URL，确保缓存key唯一）
        import urllib.parse
        params = kwargs.pop('params', None)
        if params:
            url_parts = list(urllib.parse.urlparse(url))
            existing_params = urllib.parse.parse_qs(url_parts[4])
            existing_params.update(params)
            url_parts[4] = urllib.parse.urlencode(existing_params, doseq=True)
            url = urllib.parse.urlunparse(url_parts)
        html_path, meta_path = _cache_paths(url)

        # 缓存命中
        if _is_fresh(meta_path, self.ttl):
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
                # 构造假的 Response 对象
                resp = requests.Response()
                resp.status_code = 200
                resp._content = content.encode('utf-8')
                resp.encoding = meta.get('encoding', 'utf-8')
                resp.url = url
                resp.headers['Content-Type'] = 'text/html'
                # 增加扩展属性标识缓存来源
                resp._from_cache = True
                resp._cached_at = meta['cached_at']
                return resp
            except:
                pass  # 缓存损坏则回源

        # 回源
        resp = self._session.get(url, **kwargs)
        if resp.status_code == 200 and resp.text:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(resp.text)
            meta = {
                'url': url,
                'cached_at': time.time(),
                'status': resp.status_code,
                'encoding': resp.encoding,
            }
            with open(meta_path, 'w') as f:
                json.dump(meta, f)

        resp._from_cache = False
        return resp

    def close(self):
        self._session.close()
