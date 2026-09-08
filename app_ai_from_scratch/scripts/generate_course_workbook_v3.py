#!/usr/bin/env python3
"""Generate the AIFromScratch bilingual workbook using the platform identity."""

from __future__ import annotations

import base64
import html
import re
import zipfile
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from generate_course_workbook import TOPICS


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ASSETS = ROOT / "output" / "workbook-v2" / "assets"
OUT = ROOT / "output" / "workbook-v3"
ASSETS = OUT / "assets"
PDFS = OUT / "pdf"
CANVA = OUT / "canva"
PAGE_W, PAGE_H = 960, 540

# Canonical tokens from web/src/lib/theme-css.ts and design/conito/Main.dc.html.
BLACK = "#000000"
PANEL = "#0B0B0C"
PAPER = "#F2F2F2"
WHITE = "#FFFFFF"
INK = "#000000"
BLUE = "#0A84FF"
BLUE_PAPER = "#0A5AD6"
GREEN = "#30D158"
ORANGE = "#FF9F0A"
RED = "#FF453A"
YELLOW = "#FFD60A"
LIGHT_2 = "#B8B8BE"
LIGHT_3 = "#8E8E93"
HAIR_DARK = "#3A3A3C"
HAIR_LIGHT = "#C7C7CC"


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("UI", "/System/Library/Fonts/Supplemental/Arial.ttf"))
    pdfmetrics.registerFont(TTFont("UIBold", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"))
    pdfmetrics.registerFont(TTFont("UIBlack", "/System/Library/Fonts/Supplemental/Arial Black.ttf"))
    pdfmetrics.registerFont(TTFont("Mono", "/System/Library/Fonts/Supplemental/Courier New.ttf"))
    pdfmetrics.registerFont(TTFont("MonoBold", "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"))


register_fonts()


def C(value: str):
    return HexColor(value)


def clean(value: str) -> str:
    return value.replace("—", "-").replace("–", "-")


def wrap(value: str, font: str, size: float, width: float) -> list[str]:
    output: list[str] = []
    for paragraph in clean(value).split("\n"):
        current = ""
        for word in paragraph.split():
            trial = f"{current} {word}".strip()
            if current and pdfmetrics.stringWidth(trial, font, size) > width:
                output.append(current)
                current = word
            else:
                current = trial
        output.append(current)
    return output


def draw_text(c: canvas.Canvas, value: str, x: float, y: float, width: float, *,
              font: str = "UI", size: float = 18, leading: float | None = None,
              fill: str = INK, max_lines: int | None = None) -> float:
    leading = leading or size * 1.22
    output = wrap(value, font, size, width)
    if max_lines and len(output) > max_lines:
        output = output[:max_lines]
        output[-1] = output[-1].rstrip(".,;:") + "..."
    c.setFont(font, size)
    c.setFillColor(C(fill))
    for line in output:
        c.drawString(x, y, line)
        y -= leading
    return y


def brand_mark(c: canvas.Canvas, x: float, y: float, *, inverse: bool = False) -> None:
    bg, fg, stroke = (WHITE, BLACK, WHITE) if inverse else (BLACK, WHITE, BLACK)
    c.setFillColor(C(bg)); c.setStrokeColor(C(stroke)); c.setLineWidth(1)
    c.rect(x, y, 36, 36, fill=1, stroke=1)
    c.setFont("UIBold", 17); c.setFillColor(C(fg))
    c.drawCentredString(x + 18, y + 11, "IA")


def label(c: canvas.Canvas, value: str, x: float, y: float, *, color: str = BLUE, inverse: bool = False) -> None:
    c.setFont("MonoBold", 10); c.setFillColor(C(color))
    c.drawString(x, y, value.upper())
    c.setStrokeColor(C(WHITE if inverse else INK)); c.setLineWidth(.6)
    c.line(x, y - 7, x + 72, y - 7)


def place_image(c: canvas.Canvas, path: Path, x: float, y: float, w: float, h: float,
                *, stroke: str = BLUE, line: float = 1) -> None:
    c.drawImage(ImageReader(str(path)), x, y, w, h, preserveAspectRatio=False, mask="auto")
    c.setStrokeColor(C(stroke)); c.setLineWidth(line)
    c.rect(x, y, w, h, fill=0, stroke=1)


def footer(c: canvas.Canvas, topic_no: int | None, page_no: int, total: int, *, inverse: bool = False) -> None:
    fg = LIGHT_2 if inverse else "#66666B"
    hair = HAIR_DARK if inverse else HAIR_LIGHT
    c.setStrokeColor(C(hair)); c.setLineWidth(.5); c.line(32, 31, PAGE_W - 32, 31)
    c.setFont("MonoBold", 8); c.setFillColor(C(fg))
    left = f"AI FROM SCRATCH / TOPIC {topic_no:02d}" if topic_no else "AI FROM SCRATCH / BILINGUAL WORKBOOK"
    c.drawString(32, 16, left); c.drawRightString(PAGE_W - 32, 16, f"{page_no:02d}/{total:02d}")


def cover(c: canvas.Canvas, total: int) -> None:
    c.setFillColor(C(BLACK)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    brand_mark(c, 42, 457, inverse=True)
    c.setFont("MonoBold", 10); c.setFillColor(C(BLUE)); c.drawString(92, 474, "COURSE FIELD GUIDE / 2026")
    c.setFont("UIBlack", 56); c.setFillColor(C(WHITE)); c.drawString(42, 366, "AI From")
    c.drawString(42, 312, "Scratch")
    c.setFont("UIBold", 28); c.setFillColor(C(BLUE)); c.drawString(45, 268, "IA desde cero")
    draw_text(c, "12 visual lessons to understand and use artificial intelligence.", 45, 224, 430,
              font="UIBold", size=18, leading=22, fill=WHITE, max_lines=3)
    draw_text(c, "12 lecciones visuales para entender y usar la inteligencia artificial.", 45, 152, 430,
              size=15, leading=19, fill=LIGHT_2, max_lines=3)
    c.setStrokeColor(C(BLUE)); c.setLineWidth(2); c.line(45, 88, 456, 88)
    c.setFont("Mono", 10); c.setFillColor(C(LIGHT_3)); c.drawString(45, 65, "CONCEPTS / EXAMPLES / PRACTICE / ES + EN")
    for i, (x, y, w, h) in enumerate(((532, 273, 178, 181), (718, 273, 196, 181), (532, 66, 382, 199)), start=1):
        place_image(c, ASSETS / f"topic-{i:02d}.jpg", x, y, w, h, stroke=BLUE, line=1)
    footer(c, None, 1, total, inverse=True); c.showPage()


def opener(c: canvas.Canvas, topic: dict, no: int, page_no: int, total: int) -> None:
    c.setFillColor(C(BLACK)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    brand_mark(c, 36, 466, inverse=True)
    c.setFont("MonoBold", 10); c.setFillColor(C(BLUE)); c.drawString(88, 482, f"TOPIC {no:02d} / INTRO")
    c.setFont("UIBlack", 94); c.setFillColor(C(PANEL)); c.drawRightString(490, 411, f"{no:02d}")
    draw_text(c, topic["title_es"], 42, 389, 420, font="UIBlack", size=38, leading=42, fill=WHITE, max_lines=2)
    draw_text(c, topic["title_en"], 43, 288, 410, font="UIBold", size=20, leading=24, fill=BLUE, max_lines=2)
    c.setStrokeColor(C(HAIR_DARK)); c.setLineWidth(1); c.line(43, 242, 456, 242)
    label(c, "objetivo / objective", 43, 217, inverse=True)
    draw_text(c, topic["objective_es"], 43, 183, 398, font="UIBold", size=13, leading=17, fill=WHITE, max_lines=3)
    draw_text(c, topic["objective_en"], 43, 116, 398, size=11, leading=15, fill=LIGHT_2, max_lines=3)
    place_image(c, ASSETS / f"topic-{no:02d}.jpg", 502, 49, 416, 441, stroke=BLUE, line=1)
    c.setFillColor(C(YELLOW)); c.circle(902, 474, 5, fill=1, stroke=0)
    footer(c, no, page_no, total, inverse=True); c.showPage()


def mechanism(c: canvas.Canvas, topic: dict, no: int, page_no: int, total: int) -> None:
    c.setFillColor(C(PAPER)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    brand_mark(c, 36, 466)
    c.setFont("MonoBold", 10); c.setFillColor(C(BLUE_PAPER)); c.drawString(88, 482, f"TOPIC {no:02d} / MECHANISM")
    place_image(c, ASSETS / f"topic-{no:02d}.jpg", 36, 76, 344, 368, stroke=INK, line=1)
    c.setFont("UIBlack", 32); c.setFillColor(C(INK)); c.drawString(422, 437, "Cómo funciona")
    c.setFont("UIBold", 17); c.setFillColor(C(BLUE_PAPER)); c.drawString(423, 406, "How it works")
    draw_text(c, topic["mechanism_es"], 423, 365, 493, size=14, leading=18, max_lines=5)
    draw_text(c, topic["mechanism_en"], 423, 277, 493, size=11, leading=14, fill="#66666B", max_lines=5)
    c.setStrokeColor(C(INK)); c.setLineWidth(1); c.line(423, 198, 915, 198)
    for i, (es, en) in enumerate(zip(topic["steps_es"], topic["steps_en"])):
        x = 423 + i * 123
        c.setFillColor(C(BLUE_PAPER if i == 0 else INK)); c.rect(x, 159, 26, 26, fill=1, stroke=0)
        c.setFont("MonoBold", 10); c.setFillColor(C(WHITE)); c.drawCentredString(x + 13, 168, str(i + 1))
        draw_text(c, es, x, 140, 110, font="UIBold", size=10, leading=12, max_lines=3)
        draw_text(c, en, x, 94, 110, size=8.5, leading=10, fill="#66666B", max_lines=3)
    footer(c, no, page_no, total); c.showPage()


def analogy(c: canvas.Canvas, topic: dict, no: int, page_no: int, total: int) -> None:
    c.setFillColor(C(BLACK)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    place_image(c, ASSETS / f"topic-{no:02d}.jpg", 0, 0, 480, PAGE_H, stroke=BLUE, line=1)
    c.setFillColor(C(PANEL)); c.rect(480, 0, 480, PAGE_H, fill=1, stroke=0)
    brand_mark(c, 514, 466, inverse=True)
    label(c, "analogía / analogy", 568, 482, inverse=True)
    draw_text(c, topic["analogy_es"], 518, 412, 398, font="UIBold", size=21, leading=26, fill=WHITE, max_lines=6)
    draw_text(c, topic["analogy_en"], 518, 263, 398, size=12, leading=16, fill=LIGHT_2, max_lines=6)
    c.setFillColor(C(BLACK)); c.setStrokeColor(C(HAIR_DARK)); c.setLineWidth(1)
    c.rect(518, 75, 398, 122, fill=1, stroke=1)
    c.setFont("MonoBold", 10); c.setFillColor(C(BLUE)); c.drawString(538, 173, "EXAMPLE / EJEMPLO")
    draw_text(c, topic["example_es"], 538, 145, 168, font="UIBold", size=10, leading=13, fill=WHITE, max_lines=6)
    draw_text(c, topic["example_en"], 726, 145, 168, size=9, leading=12, fill=LIGHT_2, max_lines=6)
    footer(c, no, page_no, total, inverse=True); c.showPage()


def practice(c: canvas.Canvas, topic: dict, no: int, page_no: int, total: int) -> None:
    c.setFillColor(C(PAPER)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    brand_mark(c, 36, 466)
    c.setFont("MonoBold", 10); c.setFillColor(C(BLUE_PAPER)); c.drawString(88, 482, f"TOPIC {no:02d} / PRACTICE")
    c.setFont("UIBlack", 32); c.setFillColor(C(INK)); c.drawString(42, 419, "Pruébalo")
    c.setFont("UIBold", 17); c.setFillColor(C(BLUE_PAPER)); c.drawString(43, 389, "Try it")
    place_image(c, ASSETS / f"topic-{no:02d}.jpg", 734, 355, 182, 112, stroke=INK, line=1)
    draw_text(c, topic["practice_es"], 42, 330, 650, font="UIBlack", size=28, leading=33, max_lines=4)
    draw_text(c, topic["practice_en"], 43, 207, 650, font="UIBold", size=15, leading=20, fill="#66666B", max_lines=4)
    c.setFillColor(C(WHITE)); c.setStrokeColor(C(BLUE_PAPER)); c.setLineWidth(2)
    c.rect(42, 61, 874, 112, fill=1, stroke=1)
    c.setFont("MonoBold", 10); c.setFillColor(C(GREEN)); c.drawString(62, 148, "ANSWER / RESPUESTA")
    draw_text(c, topic["answer_es"], 62, 119, 392, font="UIBold", size=12, leading=15, max_lines=4)
    draw_text(c, topic["answer_en"], 496, 119, 390, size=11, leading=14, fill="#66666B", max_lines=4)
    footer(c, no, page_no, total); c.showPage()


def build_pdf(path: Path, indexes: list[int], with_cover: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    total = len(indexes) * 4 + (1 if with_cover else 0)
    c = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    page_no = 1
    if with_cover:
        cover(c, total); page_no += 1
    for idx in indexes:
        topic, no = TOPICS[idx], idx + 1
        opener(c, topic, no, page_no, total); page_no += 1
        mechanism(c, topic, no, page_no, total); page_no += 1
        analogy(c, topic, no, page_no, total); page_no += 1
        practice(c, topic, no, page_no, total); page_no += 1
    c.save()


def data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def H(value: str) -> str:
    return html.escape(clean(value)).replace("\n", "<br>")


def html_page(content: str, label_text: str, page_no: int, total: int, topic_no: int | None, cls: str) -> str:
    topic_tag = f" / TOPIC {topic_no:02d}" if topic_no else " / BILINGUAL WORKBOOK"
    return (f'<section class="page {cls}" data-document-role="page" data-label="{html.escape(label_text)}">'
            f'{content}<footer><span>AI FROM SCRATCH{topic_tag}</span><span>{page_no:02d}/{total:02d}</span></footer></section>')


def mark(inverse: bool = False) -> str:
    return f'<div class="mark{" inverse" if inverse else ""}">IA</div>'


def topic_html(topic: dict, no: int, page_no: int, total: int) -> tuple[list[str], int]:
    output: list[str] = []
    p1 = f'''{mark(True)}<div class="meta">TOPIC {no:02d} / INTRO</div><div class="op-copy"><div class="ghost">{no:02d}</div><h1>{H(topic['title_es'])}</h1><h2>{H(topic['title_en'])}</h2><hr><b>OBJETIVO / OBJECTIVE</b><p>{H(topic['objective_es'])}</p><p class="en">{H(topic['objective_en'])}</p></div><div class="op-img art t{no}"></div><i class="eye"></i>'''
    output.append(html_page(p1, f"Topic {no} intro", page_no, total, no, "opener")); page_no += 1
    steps = "".join(f'<div class="node"><i>{i+1}</i><strong>{H(es)}</strong><span>{H(en)}</span></div>' for i, (es, en) in enumerate(zip(topic['steps_es'], topic['steps_en'])))
    p2 = f'''{mark()}<div class="meta">TOPIC {no:02d} / MECHANISM</div><div class="mech-img art t{no}"></div><main class="mech-copy"><h1>Cómo funciona</h1><h2>How it works</h2><p>{H(topic['mechanism_es'])}</p><p class="en">{H(topic['mechanism_en'])}</p><div class="process">{steps}</div></main>'''
    output.append(html_page(p2, f"Topic {no} mechanism", page_no, total, no, "mechanism")); page_no += 1
    p3 = f'''<div class="analogy-img art t{no}"></div><main class="analogy-copy">{mark(True)}<div class="meta">ANALOGÍA / ANALOGY</div><h1>{H(topic['analogy_es'])}</h1><p>{H(topic['analogy_en'])}</p><div class="example"><b>EXAMPLE / EJEMPLO</b><div><strong>{H(topic['example_es'])}</strong><span>{H(topic['example_en'])}</span></div></div></main>'''
    output.append(html_page(p3, f"Topic {no} analogy", page_no, total, no, "analogy-page")); page_no += 1
    p4 = f'''{mark()}<div class="meta">TOPIC {no:02d} / PRACTICE</div><h1 class="practice-title">Pruébalo</h1><h2 class="practice-sub">Try it</h2><div class="practice-img art t{no}"></div><div class="question"><h1>{H(topic['practice_es'])}</h1><p>{H(topic['practice_en'])}</p></div><div class="answer"><b>ANSWER / RESPUESTA</b><div><strong>{H(topic['answer_es'])}</strong><span>{H(topic['answer_en'])}</span></div></div>'''
    output.append(html_page(p4, f"Topic {no} practice", page_no, total, no, "practice-page")); page_no += 1
    return output, page_no


def build_html(path: Path, indexes: list[int], with_cover: bool) -> None:
    total = len(indexes) * 4 + (1 if with_cover else 0)
    pages: list[str] = []
    page_no = 1
    if with_cover:
        collage = "".join(f'<div class="art t{i}"></div>' for i in (1, 2, 3))
        content = f'''{mark(True)}<div class="cover-meta">COURSE FIELD GUIDE / 2026</div><div class="cover-copy"><h1>AI From<br>Scratch</h1><h2>IA desde cero</h2><p>12 visual lessons to understand and use artificial intelligence.</p><strong>12 lecciones visuales para entender y usar la inteligencia artificial.</strong><small>CONCEPTS / EXAMPLES / PRACTICE / ES + EN</small></div><div class="cover-collage">{collage}</div>'''
        pages.append(html_page(content, "Cover", page_no, total, None, "cover")); page_no += 1
    for idx in indexes:
        built, page_no = topic_html(TOPICS[idx], idx + 1, page_no, total)
        pages.extend(built)
    needed = {1, 2, 3} if with_cover else set()
    needed.update(idx + 1 for idx in indexes)
    asset_rules = "".join(f'.t{i}{{background-image:url("{data_uri(ASSETS / f"topic-{i:02d}.jpg")}")}}' for i in sorted(needed))
    css = '''*{box-sizing:border-box}body{margin:0;background:#5a5a5d;font-family:Arial,Helvetica,sans-serif;color:#000}.page{position:relative;width:960px;height:540px;margin:24px auto;background:#F2F2F2;overflow:hidden;page-break-after:always}.page footer{position:absolute;left:32px;right:32px;bottom:14px;padding-top:7px;border-top:1px solid #C7C7CC;display:flex;justify-content:space-between;font:700 8px "Courier New",monospace;color:#66666B}.art{background-size:cover;background-position:center}.mark{position:absolute;left:36px;top:38px;width:36px;height:36px;background:#000;color:#fff;border:1px solid #000;display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:700}.mark.inverse{background:#fff;color:#000;border-color:#fff}.meta,.cover-meta{position:absolute;left:88px;top:54px;color:#0A5AD6;font:700 10px "Courier New",monospace}.cover{background:#000;color:#fff}.cover .mark{top:45px;left:42px}.cover-meta{left:92px;top:60px;color:#0A84FF}.cover-copy{position:absolute;left:45px;top:118px;width:450px}.cover-copy h1{font-size:56px;line-height:.92;margin:0}.cover-copy h2{font-size:28px;color:#0A84FF;margin:14px 0 22px}.cover-copy p,.cover-copy strong{display:block;font-size:18px;line-height:1.25;margin:0 0 15px}.cover-copy strong{font-size:15px;color:#B8B8BE}.cover-copy small{display:block;border-top:2px solid #0A84FF;padding-top:14px;margin-top:18px;color:#8E8E93;font:10px "Courier New",monospace}.cover-collage .art{position:absolute;border:1px solid #0A84FF}.cover-collage .art:nth-child(1){left:532px;top:86px;width:178px;height:181px}.cover-collage .art:nth-child(2){left:718px;top:86px;width:196px;height:181px}.cover-collage .art:nth-child(3){left:532px;top:293px;width:382px;height:199px}.cover footer,.opener footer,.analogy-page footer{border-color:#3A3A3C;color:#B8B8BE}.opener{background:#000;color:#fff}.opener .meta{color:#0A84FF}.op-copy{position:absolute;left:43px;top:115px;width:420px}.ghost{position:absolute;right:0;top:-27px;color:#0B0B0C;font-size:94px;font-weight:900}.op-copy h1{position:relative;font-size:38px;line-height:1.05;margin:0 0 14px}.op-copy h2{font-size:20px;line-height:1.2;color:#0A84FF;margin:0 0 28px}.op-copy hr{border:0;border-top:1px solid #3A3A3C;margin:0 0 20px}.op-copy b{display:block;color:#0A84FF;font:700 10px "Courier New",monospace;margin-bottom:17px}.op-copy p{font-size:13px;line-height:1.3;margin:0 0 12px;max-width:398px}.op-copy .en{font-size:11px;color:#B8B8BE}.op-img{position:absolute;left:502px;top:50px;width:416px;height:441px;border:1px solid #0A84FF}.eye{position:absolute;right:52px;top:61px;width:10px;height:10px;background:#FFD60A;border-radius:50%}.mechanism .mech-img{position:absolute;left:36px;top:96px;width:344px;height:368px;border:1px solid #000}.mech-copy{position:absolute;left:423px;top:97px;width:493px}.mech-copy h1{font-size:32px;margin:0}.mech-copy h2{font-size:17px;color:#0A5AD6;margin:4px 0 22px}.mech-copy>p{font-size:14px;line-height:1.3;margin:0 0 12px}.mech-copy>.en{font-size:11px;color:#66666B}.process{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;margin-top:20px;padding-top:18px;border-top:1px solid #000}.node i{display:flex;width:26px;height:26px;align-items:center;justify-content:center;background:#000;color:#fff;font:700 10px "Courier New",monospace;font-style:normal}.node:first-child i{background:#0A5AD6}.node strong,.node span{display:block;margin-top:9px;font-size:10px;line-height:1.18}.node span{font-size:8.5px;color:#66666B}.analogy-img{position:absolute;inset:0 auto 0 0;width:480px;height:540px;border-right:1px solid #0A84FF}.analogy-copy{position:absolute;left:480px;top:0;width:480px;height:540px;background:#0B0B0C;color:#fff;padding:109px 44px}.analogy-copy .mark{top:38px;left:34px}.analogy-copy .meta{left:88px;top:54px;color:#0A84FF}.analogy-copy h1{font-size:21px;line-height:1.23;margin:0 0 22px}.analogy-copy>p{font-size:12px;line-height:1.3;color:#B8B8BE;margin:0}.example{position:absolute;left:38px;right:44px;bottom:75px;height:122px;background:#000;border:1px solid #3A3A3C;padding:20px}.example>b{color:#0A84FF;font:700 10px "Courier New",monospace}.example>div{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:14px}.example strong,.example span{font-size:10px;line-height:1.25}.example span{font-size:9px;color:#B8B8BE}.practice-title{position:absolute;left:42px;top:104px;font-size:32px;margin:0}.practice-sub{position:absolute;left:43px;top:145px;font-size:17px;color:#0A5AD6;margin:0}.practice-img{position:absolute;right:44px;top:73px;width:182px;height:112px;border:1px solid #000}.question{position:absolute;left:42px;top:205px;width:650px}.question h1{font-size:28px;line-height:1.18;margin:0 0 20px}.question p{font-size:15px;line-height:1.28;color:#66666B;margin:0}.answer{position:absolute;left:42px;right:44px;bottom:61px;height:112px;background:#fff;border:2px solid #0A5AD6;padding:20px}.answer>b{color:#30D158;font:700 10px "Courier New",monospace}.answer>div{display:grid;grid-template-columns:1fr 1fr;gap:42px;margin-top:14px}.answer strong,.answer span{font-size:11px;line-height:1.25}.answer span{font-weight:400;color:#66666B}@media print{body{background:#fff}.page{margin:0}}''' + asset_rules
    document = f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>AI From Scratch Platform Identity Workbook</title><style>{css}</style></head><body>{"".join(pages)}</body></html>'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")


def slug(topic: dict, idx: int) -> str:
    return f"{idx + 1:02d}_{re.sub(r'[^a-z0-9]+', '_', topic['title_en'].lower()).strip('_')}"


def prepare_assets() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for idx in range(1, 13):
        source = SOURCE_ASSETS / f"topic-{idx:02d}.jpg"
        target = ASSETS / source.name
        with Image.open(source) as img:
            gray = ImageOps.grayscale(img.convert("RGB"))
            gray = ImageEnhance.Contrast(gray).enhance(1.15)
            branded = ImageOps.colorize(gray, black=BLACK, mid=BLUE, white=PAPER, midpoint=138)
            branded.save(target, "JPEG", quality=84, optimize=True, progressive=True)


def build_zip() -> None:
    zip_path = OUT / "AIFromScratch_V3_All_PDFs.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for pdf in sorted(PDFS.glob("*.pdf")):
            archive.write(pdf, arcname=pdf.name)


def main() -> None:
    prepare_assets()
    PDFS.mkdir(parents=True, exist_ok=True); CANVA.mkdir(parents=True, exist_ok=True)
    all_indexes = list(range(12))
    build_pdf(PDFS / "AIFromScratch_Platform_Identity_Bilingual_Workbook_V3.pdf", all_indexes, True)
    build_html(CANVA / "AIFromScratch_Platform_Identity_Bilingual_Workbook_V3.html", all_indexes, True)
    for idx, topic in enumerate(TOPICS):
        name = slug(topic, idx)
        build_pdf(PDFS / f"AIFromScratch_V3_{name}.pdf", [idx], False)
        build_html(CANVA / f"AIFromScratch_V3_{name}.html", [idx], False)
    build_zip()
    print("Generated the platform-identity V3 master and twelve topic editions.")


if __name__ == "__main__":
    main()
