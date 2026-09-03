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
          'EO-Bot-Captcha-Token=t04kl--ixHJuXvy3Ql0UHOJn2vT1KHkOWPMYAyc_OzIzv-kQzaubTNVk3UZ9HHNM2ClOIHU-dnAMCZyZC7-qiQ871_Uca-Lu2vdgg2J82UElP2dCZn6tlxTTeNdC1I-2sQcKHIuPS-Hi-IRH_nnsu-3JzHd0pmRd8dTO2lH-zUErVqgaCOrviymQ0hCAc3pZF4LXU3wLdaTl9KOy6qXoYpuhbRSnXi7GaQhd1NXDHqZusiX-SlNJllREQpyDWyrND7LgvAu4Dea_RAQE_fTsYmekZLIAmQvjuHs6iumOFqJuF2bmDx4pKd6nx3uxJC00uaNL5ZMe_aYuub13lwtjUnFhKE1voCanDhP4LBC8jB_NQ-2VJDVSsMDWTlBqaM4gED0fTk1eb1yB4rYAavy9XfTiUBLwezikCjtCvmPciCIlMboxblM1-h5Pn1hc-xUqQ-b')

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
