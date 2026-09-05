# -*- coding: utf-8 -*-
"""500.com EdgeOne ticket 自动续期工具 (2026-09-04 跑通)

原理: EdgeOne 对"真实 Chrome + 简单勾选验证"放行简单勾选框(非滑块)。
  1. 用 CDP 启动真实 Chrome(独立profile, 非playwright launch -> 无webdriver特征)
  2. playwright connect_over_cdp 连上, 访问 ouzhi 页
  3. 轮询找 #verifyCheckbox 点击("确认您是真人")
  4. 页面变正常后取 cookie, 更新 scripts/_http_common.py

用法: python refresh_500_ticket.py [--fid 1430497] [--commit]
  --fid: 用于触发验证的页面 (默认 1430497 周五001)
  --commit: 自动 git commit
退出码: 0=成功拿到新ticket并更新, 1=失败(验证码形态非勾选/超时)
"""
import argparse
import io
import os
import re
import subprocess
import sys
import time

CHROME = r"C:\Users\lianjie\AppData\Local\Google\Chrome\Application\chrome.exe"
HTTP_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_http_common.py")
TMP_PROFILE = r"C:\Users\lianjie\AppData\Local\Temp\pw_ticket_refresh"


def log(*a):
    print(*a)
    sys.stdout.flush()


def _is_pass(page):
    try:
        content = page.content()
        return len(content) > 5000 and "security verification" not in content.lower()
    except Exception:
        return False


def _kill_old_chrome():
    """杀掉上次残留的 ticket refresh chrome (按 profile 路径匹配)"""
    try:
        ps = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             f"Get-CimInstance Win32_Process | Where-Object {{ $_.Name -eq 'chrome.exe' -and $_.CommandLine -match 'pw_ticket_refresh' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}"],
            capture_output=True, timeout=30)
    except Exception as e:
        log(f"[warn] kill old chrome: {e}")


def _unique_profile():
    """每次用全新 profile, 避免残留状态干扰"""
    import datetime
    ts = datetime.datetime.now().strftime("%H%M%S")
    return rf"C:\Users\lianjie\AppData\Local\Temp\pw_ticket_{ts}"


def _get_cookies(ctx, url):
    """取 cookie, 带重试。优先 CDP Network.getAllCookies (含 session cookie L1),
    兜底 ctx.cookies(url)。2026-09-05 修复: ctx.cookies(url) 只返回持久 cookie,
    漏 session cookie (__tst_status/EO_Bot_Ssid) 导致 requests 缺 L1 被 EdgeOne 拦。"""
    import time as _t
    page = None
    for pg in (getattr(ctx, 'pages', None) or []):
        page = pg
        break
    for i in range(3):
        try:
            if page is not None:
                cdp = ctx.new_cdp_session(page)
                res = cdp.send("Network.getAllCookies")
                cookies = res.get("cookies", [])
                if cookies:
                    out = []
                    for c in cookies:
                        out.append({
                            "name": c["name"], "value": c["value"],
                            "domain": c.get("domain", ""), "path": c.get("path", "/"),
                            "secure": c.get("secure", False), "httpOnly": c.get("httpOnly", False),
                        })
                    return out
            return ctx.cookies(url)
        except Exception as e:
            log(f"  cookies retry {i+1}: {str(e)[:80]}")
            _t.sleep(3)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fid", default="1430497")
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()

    _kill_old_chrome()
    time.sleep(2)

    import datetime
    profile = _unique_profile()
    port = 9340 + int(datetime.datetime.now().strftime("%S")) % 10  # 9340-9349 避免端口占用
    subprocess.Popen([
        CHROME,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile}",
        "--no-first-run", "--no-default-browser-check",
        "--disable-blink-features=AutomationControlled",
        "about:blank",
    ])
    log(f"[1/5] Chrome launched (port {port})")
    time.sleep(6)

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        page = ctx.new_page() if not ctx.pages else ctx.pages[0]
        url = f"https://odds.500.com/fenxi/ouzhi-{args.fid}.shtml"
        log(f"[2/5] goto {url}")
        page.goto(url, timeout=60000, wait_until="domcontentloaded")

        # 若直接 PASS (ticket 可能还有效) 也取 cookie 返回
        if _is_pass(page):
            log("[3/5] already PASS (no captcha)")
        else:
            log("[3/5] captcha present, clicking checkbox...")
            clicked = 0
            for i in range(45):  # 90s
                time.sleep(2)
                if _is_pass(page):
                    log(f"  PASS after ~{(i+1)*2}s (clicked {clicked}x)")
                    break
                cap = None
                for f in page.frames:
                    if "captcha" in f.url or "gtimg" in f.url:
                        cap = f
                        break
                if cap:
                    try:
                        cb = cap.query_selector("#verifyCheckbox, .checkbox-verify, [class*=checkbox]")
                        if cb:
                            clicked += 1
                            cb.click(timeout=3000)
                        else:
                            text = cap.evaluate("document.body?document.body.innerText:''")
                            if "滑块" in text or "slide" in text.lower():
                                log(f"[FAIL] slider captcha (not auto-passable): {repr(text[:150])}")
                                browser.close()
                                return 1
                    except Exception as e:
                        log(f"  click err: {str(e)[:100]}")
            else:
                log("[FAIL] timeout 90s no pass")
                browser.close()
                return 1

        time.sleep(2)
        if not _is_pass(page):
            log("[FAIL] final check blocked")
            browser.close()
            return 1

        # [4/5] 取 cookie (全量 + 核心三值)
        cookies_all = _get_cookies(ctx, "https://odds.500.com")
        if cookies_all is None or not cookies_all:
            # 再访问一次确保 cookie 种全
            page.goto(f"https://odds.500.com/fenxi/ouzhi-{args.fid}.shtml", timeout=30000, wait_until="domcontentloaded")
            time.sleep(3)
            cookies_all = _get_cookies(ctx, "https://odds.500.com")
        if not cookies_all:
            log("[FAIL] no cookies")
            browser.close()
            return 1
        need = {}
        for c in cookies_all:
            if c["name"] in ("EO-Bot-Captcha-Token", "__tst_status", "EO_Bot_Ssid"):
                need[c["name"]] = c["value"]
        browser.close()
        if "EO-Bot-Captcha-Token" not in need:
            log("[FAIL] EO-Bot-Captcha-Token not in cookies")
            return 1
        log(f"[4/5] got token {need['EO-Bot-Captcha-Token'][:30]}... ({len(cookies_all)} cookies)")

        # [5/5] 更新 _http_common.py: 写完整 cookie 串 (EdgeOne 校验 cookie 集完整性)
        full_cookie = "; ".join(f"{c['name']}={c['value']}" for c in cookies_all)
        with io.open(HTTP_COMMON, encoding="utf-8") as f:
            src = f.read()
        # 替换 COOKIE 赋值行: 兼容 "COOKIE = None" 占位 或 "COOKIE = ('...')" 旧格式
        m = re.search(r"^COOKIE\s*=.*$", src, re.M)
        if not m:
            log("[FAIL] COOKIE line not found")
            browser.close()
            return 1
        src = src[:m.start()] + "COOKIE = " + repr(full_cookie) + src[m.end():]
        with io.open(HTTP_COMMON, "w", encoding="utf-8", newline="\n") as f:
            f.write(src)
        log(f"[5/5] wrote full cookie ({len(cookies_all)} items)")

        # 验证新 cookie 对 requests 生效 (保持原 UA 不变)
        sys.path.insert(0, os.path.dirname(HTTP_COMMON))
        import requests
        from _http_common import headers
        r = requests.get(f"https://odds.500.com/fenxi/ouzhi-{args.fid}.shtml",
                         headers=headers(), timeout=15)
        if len(r.content) > 3000:
            log(f"[OK] requests verified: {len(r.content)} bytes")
        else:
            log("[FAIL] requests still blocked after update")
            return 1

        if args.commit:
            subprocess.run(["git", "add", "-f", "_http_common.py"],
                           cwd=os.path.dirname(HTTP_COMMON), check=False)
            subprocess.run(["git", "commit", "-m",
                            f"fix(500): 自动续期EO-Bot-Captcha-Token (refresh_500_ticket.py, {need['EO-Bot-Captcha-Token'][:20]}...)",
                            "_http_common.py"],
                           cwd=os.path.dirname(HTTP_COMMON), check=False)
        log("[DONE] ticket refreshed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
