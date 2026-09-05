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
COOKIE = 'EO-Bot-Captcha-Token=t04sn7kGKrSze0rHCxqyCjWGK6ZFp9Y6ipHxBupMR-SXG9aM1Wo9WQs54rRxymnUM20pykPtUVUieaTNJaUgthBdnj2WoQNOeuX41bBUruDO3wjqQiZsOe3e7u16VfyLGb9cxg0GTIh0bsomliVaAKRNEr3B0bssFLOFi6a1emHEFcYOtQ8JHlpG1h5jOOgXj8ic0umfUmJtfcP3IMcw146fqAKcwm7qGYopX3s9Cd6WDdpm-MNrYz7xWMJkyj1ZpTeZFV2yzxpyFypjQMjgoV1eYVxTR6BDXFbpxztfdVs0obqj0REA7JBAQOeYGQQug5EAvShlmWF2TjDZv9TTdqLYCn9FO4I9sTCjSAgmDbbn8e0FHewRuT7m2GLQCfUP24qsy-tnbLnwdiJXUW7J9e0SZVtS4UwZacAT7I5-m9U3dJvJ1lrTtuep0YLtESMfVzZ; ck_RegFromUrl=https%3A//odds.500.com/fenxi/ouzhi-1430497.shtml; WT_FPC=id=undefined:lv=1788607250512:ss=1788607250512; sdc_session=1788607250514; sdc_userflag=1788607250515::1788607250515::1; Hm_lvt_4f816d475bb0b9ed640ae412d6b42cab=1788607251; Hm_lpvt_4f816d475bb0b9ed640ae412d6b42cab=1788607251; HMACCOUNT=84F56C771F424A9A; _jzqa=1.2627869779566779400.1788607251.1788607251.1788607251.1; _jzqc=1; _jzqx=1.1788607251.1788607251.1.jzqsr=odds%2E500%2Ecom|jzqct=/fenxi/ouzhi-1430497%2Eshtml.-; _jzqckmp=1; _qzja=1.1020405106.1788607250618.1788607250618.1788607250618.1788607250618.1788607250618.0.0.0.1.1; _qzjc=1; _qzjto=1.1.0; CLICKSTRN_ID=2408:822f:2091:cd40:91e9:d892:ef65:c7b3-1788607250.857891::59109EF79FA94E0DF5A1D1EE94685340; _jzqb=1.1.10.1788607251.1; _qzjb=1.1788607250618.1.0.0.0; __utma=63332592.1510378684.1788607251.1788607251.1788607251.1; __utmc=63332592; __utmz=63332592.1788607251.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; __utmb=63332592.1.10.1788607251; __tst_status=3531435374#; EO_Bot_Ssid=3389128704'

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
