# -*- coding: utf-8 -*-
"""
竞彩数据获取脚本模板 - 带反爬机制
用法: python fetch_odds.py <match_id>
"""
import requests
from bs4 import BeautifulSoup
import random
import time
import re
import json
import sys

# ==================== 反爬配置 ====================

# 随机User-Agent池
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

def get_headers(referer=None):
    """生成随机请求头"""
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    if referer:
        headers["Referer"] = referer
    else:
        headers["Referer"] = "https://odds.500.com/"
    return headers

def fetch_with_retry(url, max_retries=3, delay_range=(1.5, 4.0), referer=None):
    """
    带重试和延迟的请求
    
    Args:
        url: 目标URL
        max_retries: 最大重试次数
        delay_range: 请求间隔范围(秒)，随机取值避免被检测
        referer: Referer头
    
    Returns:
        requests.Response 或 None
    """
    session = requests.Session()
    
    for attempt in range(max_retries):
        try:
            # 随机延迟，模拟人类行为
            delay = random.uniform(*delay_range)
            if attempt > 0:
                print(f"  重试 {attempt}/{max_retries} (等待{delay:.1f}s)...")
            time.sleep(delay)
            
            resp = session.get(
                url,
                headers=get_headers(referer),
                timeout=15,
                allow_redirects=True
            )
            
            # 处理429限流
            if resp.status_code == 429:
                wait = random.uniform(5, 15) * (attempt + 1)
                print(f"  ⚠️ 429限流，等待{wait:.1f}s后重试")
                time.sleep(wait)
                continue
            
            # 处理503等服务器错误
            if resp.status_code >= 500:
                print(f"  ⚠️ 服务器错误 {resp.status_code}")
                continue
            
            if resp.status_code == 200:
                return resp
            
            print(f"  ⚠️ HTTP {resp.status_code}")
            
        except requests.exceptions.Timeout:
            print(f"  ⚠️ 请求超时")
        except requests.exceptions.ConnectionError:
            print(f"  ⚠️ 连接错误")
        except Exception as e:
            print(f"  ⚠️ 错误: {e}")
    
    return None

def parse_gbk_safe(resp):
    """安全解析GBK编码页面"""
    # 尝试多种编码
    for encoding in ['gbk', 'gb2312', 'gb18030', 'utf-8']:
        try:
            resp.encoding = encoding
            text = resp.text
            # 检查是否有乱码
            if '\ufffd' not in text or len(text) > 1000:
                return text
        except:
            continue
    # 最后用replace模式
    resp.encoding = 'gbk'
    return resp.text.encode('utf-8', errors='replace').decode('utf-8')

# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 示例：获取欧赔页面
    match_id = sys.argv[1] if len(sys.argv) > 1 else "1362643"
    
    url = f"https://odds.500.com/fenxi/ouzhi-{match_id}.shtml"
    print(f"获取: {url}")
    
    resp = fetch_with_retry(url, referer="https://odds.500.com/fenxi/")
    
    if resp:
        html = parse_gbk_safe(resp)
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('title')
        print(f"标题: {title.text if title else '无'}")
        print(f"内容长度: {len(html)}")
    else:
        print("获取失败")
