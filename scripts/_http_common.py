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

COOKIE = ('__tst_status=414040839#; '

          'EO_Bot_Ssid=4048158720; '

          'EO-Bot-Captcha-Token=t04FmzB6RKyUte0rfDufPRg72GgHx5rRbdoj3CnTSXEMc-werAFEpqFC3xNWAsq04-eUkPyOPYnYssQxo0vu7Iu-UU4EQ6QMyC_kMg1-c4QnUeWurYmfolK4BBo3VpyjnOWqyTXx5gwdtgyFfq1zRQ9J4o33E4SWs1_QmfFjW0D5IpQ6C0bxWV7gomnR9Hk0UQp-0xqOIyJyQ-kOC-OzIPwezR3EqF2QBQ1CQyh1FZjAIgIHzy885m9g3Xoe5tisloKBMbguIlEiPn2cehRq4BgSS_eYLu2y_RUGPODTVoWj-g6wLbcbkBIWpMuk2bV5RFdQnJXh1dVTlVZ3ogrtQEkhu-TCH-kNc_3EhY1VjtSSPfb33p9vUjNFcVWcWrGm7JmWusG7L25W0pYkBuGa8WoF3nTDocD6q5P0H_m6O9FPnpZcsVs3zgnssvROKTrSIfl')



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

