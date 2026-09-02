# -*- coding: utf-8 -*-
"""500.com 请求头统一配置 — 2026-09-02 用户真人过验证后落地

odds.500.com 腾讯EdgeOne 双层防护破解:
  1. UA 必须匹配用户浏览器 (Chrome/147.0.0.0) — ticket 绑定 UA，不匹配仍被拦
  2. Cookie 需含 EO-Bot-Captcha-Token (用户勾选验证签发, 30天有效, 过期需重新验证)
  3. 完整浏览器头 (Sec-Fetch-* 等) 降低被拦概率

2026-09-02 实测: 仅带 3 个核心 cookie + UA Chrome/147 → yazhi 页 128KB 正常返回(含"威")
"""
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36'

# 用户浏览器过验证后的核心 cookie（其余统计 cookie 非必需）
COOKIE = ('__tst_status=2963622577#; '
          'EO_Bot_Ssid=2622816256; '
          'EO-Bot-Captcha-Token=t04mMyAXMoqJLBNK6rmu66xBOKUTMgb45guWuRqJOoLC-x3siLfhKNYQAvflMLlXfk8vEM6ZrgpeqbR1M3MG4qnlj-I20macsP-Sm-puKqCGS4DOvteKt_JYV3mDa-h_mV17ddKoX4O7snuNZ1jtKYoF1aZ0a4GNpPV9vsYgpJJIQjs-G0WFsgzdIPnVq8t8QvHJogdiMqrSmy3WcN90zrVWeIC_YiWV3lyOaSlP60BQ6muwIMX8C35_FJ885MG7Y3OYUPjDONp83W-ArelHVVEWxjn_xz8WIkJtJFmz9pi-YZ8k9Zpk9yKhKpCk4K5VLkF7mb3HAVzlUK_tfkkn-FVVL0AWZX_QfkkFkgXBi5Lc8p-JGLEwkJSxnwdv_WZaHTXgYtxhMjvxBwME87m3NiC3aDqrCLAgU2_QQpTd46Fxd3BUtzEHNgJSxxY1Zyzz81A')

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
