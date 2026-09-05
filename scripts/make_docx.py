# -*- coding: utf-8 -*-
"""5工具txt -> 手机易读 docx (每场 merge→4way→min→sameodds→samepan)
用法: python make_docx.py 2026-09-03
"""
import html, os, re, sys
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_LINE_SPACING

OUT_DIR = r"C:\Users\lianjie\jingcai_out"
TOOL_ORDER = ["merge", "4way", "min", "sameodds", "av_sameodds", "samepan"]
TOOL_COLORS = {"merge": "E67E22", "4way": "2980B9", "min": "27AE60",
               "sameodds": "8E44AD", "av_sameodds": "16A085", "samepan": "C0392B"}
TOOL_CN = {"merge": "合成信号", "4way": "四维匹配", "min": "最小值匹配",
           "sameodds": "同赔初盘", "av_sameodds": "百家同赔", "samepan": "同盘统计"}

def read_txt(path):
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n").replace("\r", "\n")

def match_key(line):
    line2 = re.sub(r"^(【[^】]*】|\[[^\]]*\])\s*", "", line).strip()
    m = re.search(r"([^\s]+)\s+vs\s+([^\s（(]+)", line2)
    if not m:
        return None
    return f"{m.group(1).strip()} vs {m.group(2).strip()}"

def split_sections(text, tool):
    lines = text.split("\n")
    sections = []
    cur_key = None
    cur = []
    def flush():
        nonlocal cur_key, cur
        if cur_key and cur:
            sections.append((cur_key, "\n".join(cur)))
        cur_key = None
        cur = []
    for ln in lines:
        is_title = False
        if tool == "4way":
            if re.match(r"^(?!\[)\S.*\bvs\b.*FID=\d+", ln) and not re.match(r"^\d{4}-", ln):
                is_title = True
        elif tool == "min":
            is_title = bool(re.match(r"^\[\d+/\d+\] ", ln))
        elif tool == "merge":
            is_title = bool(re.match(r"^\[\d{2}\] ", ln))
        elif tool in ("sameodds", "av_sameodds"):
            is_title = bool(re.match(r"^【.*\d{3}】", ln))
        elif tool == "samepan":
            is_title = bool(re.match(r"^\[(?:周[一二三四五六日天])?\d{3}\] ", ln))
        if is_title:
            flush()
            key = match_key(ln)
            cur_key = key
            cur = [ln]
        else:
            if cur_key is not None:
                cur.append(ln)
    flush()
    return sections

def transform_sameodds(body):
    out = []
    for ln in body.split("\n"):
        s = ln.strip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip().strip("|").split("|")]
            if not cells:
                out.append(ln); continue
            if cells[0] == "赛事" or (cells[0] and set(cells[0]) <= set("-: ")):
                continue
            if len(cells) >= 7:
                league, date_, vs_, result_, p0, p1, trend = cells[:7]
                matchlvl = cells[7] if len(cells) > 7 else ""
                out.append(f"{league} {date_} {vs_} {result_} [{matchlvl}]".rstrip())
                out.append(f"   初:{p0} -> 终:{p1} {trend}")
            else:
                out.append(ln)
        else:
            out.append(ln)
    return "\n".join(out)



def transform_av_sameodds(body):
    """av_sameodds 表格(日期/对阵/比分/赛果/历史百家初/终/盘路) -> 紧凑行"""
    out = []
    for ln in body.split("\n"):
        s = ln.strip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip().strip("|").split("|")]
            if not cells:
                out.append(ln); continue
            if cells[0] in ("日期",) or (cells[0] and set(cells[0]) <= set("-: ")):
                continue
            if len(cells) >= 6:
                date_, vs_, score_, result_, p0 = cells[:5]
                p1 = cells[5] if len(cells) > 5 else ""
                trend = cells[6] if len(cells) > 6 else ""
                out.append(f"{date_} {vs_} {score_} {result_}")
                out.append(f"   初:{p0}  ->  终:{p1} {trend}".rstrip())
            else:
                out.append(ln)
        else:
            out.append(ln)
    return "\n".join(out)

def parse_date(datestr):
    if re.match(r"^\d{4}-\d{2}-\d{2}$", datestr): return datestr
    if re.match(r"^\d{2}-\d{2}$", datestr): return "2026-" + datestr
    return datestr

def clean_body(tool, body):
    ls = body.split("\n")
    if ls and (re.match(r"^(\[\d{2}\]|【.*\d{3}】|\[\d+/\d+\]|\[(?:周[一二三四五六日天])?\d{3}\])\s", ls[0])
               or re.match(r"^(?!\[)\S.*\bvs\b.*FID=\d+", ls[0])):
        ls = ls[1:]
    ls = [x for x in ls if not re.match(r"^[═=\-]{5,}$", x)]
    body = "\n".join(ls).strip("\n")
    if tool == "sameodds":
        body = transform_sameodds(body)
    if tool == "av_sameodds":
        body = transform_av_sameodds(body)
    return body

def main():
    if len(sys.argv) < 2:
        print("usage: make_docx.py 2026-09-03 [006-016]"); return
    date_s = parse_date(sys.argv[1])
    rng = None
    if len(sys.argv) > 2 and re.match(r'^\d{3}-\d{3}$', sys.argv[2]):
        a, b = sys.argv[2].split('-')
        rng = (int(a), int(b))

    tool_data = {}
    order_keys = []
    for tool in TOOL_ORDER:
        txt_path = os.path.join(OUT_DIR, f"{tool}_{date_s}.txt")
        # samepan 优先读补了欧赔的增强版 (enrich_samepan_odds.py 生成)
        if tool == "samepan":
            enhanced = os.path.join(OUT_DIR, f"samepan_odds_{date_s}.txt")
            if os.path.exists(enhanced):
                txt_path = enhanced
        if not os.path.exists(txt_path):
            print(f"[skip] {tool} txt missing")
            continue
        secs = split_sections(read_txt(txt_path), tool)
        d = {}
        for key, body in secs:
            if key:
                d[key] = body
        tool_data[tool] = d
        if not order_keys and tool in ("min", "4way"):
            for key, _b in secs:
                if key and key not in order_keys:
                    order_keys.append(key)
        print(f"[load] {tool}: {len(d)}")
    if not order_keys:
        order_keys = list(tool_data.get("merge", {}))
    if rng:
        lo, hi = rng
        # order_keys 顺序 = 场次 1..N（min/4way split 标题顺序）
        order_keys = [k for i, k in enumerate(order_keys, 1) if lo <= i <= hi]
        print(f"[range] 保留场次 {lo}-{hi}: {len(order_keys)} 场", file=sys.stderr)

    doc = Document()
    # 页面边距调小
    for sec in doc.sections:
        sec.top_margin = Cm(1.2); sec.bottom_margin = Cm(1.2)
        sec.left_margin = Cm(1.4); sec.right_margin = Cm(1.4)

    st = doc.styles["Normal"]
    st.font.name = "Microsoft YaHei"
    st.font.size = Pt(10)

    def add_title(text, size=16, color="1C2B4A", space_before=0, space_after=6, bold=True):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        r = p.add_run(text)
        r.bold = bold
        r.font.size = Pt(size)
        r.font.color.rgb = RGBColor.from_string(color)
        return p

    def add_body(text, size=10, color="222222", indent=0, space_after=2):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(0); pf.space_after = Pt(space_after)
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
        if indent:
            pf.left_indent = Cm(indent)
        r = p.add_run(text)
        r.font.size = Pt(size)
        r.font.color.rgb = RGBColor.from_string(color)
        return p

    add_title(f"⚽ {date_s} 竞彩4skill 按场次", 17, "1C2B4A")
    add_body("顺序: merge合成 → 4way四维 → min最小 → sameodds同赔 → av百家同赔 → samepan同盘", 9, "888888")

    for i, key in enumerate(order_keys, 1):
        add_title(f"{i}. {key}", 13, "FFFFFF", space_before=10, space_after=0)
        # 深色底纹标题
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), "1C2B4A")
        doc.paragraphs[-1]._p.get_or_add_pPr().append(shd)
        for tool in TOOL_ORDER:
            body = tool_data.get(tool, {}).get(key)
            if body is None:
                continue
            body = clean_body(tool, body)
            if not body:
                continue
            color = TOOL_COLORS[tool]
            add_body(f"■ {tool} {TOOL_CN.get(tool,'')}", 11, color, space_after=2)
            for ln in body.split("\n"):
                add_body(ln if ln else " ", 9.5, "222222")
    out_docx = os.path.join(OUT_DIR, f"mobile_{date_s}.docx")
    if rng:
        out_docx = os.path.join(OUT_DIR, f"mobile_{date_s}_{rng[0]:03d}-{rng[1]:03d}.docx")
    doc.save(out_docx)
    print(f"[docx] {out_docx} {os.path.getsize(out_docx)} bytes, {len(order_keys)} matches")

if __name__ == "__main__":
    main()
