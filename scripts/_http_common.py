# -*- coding: utf-8 -*-
"""500.com 请求头统一配置 — 2026-09-02 用户真人过验证后落地

odds.500.com 腾讯EdgeOne 双层防护破解:
  1. UA 必须匹配用户浏览器 (Chrome/147.0.0.0) — ticket 绑定 UA，不匹配仍被拦
  2. Cookie 需含 EO-Bot-Captcha-Token (用户勾选验证签发)
  3. 完整浏览器头 (Sec-Fetch-* 等) 降低被拦概率

⚠️ 2026-09-04 重大更新: 自动续期工具 scripts/refresh_500_ticket.py
  - ticket 吊销后跑它即可自动过 EdgeOne 勾选验证并更新本文件 COOKIE
  - 实测: cookie 必须带完整集(统计cookie也要), 仅3个核心值会被拦(987B)
  - UA 必须保持 Chrome/147.0.0.0 (完整版本号 147.0.7727.56 反而被拦!)
"""
def _detect_chrome_major():
    """自动跟随本机 Chrome 大版本 (2026-09-29 教训 — 根因修复)

    EdgeOne 的 ticket 绑定 UA 大版本: Chrome 从 147 自动升级到 153 后,
    写死的 Chrome/147.0.0.0 会让所有请求被拦(983B JS 挑战页 / 2170B 拦截页),
    而 SQL 排查时会误判成 "ticket 过期" 反复刷 refresh (无效)。
    这里动态读本机 Chrome 版本, 避免每次 Chrome 更新都要手工改本文件。
    """
    import os as _os
    import re as _re
    try:
        app = _os.path.join(_os.environ.get("LOCALAPPDATA")
                            or r"C:\Users\lianjie\AppData\Local",
                            "Google", "Chrome", "Application")
        vers = [int(d.split(".")[0]) for d in _os.listdir(app)
                if _re.match(r"^\d+\.\d+\.\d+\.\d+$", d)]
        if vers:
            return max(vers)
    except Exception:
        pass
    return None


_CHROME_MAJOR = _detect_chrome_major() or 153   # 探测失败时回退到最后已知可用版本

# ⚠️ 必须是 "Chrome/<大版本>.0.0.0": 完整版本号(如 153.0.8010.53) 反而会被拦
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/%d.0.0.0 Safari/537.36') % _CHROME_MAJOR

# 用户浏览器过验证后的完整 cookie 集 (refresh_500_ticket.py 自动更新)
COOKIE = 'EO-Bot-Captcha-Token=t04oPT3N2n3pscmAVuWyXWzl23vQUt97Mzo23HeoXGI86NsbneR16xRAsxhgjeiiLm1OxkGeV3WSIN27x5t-zf9jXkB9XNtDoHHfBsI6r5eRTJgPBXM9m8J-GRWNb8pVJSZQwMZ6HHzLmXGF35Y8Sf-s7gzw6wfGulk7aN3gV3q83uWlaYXBDBRjrAOWkDLJD6A9jdml5fxNbexmhVZhd81GaB-M1mL14eAH-_dapyl1ktx5BXSGUBIe_hrUCHGchuxEUI-3Y01-3vMgUKAbpQ5b99DU6Vh9xvU_rtaxwREw-YndVVE4_99vAGK0WjpBk2kWnrSvMVAzo7IXOodSOIq67q72Wzp8NzrFN4Bq05-ve5daOA4SbVSIu3n740yIRwPDN_I-XvzpgpsVej5PVA7QoKQ1HJSe7oPI3cS1CI3JXY_b5kBvE5Xwwmf1FsPkPV0; ck_RegFromUrl=https%3A//odds.500.com/fenxi/ouzhi-1430497.shtml; WT_FPC=id=undefined:lv=1790659730877:ss=1790659730877; sdc_session=1790659730880; sdc_userflag=1790659730881::1790659730881::1; HMACCOUNT_BFESS=B16A9ECC0A228DD9; Hm_lvt_4f816d475bb0b9ed640ae412d6b42cab=1790659731; Hm_lpvt_4f816d475bb0b9ed640ae412d6b42cab=1790659731; HMACCOUNT=B16A9ECC0A228DD9; _jzqa=1.1391156886679796700.1790659731.1790659731.1790659731.1; _jzqc=1; _jzqx=1.1790659731.1790659731.1.jzqsr=odds%2E500%2Ecom|jzqct=/fenxi/ouzhi-1430497%2Eshtml.-; _jzqckmp=1; _qzja=1.1334047856.1790659730970.1790659730970.1790659730970.1790659730970.1790659730970.0.0.0.1.1; _qzjc=1; _qzjto=1.1.0; BAIDUID_BFESS=34EA7F2B6EEFC2E0CB713ED9E687FFB8:FG=1; v1=KZy^.rUKw0>ZFg1HJ[q%; _jzqb=1.1.10.1790659731.1; _qzjb=1.1790659730970.1.0.0.0; CLICKSTRN_ID=2408:822f:2093:5940:5000:f485:3332:3717-1790659731.3508115::ECE4319FB9924FDBB89DAB695F7716D7; __utma=63332592.743071124.1790659733.1790659733.1790659733.1; __utmc=63332592; __utmz=63332592.1790659733.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; __utmb=63332592.1.10.1790659733'

# 澳客数据源已弃用 (2026-09-02 用户指令"去掉澳客 只留500") — 各脚本用此开关禁用 okooo 分支
USE_OKOOO = False


def headers(referer='https://odds.500.com/'):
    """带 EdgeOne 认证的完整浏览器请求头"""
    return {
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Referer': referer,
        'Cookie': COOKIE,
    }
