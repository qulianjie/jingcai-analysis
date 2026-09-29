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
COOKIE = 'path=/; __tst_status=204872233#; EO_Bot_Ssid=267517952; EO-Bot-Captcha-Token=t04IgEs8RUwV--QQaw8eSL-YzQXlH4VmlZKGtIV96h-rkpLj_6IeXTnChx2qNl0jdxhFAzaW_9QNAR_snFZi-VUlCwjPtmpOvcIxx9xvN5lbm5-PEXgCdVKDU3Mx-qVFOlFH-QmGFpYNMpseX7u2Du2wkqDVwxZS-lBhh5p4lRFN900i_Sv4WIDEoFvH9DBJxXzHI-41SzvcelLJnACnXAjysJtA7CggR3EmB8y66LR2nzY2yWDW-Q6MqA0yr9oqFrvgkUc9vkDIxmCkmKVGP0bIiKE6P91N2Eu_T4j4TaGYeY1CqgEikfVivTz9dhILOJYZ11qkT6hw5oZnwMLIJ90eSiY_jFfDdmMxUk8XrDvd1LbTT95XOxfAONROJaq_egrRPWwZ9DklumS-3EIxTImVQhCogbUh34VPCnn0v4JH58_azqeExVDJKu2psb7owT6; ck_RegFromUrl=https%3A//odds.500.com/fenxi/ouzhi-1430497.shtml; WT_FPC=id=undefined:lv=1790664092138:ss=1790664092138; sdc_session=1790664092140; sdc_userflag=1790664092141::1790664092141::1; HMACCOUNT_BFESS=2D0D99F53CC203CB; Hm_lvt_4f816d475bb0b9ed640ae412d6b42cab=1790664092; Hm_lpvt_4f816d475bb0b9ed640ae412d6b42cab=1790664092; HMACCOUNT=2D0D99F53CC203CB; _jzqa=1.934754673968950000.1790664092.1790664092.1790664092.1; _jzqc=1; _jzqx=1.1790664092.1790664092.1.jzqsr=odds%2E500%2Ecom|jzqct=/fenxi/ouzhi-1430497%2Eshtml.-; _jzqckmp=1; BAIDUID_BFESS=C653BFFD093CD16E8C8BF479FF8A8B45:FG=1; _qzja=1.1875972722.1790664092344.1790664092344.1790664092345.1790664092344.1790664092345.0.0.0.1.1; _qzjc=1; _qzjto=1.1.0; v1=1!YF#m^#O.>ZFg1:IXAi; _jzqb=1.1.10.1790664092.1; _qzjb=1.1790664092344.1.0.0.0; CLICKSTRN_ID=2408:822f:2093:5940:5000:f485:3332:3717-1790664091.9541898::982F2A90478ED9A340EB4395B1E25D30; __utma=63332592.246098776.1790664093.1790664093.1790664093.1; __utmc=63332592; __utmz=63332592.1790664093.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; __utmb=63332592.1.10.1790664093'

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
