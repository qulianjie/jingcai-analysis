# -*- coding: utf-8 -*-
"""samepan txt -> 历史匹配场次行尾补 百家/竞彩/IW 欧赔 + 竞彩让球指数
口径与 4way_match.py 一致：
  竞彩 = odds_europe.companies[] 中名字含'官'的行
  IW   = odds_europe.companies[] 中名字含'塞浦路斯'的行
  百家 = odds_europe.av (顶层, 来自'平均'/'百家'行) 缺则 companies 中'平均'/'百家'行
  让球 = odds_handicap.jc (竞彩官方让球)
有就带，没有留空。输出 samepan_odds_{date}.txt 供 make_docx 优先读取。
用法: python enrich_samepan_odds.py 2026-09-03
"""
import json, os, re, sys

OUT_DIR = r"C:\Users\lianjie\jingcai_out"
CACHE_DIR = r"C:\Users\lianjie\.openclaw\workspace\jingcai\data\league_cache"


def _fmt_tri(v):
    """v=[w,d,l] 或 dict-> 'w/d/l' 两位小数去尾零"""
    if isinstance(v, dict):
        v = [v.get("lw"), v.get("ld"), v.get("ll")]
    if not v or len(v) < 3 or not all(x is not None for x in v):
        return None
    parts = []
    for x in v:
        try:
            f = float(x)
        except (TypeError, ValueError):
            return None
        parts.append(f"{f:.2f}")
    return "/".join(parts)


def _live_of(d):
    """dict(iw,id,il,lw,ld,ll) -> [lw,ld,ll]"""
    if not d:
        return None
    if d.get("lw") is not None:
        return [d.get("lw"), d.get("ld"), d.get("ll")]
    return [d.get("iw"), d.get("id"), d.get("il")]


def extract_odds(rec):
    """返回 [(label, text)], 与4way口径一致"""
    oe = rec.get("odds_europe") or {}
    if not isinstance(oe, dict):
        oe = {}
    comps = oe.get("companies") or []
    out = []

    # 竞彩: companies '官' 行
    guan = None
    for c in comps:
        if "官" in str(c.get("name", "")):
            guan = c
            break
    if guan:
        init = _fmt_tri(guan.get("init") or [guan.get("iw"), guan.get("id"), guan.get("il")])
        live = _fmt_tri(guan.get("live") or _live_of(guan))
        if init and live:
            out.append(("竞", f"{init}→{live}"))
        elif live:
            out.append(("竞", live))
    elif not comps:
        # 无companies(旧缓存): 顶层jc若与iw不同才可信
        jc = oe.get("jc")
        iw = oe.get("iw")
        if isinstance(jc, dict) and isinstance(iw, dict):
            if _live_of(jc) != _live_of(iw):
                live = _fmt_tri(_live_of(jc))
                if live:
                    out.append(("竞", live))
        elif isinstance(jc, dict):
            live = _fmt_tri(_live_of(jc))
            if live:
                out.append(("竞", live))

    # 百家: 顶层 av, 缺则 companies '平均'/'百家' 行
    av = oe.get("av")
    av_txt = _fmt_tri(_live_of(av)) if isinstance(av, dict) else None
    if not av_txt:
        for c in comps:
            nm = str(c.get("name", ""))
            if "平均" in nm or "百家" in nm:
                av_txt = _fmt_tri(c.get("live") or _live_of(c))
                break
    if av_txt:
        out.append(("百", av_txt))

    # IW: companies '塞浦路斯' 行
    sai = None
    for c in comps:
        if "塞浦路斯" in str(c.get("name", "")):
            sai = c
            break
    if sai:
        init = _fmt_tri(sai.get("init") or [sai.get("iw"), sai.get("id"), sai.get("il")])
        live = _fmt_tri(sai.get("live") or _live_of(sai))
        if init and live:
            out.append(("IW", f"{init}→{live}"))
        elif live:
            out.append(("IW", live))

    # 竞彩让球: odds_handicap.jc
    oh = rec.get("odds_handicap") or {}
    hc = oh.get("jc") if isinstance(oh, dict) else None
    if isinstance(hc, dict):
        hc_live = _fmt_tri(_live_of(hc))
        if hc_live:
            handicap = hc.get("handicap")
            out.append(("让", f"{handicap} {hc_live}" if handicap else hc_live))
    return out


def load_cache_maps():
    maps = {}
    if not os.path.isdir(CACHE_DIR):
        return maps
    for fn in os.listdir(CACHE_DIR):
        if not fn.endswith(".json"):
            continue
        p = os.path.join(CACHE_DIR, fn)
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        allm = d.get("all_matches", [])
        if not allm:
            continue
        idx = {}
        for m in allm:
            date = str(m.get("MATCHDATE", m.get("VSDATE", "")))[:10]
            h = m.get("HOMETEAMSXNAME", "")
            a = m.get("AWAYTEAMSXNAME", "")
            hs = m.get("HOMESCORE")
            as_ = m.get("AWAYSCORE")
            if not date or not h or not a:
                continue
            key = (date, h, a, hs, as_)
            if key not in idx:
                idx[key] = m
        maps[fn] = idx
    return maps


def main():
    if len(sys.argv) < 2:
        print("usage: enrich_samepan_odds.py 2026-09-03")
        return
    date_s = sys.argv[1]
    src = os.path.join(OUT_DIR, f"samepan_{date_s}.txt")
    if not os.path.exists(src):
        print(f"[ERR] missing {src}")
        return
    maps = load_cache_maps()
    print(f"[cache] {len(maps)} league files loaded")

    n_hist = 0
    stats = {"竞": 0, "百": 0, "IW": 0, "让": 0}
    out_lines = []
    for ln in open(src, encoding="utf-8"):
        raw = ln.rstrip("\n").rstrip("\r")
        m = re.match(r"^\s*\[(\d{4}-\d{2}-\d{2})\]\s+(\S+)\s+vs\s+(\S+)\s+(\d+):(\d+)", raw)
        if m:
            n_hist += 1
            key = (m.group(1), m.group(2), m.group(3), int(m.group(4)), int(m.group(5)))
            rec = None
            for idx in maps.values():
                if key in idx:
                    rec = idx[key]
                    break
            if rec:
                odds = extract_odds(rec)
                if odds:
                    for label, txt in odds:
                        stats[label] += 1
                    raw = raw.rstrip() + "  " + "  ".join(f"{lb}:{tx}" for lb, tx in odds)
        out_lines.append(raw + "\n")

    out_path = os.path.join(OUT_DIR, f"samepan_odds_{date_s}.txt")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(out_lines)
    print(f"[done] {out_path}  hist={n_hist}  {dict(stats)}")


if __name__ == "__main__":
    main()
