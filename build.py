#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — 由中间 JSON 生成 AI native HTML 幻灯片。

用法：
    /usr/bin/python3 build.py            # 生成全部三讲 + index.html
    /usr/bin/python3 build.py 1          # 只生成第 1 讲

输入：data/lectureN.json（extract.py 生成）
输出：lectureN.html、index.html（均引用共享 css/slides.css、js/slides.js，
      全部相对路径，file:// 直接打开可用；幻灯片数据已静态内联为 HTML，无 fetch）。

版式自动判定：
    cover     第 1 页
    section   文字极少（无图且 bullets 总字符 ≤40）
    fullimg   整页大图（有图、几乎无文字）
    gallery   ≥4 张图
    imgtext   1–3 张图 + 文字（侧栏或上下布局）
    text      纯文字 / 含表格
"""
import sys
import os
import json
import html
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
EMU_PER_PX = 9525  # 96dpi 下 1px = 9525 EMU，仅用于宽高比/相对位置推断

MONO_RE = re.compile(
    r"(\bdef |\bimport |\bclass |\breturn\b|->|=>|torch\.|np\.|\.backward\(\)|"
    r"\bfor .+ in |print\(|\w+\(\w*\)=|layer\d|W\d|softmax|ReLU\b)")


def esc(s):
    return html.escape(s or "", quote=True)


def bullet_chars(slide):
    n = sum(len(b["text"]) for b in slide["bullets"])
    for t in slide["tables"]:
        for row in t:
            n += sum(len(c) for c in row)
    return n


def classify(slide, slide_count):
    n_img = len(slide["images"])
    n_txt = bullet_chars(slide)
    n_bul = len(slide["bullets"])
    if slide["index"] == 1:
        return "cover"
    if n_img >= 1 and n_txt <= 6 and n_bul <= 1 and not slide["tables"] \
            and not slide["title"]:
        return "fullimg"
    if n_img >= 4:
        return "gallery"
    if n_img == 0 and n_txt <= 40 and slide["title"]:
        return "section"
    if n_img >= 1 and (n_bul or slide["tables"]):
        return "imgtext"
    if n_img >= 1:
        return "fullimg" if not slide["title"] else "imgtext"
    return "text"


def fs_class(slide):
    n = bullet_chars(slide)
    if n > 900:
        return "fs-s"
    if n > 550:
        return "fs-m"
    if n > 280:
        return "fs-l"
    return ""


def sorted_images(slide):
    """按原始版面位置排序（先上后下、先左后右），保持布局意图。"""
    return sorted(slide["images"], key=lambda im: (im["top"], im["left"]))


def flat(s):
    """渲染前压缩内部换行/多余空白为单空格。"""
    return re.sub(r"\s+", " ", s or "").strip()


def render_bullets(bullets, cap=None):
    items = bullets if cap is None else bullets[:cap]
    out = ['<ul class="bullets">']
    for b in items:
        lv = min(max(b["level"], 0), 2)
        cls = "lv%d" % lv if lv else ""
        if MONO_RE.search(b["text"]):
            cls = (cls + " mono").strip()
        out.append('<li class="%s">%s</li>' % (cls, esc(flat(b["text"]))))
    out.append("</ul>")
    return "\n".join(out)


def render_tables(tables, max_rows=10):
    out = []
    for t in tables:
        out.append('<table class="tbl">')
        for row in t[:max_rows]:
            cells = "".join("<td>%s</td>" % esc(flat(c)) for c in row)
            out.append("<tr>%s</tr>" % cells)
        out.append("</table>")
        if len(t) > max_rows:
            out.append('<p class="tbl-more">… 共 %d 行</p>' % len(t))
    return "\n".join(out)


def render_figures(images, cols_cls=""):
    figs = []
    for im in images:
        w, h = im["width"], im["height"]
        style = ""
        if w and h:
            style = ' style="aspect-ratio:%d/%d"' % (w, h)
        figs.append("<figure%s><img src=\"%s\" alt=\"\" loading=\"lazy\"></figure>"
                    % (style, esc(im["path"])))
    return '<div class="img-grid %s">%s</div>' % (cols_cls, "\n".join(figs))


def render_slide(slide, doc):
    layout = classify(slide, doc["slide_count"])
    title = esc(slide["title"])
    fs = fs_class(slide)
    cls = "slide layout-%s %s" % (layout, fs)
    body = []

    if layout == "cover":
        subs = [b["text"] for b in slide["bullets"]]
        body.append('<div class="cover-kicker">DEEP LEARNING &amp; COMPUTER VISION</div>')
        body.append('<h1 class="cover-title">%s</h1>' % (title or esc(doc["name"])))
        if subs:
            body.append('<div class="cover-sub">%s</div>'
                        % "<br>".join(esc(s) for s in subs[:4]))
        body.append('<div class="cover-badge">第 %d 讲 · 共 %d 页</div>'
                    % (doc["lecture"], doc["slide_count"]))

    elif layout == "section":
        m = re.match(r"^(\d+)[\.、\s]*(.*)$", slide["title"])
        if m:
            body.append('<div class="section-no">%s</div>' % esc(m.group(1)))
            body.append('<h1 class="section-title">%s</h1>' % esc(m.group(2) or slide["title"]))
        else:
            body.append('<div class="section-no">§</div>')
            body.append('<h1 class="section-title">%s</h1>' % title)
        subs = [b["text"] for b in slide["bullets"] if b["text"] != slide["title"]]
        if subs:
            body.append('<div class="section-sub">%s</div>' % esc(" · ".join(subs[:3])))

    elif layout == "fullimg":
        imgs = sorted_images(slide)
        body.append(render_figures(imgs, "single"))

    elif layout == "gallery":
        if title:
            body.append('<h2 class="slide-title">%s</h2>' % title)
        body.append('<div class="gallery-grid">')
        for im in sorted_images(slide):
            body.append('<img src="%s" alt="" loading="lazy">' % esc(im["path"]))
        body.append("</div>")
        txts = [b["text"] for b in slide["bullets"]]
        if txts or slide["tables"]:
            note = "；".join(flat(t) for t in txts)
            if slide["tables"]:
                note += ("；" if note else "") + render_tables_text(slide["tables"])
            body.append('<div class="gallery-note">%s</div>' % esc(note))

    elif layout == "imgtext":
        if title:
            body.append('<h2 class="slide-title">%s</h2>' % title)
        imgs = sorted_images(slide)
        n = len(imgs)
        cols = "single" if n == 1 else ("cols-2" if n == 2 else "cols-3")
        text_html = render_bullets(slide["bullets"])
        if slide["tables"]:
            text_html += render_tables(slide["tables"])
        # 文字多则图在上文在下；文字少侧栏
        below = bullet_chars(slide) > 200 or len(slide["bullets"]) > 5
        body.append('<div class="imgtext-body">')
        body.append('<div class="img-zone">%s</div>' % render_figures(imgs, cols))
        if text_html.strip():
            body.append('<div class="side-bullets">%s</div>' % text_html)
        body.append("</div>")
        if below:
            # 通过额外 class 切换为上下布局
            cls += " img-below"

    else:  # text
        if title:
            body.append('<h2 class="slide-title">%s</h2>' % title)
        body.append(render_bullets(slide["bullets"]))
        if slide["tables"]:
            body.append(render_tables(slide["tables"]))

    if slide["notes"]:
        body.append('<aside class="notes-hint">%s</aside>' % esc(slide["notes"]))

    return '<section class="%s" data-index="%d">\n%s\n</section>' % (
        cls.strip(), slide["index"], "\n".join(body))


def render_tables_text(tables):
    parts = []
    for t in tables:
        for row in t:
            parts.append(" | ".join(flat(c) for c in row if flat(c)))
    return "；".join(p for p in parts if p)


PAGE_TMPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>第{num}讲 · {name} — 深度学习与计算机视觉</title>
<link rel="stylesheet" href="css/slides.css">
</head>
<body>
<div id="viewport">
  <div id="stage">
{slides}
  </div>
</div>
<div id="progress"></div>
<div id="pager"></div>
<div id="hint">←/→ 翻页 · O 总览 · F 全屏</div>
<script src="js/slides.js"></script>
</body>
</html>
"""


def build_lecture(num):
    path = os.path.join(ROOT, "data", "lecture%d.json" % num)
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    sections = [render_slide(s, doc) for s in doc["slides"]]
    page = PAGE_TMPL.replace("{num}", str(num)) \
                    .replace("{name}", esc(doc["name"])) \
                    .replace("{slides}", "\n".join(sections))
    out = os.path.join(ROOT, "lecture%d.html" % num)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)

    # 版式统计
    from collections import Counter
    stats = Counter(classify(s, doc["slide_count"]) for s in doc["slides"])
    print("lecture%d.html: %d 页, 版式 %s"
          % (num, doc["slide_count"], dict(stats)))
    return doc


INDEX_TMPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>深度学习与计算机视觉 · 课程幻灯片</title>
<link rel="stylesheet" href="css/slides.css">
<style>
  body {{ overflow: auto; }}
  .home {{ max-width: 1080px; margin: 0 auto; padding: 72px 32px 96px; }}
  .home-kicker {{ color: var(--accent); letter-spacing: .4em; font-size: 14px; margin-bottom: 16px; }}
  .home h1 {{ font-size: 44px; font-weight: 800; color: #fff; margin-bottom: 10px; }}
  .home .sub {{ color: var(--muted); font-size: 17px; margin-bottom: 48px; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; }}
  .card {{
    display: block; text-decoration: none; color: var(--text);
    background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
    overflow: hidden; transition: transform .2s ease, border-color .2s ease;
  }}
  .card:hover {{ transform: translateY(-4px); border-color: var(--accent); }}
  .card .thumb {{ height: 170px; display: flex; align-items: center; justify-content: center;
    background: radial-gradient(400px 200px at 50% 0%, rgba(56,200,240,.12), transparent); }}
  .card .thumb img {{ max-width: 92%; max-height: 150px; object-fit: contain; border-radius: 6px; }}
  .card .thumb .noimg {{ font-size: 40px; color: var(--accent); font-weight: 800; }}
  .card .meta {{ padding: 18px 22px 22px; }}
  .card .no {{ font-family: var(--font-mono); font-size: 12px; color: var(--accent); letter-spacing: .2em; }}
  .card .name {{ font-size: 20px; font-weight: 700; color: #fff; margin: 8px 0 6px; }}
  .card .cnt {{ font-size: 13px; color: var(--muted); }}
</style>
</head>
<body>
<div class="home">
  <div class="home-kicker">DEEP LEARNING &amp; COMPUTER VISION</div>
  <h1>深度学习与计算机视觉</h1>
  <div class="sub">王兴刚 · 华中科技大学 · AI native 幻灯片（←/→ 翻页，O 总览，F 全屏）</div>
  <div class="cards">
{cards}
  </div>
</div>
</body>
</html>
"""

CARD_TMPL = """    <a class="card" href="lecture{num}.html">
      <div class="thumb">{thumb}</div>
      <div class="meta">
        <div class="no">LECTURE {num:02d}</div>
        <div class="name">{name}</div>
        <div class="cnt">{count} 页 · {imgs} 张图</div>
      </div>
    </a>"""


def first_image(doc):
    for s in doc["slides"]:
        if s["images"]:
            return s["images"][0]["path"]
    return None


def build_index(docs):
    cards = []
    for doc in docs:
        img = first_image(doc)
        thumb = ('<img src="%s" alt="">' % esc(img)) if img \
            else '<div class="noimg">∇</div>'
        cards.append(CARD_TMPL.format(
            num=doc["lecture"], name=esc(doc["name"]),
            count=doc["slide_count"], imgs=doc["image_count"], thumb=thumb))
    page = INDEX_TMPL.replace("{cards}", "\n".join(cards))
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print("index.html 已生成")


def main():
    nums = [int(a) for a in sys.argv[1:]] or [1, 2, 3]
    docs = [build_lecture(n) for n in nums]
    if len(nums) == 3 or not nums:
        build_index(docs)
    elif len(nums) > 1:
        build_index(docs)


if __name__ == "__main__":
    main()
