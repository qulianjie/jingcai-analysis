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
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36'

# 用户浏览器过验证后的完整 cookie 集 (refresh_500_ticket.py 自动更新)
COOKIE = 'EO-Bot-Captcha-Token=t04PHsuN0T6MU079_p2rn9kSokm51VTlMGaxDm2kM9RJSwSwTBL4ipP0_qGxFgU_X59cKMOLYPguN7hkTYkOdpqK_Gse88IEYOupu_0BVHmATTmC-5qT5pzTCWwIj9TiIWGFSNjVtFQR9R_1Y_2nErhhKzkB1YanJtY72VJ5cLjNrNQYizj7EFEUoe2Qg390hWfSH3ApfszenvqrC8HrZpe5r-fINLV9PozqnhZY_BjGsoAij__ncpmpVKpiQKY5JzLfuO0UNFnDevVqACanrBCgNRNNaTDa17x7euCxKCuoRcL8-A6-sCtqx9nFjsgZH3D_EX7M2egLX2pJKfQuzeOoQvPrEPdNaIS4VuZ0WlSq706gtafuXVmzdlZ9plJVHifOhg1gY1Tyu-AdpYAosd8vCIpqMtFFLDW-ZvSz2MjAwuScGp3vYjIHnMAusWrqOb8; ck_RegFromUrl=https%3A//odds.500.com/fenxi/ouzhi-1430497.shtml; sdc_session=1788518959263; Hm_lvt_4f816d475bb0b9ed640ae412d6b42cab=1788518959; HMACCOUNT=A8A27CB2EB945C7C; _jzqa=1.3506536222240313300.1788518959.1788518959.1788518959.1; _jzqc=1; _jzqx=1.1788518959.1788518959.1.jzqsr=odds%2E500%2Ecom|jzqct=/fenxi/ouzhi-1430497%2Eshtml.-; _jzqckmp=1; _qzjc=1; __utma=63332592.757332690.1788518960.1788518960.1788518960.1; __utmc=63332592; __utmz=63332592.1788518960.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; WT_FPC=id=undefined:lv=1788519112348:ss=1788518959261; sdc_userflag=1788518959263::1788519112350::2; Hm_lpvt_4f816d475bb0b9ed640ae412d6b42cab=1788519112; _qzja=1.1166437582.1788518959339.1788518959339.1788518959339.1788518959339.1788519112390.0.0.0.2.1; _qzjb=1.1788518959339.2.0.0.0; _qzjto=2.1.0; _jzqb=1.2.10.1788518959.1; __utmb=63332592.2.10.1788518960; CLICKSTRN_ID=2408:822f:2091:cd40:ace3:930b:58bd:2c32-1788518959.6588182::D7AD80A7116E22F804AAD5F2EC9CF3FB'

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
