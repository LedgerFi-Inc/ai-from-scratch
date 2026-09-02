#!/usr/bin/env python3
"""Editorial redesign of the bilingual AIFromScratch workbook."""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from generate_course_workbook import TOPICS


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "workbook-v2"
ASSETS = OUT / "assets"
PDFS = OUT / "pdf"
CANVA = OUT / "canva"
PAGE_W, PAGE_H = 960, 540

INK = "#171714"
PAPER = "#F4F0E8"
CORAL = "#E7654E"
MINT = "#A9C7B8"
BLUE = "#B8CBD3"
WHITE = "#FFFDF7"
SOFT = "#DDD7CB"
MUTED = "#68655F"


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("Editorial", "/System/Library/Fonts/Supplemental/Arial.ttf"))
    pdfmetrics.registerFont(TTFont("EditorialBold", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"))
    pdfmetrics.registerFont(TTFont("EditorialBlack", "/System/Library/Fonts/Supplemental/Arial Black.ttf"))


register_fonts()


def C(value: str):
    return HexColor(value)


def clean(value: str) -> str:
    return value.replace("—", "-").replace("–", "-")


def lines(text: str, font: str, size: float, width: float) -> list[str]:
    result: list[str] = []
    for paragraph in clean(text).split("\n"):
        current = ""
        for word in paragraph.split():
            trial = f"{current} {word}".strip()
            if current and pdfmetrics.stringWidth(trial, font, size) > width:
                result.append(current)
                current = word
            else:
                current = trial
        result.append(current)
    return result


def text(c: canvas.Canvas, value: str, x: float, y: float, width: float, *,
         font: str = "Editorial", size: float = 18, leading: float | None = None,
         fill: str = INK, max_lines: int | None = None) -> float:
    leading = leading or size * 1.22
    wrapped = lines(value, font, size, width)
    if max_lines and len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines]
        wrapped[-1] = wrapped[-1].rstrip(".,;:") + "..."
    c.setFont(font, size)
    c.setFillColor(C(fill))
    for line in wrapped:
        c.drawString(x, y, line)
        y -= leading
    return y


def pill(c: canvas.Canvas, label: str, x: float, y: float, w: float, fill: str, fg: str = INK) -> None:
    c.setFillColor(C(fill))
    c.roundRect(x, y, w, 28, 14, fill=1, stroke=0)
    c.setFont("EditorialBold", 10)
    c.setFillColor(C(fg))
    c.drawCentredString(x + w / 2, y + 9, label)


def image(c: canvas.Canvas, path: Path, x: float, y: float, w: float, h: float, radius: float = 0) -> None:
    c.saveState()
    if radius:
        p = c.beginPath()
        p.roundRect(x, y, w, h, radius)
        c.clipPath(p, stroke=0, fill=0)
    c.drawImage(ImageReader(str(path)), x, y, w, h, preserveAspectRatio=False, mask="auto")
    c.restoreState()


def footer(c: canvas.Canvas, topic_no: int, page_no: int, total: int) -> None:
    c.setFont("EditorialBold", 9)
    c.setFillColor(C(MUTED))
    c.drawString(34, 22, f"AI FROM SCRATCH   TOPIC {topic_no:02d}")
    c.drawRightString(PAGE_W - 34, 22, f"{page_no}/{total}")


def cover(c: canvas.Canvas, total: int) -> None:
    c.setFillColor(C(PAPER)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(C(CORAL)); c.rect(0, 0, 18, PAGE_H, fill=1, stroke=0)
    c.setFont("EditorialBlack", 59); c.setFillColor(C(INK)); c.drawString(56, 410, "AI From")
    c.drawString(56, 350, "Scratch")
    c.setFont("EditorialBold", 26); c.setFillColor(C(CORAL)); c.drawString(60, 305, "IA desde cero")
    text(c, "12 visual lessons to understand and use AI", 60, 260, 360, size=18, max_lines=2)
    text(c, "12 lecciones visuales para entender y usar la IA", 60, 205, 360, font="EditorialBold", size=18, max_lines=2)
    c.setStrokeColor(C(INK)); c.setLineWidth(2); c.line(60, 150, 380, 150)
    text(c, "Concepts, examples and practice in English and Spanish.", 60, 128, 320, size=12, fill=MUTED, max_lines=2)
    positions = [(474, 218, 210, 250, -4), (666, 254, 238, 238, 5), (570, 34, 250, 230, 2)]
    for idx, (x, y, w, h, rot) in enumerate(positions):
        c.saveState(); c.translate(x + w/2, y + h/2); c.rotate(rot)
        c.setFillColor(C(INK)); c.roundRect(-w/2 - 7, -h/2 - 7, w + 14, h + 14, 10, fill=1, stroke=0)
        c.drawImage(ImageReader(str(ASSETS / f"topic-{idx + 1:02d}.jpg")), -w/2, -h/2, w, h, mask="auto")
        c.restoreState()
    c.setFont("EditorialBold", 9); c.setFillColor(C(MUTED)); c.drawString(60, 28, "BILINGUAL VISUAL WORKBOOK")
    c.drawRightString(PAGE_W - 34, 28, f"1/{total}")
    c.showPage()


def opener(c: canvas.Canvas, topic: dict, no: int, page_no: int, total: int) -> None:
    c.setFillColor(C(PAPER)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(C(CORAL)); c.rect(0, 0, 18, PAGE_H, fill=1, stroke=0)
    c.setFont("EditorialBlack", 94); c.setFillColor(C(SOFT)); c.drawString(46, 420, f"{no:02d}")
    text(c, topic["title_es"], 54, 341, 410, font="EditorialBlack", size=39, leading=42, max_lines=2)
    text(c, topic["title_en"], 56, 252, 395, font="EditorialBold", size=22, fill=CORAL, max_lines=2)
    c.setStrokeColor(C(INK)); c.setLineWidth(2); c.line(56, 202, 416, 202)
    pill(c, "OBJETIVO", 56, 154, 92, MINT)
    text(c, topic["objective_es"], 56, 132, 360, size=14, leading=18, max_lines=3)
    pill(c, "OBJECTIVE", 56, 70, 98, BLUE)
    text(c, topic["objective_en"], 56, 48, 360, size=12, leading=15, fill=MUTED, max_lines=2)
    image(c, ASSETS / f"topic-{no:02d}.jpg", 478, 48, 432, 444, 28)
    c.setStrokeColor(C(INK)); c.setLineWidth(3); c.roundRect(478, 48, 432, 444, 28, fill=0, stroke=1)
    footer(c, no, page_no, total); c.showPage()


def mechanism(c: canvas.Canvas, topic: dict, no: int, page_no: int, total: int) -> None:
    c.setFillColor(C(WHITE)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    image(c, ASSETS / f"topic-{no:02d}.jpg", 36, 88, 330, 408, 165)
    c.setStrokeColor(C(INK)); c.setLineWidth(3); c.roundRect(36, 88, 330, 408, 165, fill=0, stroke=1)
    c.setFont("EditorialBlack", 32); c.setFillColor(C(INK)); c.drawString(410, 458, "Cómo funciona")
    c.setFont("EditorialBold", 17); c.setFillColor(C(CORAL)); c.drawString(412, 425, "How it works")
    text(c, topic["mechanism_es"], 412, 382, 490, size=14, leading=18, max_lines=5)
    text(c, topic["mechanism_en"], 412, 286, 490, size=12, leading=15, fill=MUTED, max_lines=5)
    y = 202
    c.setStrokeColor(C(INK)); c.setLineWidth(2); c.line(424, y + 28, 882, y + 28)
    for i, (es, en) in enumerate(zip(topic["steps_es"], topic["steps_en"])):
        x = 420 + i * 118
        c.setFillColor(C(CORAL if i in (0, 3) else MINT)); c.circle(x + 18, y + 28, 16, fill=1, stroke=0)
        c.setFont("EditorialBold", 10); c.setFillColor(C(INK)); c.drawCentredString(x + 18, y + 24, str(i + 1))
        text(c, es, x, y - 2, 104, font="EditorialBold", size=11, leading=13, max_lines=3)
        text(c, en, x, y - 52, 104, size=9, leading=11, fill=MUTED, max_lines=3)
    footer(c, no, page_no, total); c.showPage()


def analogy(c: canvas.Canvas, topic: dict, no: int, page_no: int, total: int) -> None:
    c.setFillColor(C(PAPER)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    image(c, ASSETS / f"topic-{no:02d}.jpg", 0, 0, 500, PAGE_H)
    c.setFillColor(C(INK)); c.rect(464, 0, 496, PAGE_H, fill=1, stroke=0)
    pill(c, "ANALOGÍA", 516, 452, 102, CORAL, WHITE)
    text(c, topic["analogy_es"], 516, 406, 382, font="EditorialBold", size=22, leading=27, fill=WHITE, max_lines=6)
    text(c, topic["analogy_en"], 516, 254, 382, size=13, leading=17, fill=BLUE, max_lines=6)
    c.setFillColor(C(PAPER)); c.roundRect(516, 76, 382, 118, 0, fill=1, stroke=0)
    c.setFont("EditorialBlack", 13); c.setFillColor(C(CORAL)); c.drawString(536, 168, "EJEMPLO / EXAMPLE")
    text(c, topic["example_es"], 536, 142, 166, size=10, leading=13, max_lines=6)
    text(c, topic["example_en"], 724, 142, 154, size=9, leading=12, fill=MUTED, max_lines=6)
    c.setFont("EditorialBold", 9); c.setFillColor(C(BLUE)); c.drawString(516, 24, f"AI FROM SCRATCH   TOPIC {no:02d}")
    c.drawRightString(PAGE_W - 34, 24, f"{page_no}/{total}")
    c.showPage()


def practice(c: canvas.Canvas, topic: dict, no: int, page_no: int, total: int) -> None:
    c.setFillColor(C(INK)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(C(CORAL)); c.circle(86, 458, 39, fill=1, stroke=0)
    c.setFont("EditorialBlack", 24); c.setFillColor(C(WHITE)); c.drawCentredString(86, 450, f"{no:02d}")
    c.setFont("EditorialBlack", 32); c.setFillColor(C(WHITE)); c.drawString(144, 470, "Pruébalo")
    c.setFont("EditorialBold", 17); c.setFillColor(C(MINT)); c.drawString(146, 438, "Try it")
    image(c, ASSETS / f"topic-{no:02d}.jpg", 742, 350, 164, 164, 82)
    c.setStrokeColor(C(WHITE)); c.setLineWidth(3); c.roundRect(742, 350, 164, 164, 82, fill=0, stroke=1)
    text(c, topic["practice_es"], 58, 355, 620, font="EditorialBlack", size=31, leading=36, fill=WHITE, max_lines=4)
    text(c, topic["practice_en"], 60, 222, 620, font="EditorialBold", size=17, leading=21, fill=BLUE, max_lines=4)
    c.setFillColor(C(MINT)); c.rect(0, 42, PAGE_W, 132, fill=1, stroke=0)
    c.setFont("EditorialBlack", 13); c.setFillColor(C(INK)); c.drawString(58, 143, "RESPUESTA / ANSWER")
    text(c, topic["answer_es"], 58, 116, 400, font="EditorialBold", size=13, leading=16, max_lines=4)
    text(c, topic["answer_en"], 508, 116, 394, size=12, leading=15, max_lines=4)
    c.setFont("EditorialBold", 9); c.setFillColor(C(SOFT)); c.drawString(34, 20, f"AI FROM SCRATCH   TOPIC {no:02d}")
    c.drawRightString(PAGE_W - 34, 20, f"{page_no}/{total}")
    c.showPage()


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


def page(content: str, label: str, page_no: int, total: int, topic_no: int | None = None, cls: str = "") -> str:
    tag = f"AI FROM SCRATCH&nbsp;&nbsp; TOPIC {topic_no:02d}" if topic_no else "BILINGUAL VISUAL WORKBOOK"
    return f'<section class="page {cls}" data-document-role="page" data-label="{html.escape(label)}">{content}<footer><span>{tag}</span><span>{page_no}/{total}</span></footer></section>'


def topic_html(topic: dict, no: int, page_no: int, total: int) -> tuple[list[str], int]:
    result: list[str] = []
    p1 = f'''<div class="side"></div><div class="op-copy"><div class="ghost">{no:02d}</div><h1>{H(topic['title_es'])}</h1><h2>{H(topic['title_en'])}</h2><hr><b>OBJETIVO</b><p>{H(topic['objective_es'])}</p><b>OBJECTIVE</b><p class="en">{H(topic['objective_en'])}</p></div><div class="op-img art t{no}"></div>'''
    result.append(page(p1, f"Topic {no} opener", page_no, total, no, "opener")); page_no += 1
    process = "".join(f'<div class="node"><i>{i+1}</i><strong>{H(es)}</strong><span>{H(en)}</span></div>' for i,(es,en) in enumerate(zip(topic['steps_es'],topic['steps_en'])))
    p2 = f'''<div class="mech-img art t{no}"></div><main class="mech-copy"><h1>Cómo funciona</h1><h2>How it works</h2><p>{H(topic['mechanism_es'])}</p><p class="en">{H(topic['mechanism_en'])}</p><div class="process">{process}</div></main>'''
    result.append(page(p2, f"Topic {no} mechanism", page_no, total, no, "mechanism")); page_no += 1
    p3 = f'''<div class="analogy-img art t{no}"></div><main class="analogy-copy"><b>ANALOGÍA</b><h1>{H(topic['analogy_es'])}</h1><p>{H(topic['analogy_en'])}</p><div class="example"><strong>EJEMPLO / EXAMPLE</strong><div><span>{H(topic['example_es'])}</span><span>{H(topic['example_en'])}</span></div></div></main>'''
    result.append(page(p3, f"Topic {no} analogy", page_no, total, no, "analogy-page")); page_no += 1
    p4 = f'''<div class="practice-head"><i>{no:02d}</i><div><h1>Pruébalo</h1><h2>Try it</h2></div></div><div class="practice-img art t{no}"></div><div class="question"><h1>{H(topic['practice_es'])}</h1><p>{H(topic['practice_en'])}</p></div><div class="answer"><b>RESPUESTA / ANSWER</b><div><strong>{H(topic['answer_es'])}</strong><span>{H(topic['answer_en'])}</span></div></div>'''
    result.append(page(p4, f"Topic {no} practice", page_no, total, no, "practice-page")); page_no += 1
    return result, page_no


def build_html(path: Path, indexes: list[int], with_cover: bool) -> None:
    total = len(indexes) * 4 + (1 if with_cover else 0)
    pages: list[str] = []
    page_no = 1
    if with_cover:
        imgs = "".join(f'<div class="art t{i}"></div>' for i in (1,2,3))
        content = f'''<div class="cover-copy"><h1>AI From<br>Scratch</h1><h2>IA desde cero</h2><p>12 visual lessons to understand and use AI</p><strong>12 lecciones visuales para entender y usar la IA</strong></div><div class="cover-collage">{imgs}</div>'''
        pages.append(page(content, "Cover", page_no, total, cls="cover")); page_no += 1
    for idx in indexes:
        built, page_no = topic_html(TOPICS[idx], idx + 1, page_no, total)
        pages.extend(built)
    asset_rules = "".join(f'.t{i}{{background-image:url("{data_uri(ASSETS / f"topic-{i:02d}.jpg")}")}}' for i in range(1,13))
    css = '''*{box-sizing:border-box}body{margin:0;background:#cfc8bc;font-family:Arial,Helvetica,sans-serif;color:#171714}.page{position:relative;width:960px;height:540px;margin:24px auto;background:#F4F0E8;overflow:hidden;page-break-after:always}.page footer{position:absolute;left:34px;right:34px;bottom:18px;display:flex;justify-content:space-between;font-size:9px;font-weight:700;color:#68655F}.art{background-size:cover;background-position:center}.cover{border-left:18px solid #E7654E}.cover-copy{position:absolute;left:42px;top:62px;width:390px}.cover h1{font-size:59px;line-height:.96;margin:0}.cover h2{font-size:26px;color:#E7654E;margin:26px 0}.cover p,.cover strong{display:block;font-size:18px;max-width:340px;line-height:1.35;margin:0 0 18px}.cover-collage .art{position:absolute;width:220px;height:250px;border:7px solid #171714;border-radius:12px}.cover-collage .art:nth-child(1){left:470px;top:50px;transform:rotate(-4deg)}.cover-collage .art:nth-child(2){left:675px;top:78px;transform:rotate(5deg)}.cover-collage .art:nth-child(3){left:574px;top:270px;transform:rotate(2deg)}.opener{border-left:18px solid #E7654E}.op-copy{position:absolute;left:38px;top:52px;width:420px}.ghost{font-size:94px;font-weight:900;color:#DDD7CB;line-height:1}.op-copy h1{font-size:39px;line-height:1.05;margin:-8px 0 8px}.op-copy h2{font-size:22px;color:#E7654E;margin:0 0 28px}.op-copy hr{border:0;border-top:2px solid #171714;margin:0 0 18px}.op-copy b{display:inline-block;background:#A9C7B8;border-radius:20px;padding:7px 13px;font-size:10px;margin:0 0 8px}.op-copy p{font-size:14px;line-height:1.3;margin:0 0 10px;max-width:360px}.op-copy .en{font-size:12px;color:#68655F}.op-img{position:absolute;left:478px;top:48px;width:432px;height:444px;border:3px solid #171714;border-radius:28px}.mechanism{background:#FFFDF7}.mech-img{position:absolute;left:36px;top:48px;width:330px;height:448px;border:3px solid #171714;border-radius:165px}.mech-copy{position:absolute;left:410px;top:48px;width:500px}.mech-copy h1{font-size:32px;margin:0}.mech-copy h2{font-size:17px;color:#E7654E;margin:4px 0 22px}.mech-copy>p{font-size:14px;line-height:1.3;margin:0 0 12px}.mech-copy>.en{font-size:12px;color:#68655F}.process{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:24px;padding-top:24px;border-top:2px solid #171714}.node i{display:flex;width:32px;height:32px;align-items:center;justify-content:center;border-radius:50%;background:#A9C7B8;font-style:normal;font-weight:700}.node:first-child i,.node:last-child i{background:#E7654E}.node strong,.node span{display:block;margin-top:10px;font-size:11px;line-height:1.2}.node span{font-size:9px;color:#68655F}.analogy-img{position:absolute;inset:0 auto 0 0;width:500px;height:540px}.analogy-copy{position:absolute;left:464px;top:0;width:496px;height:540px;background:#171714;color:#FFFDF7;padding:46px 52px}.analogy-copy>b{display:inline-block;background:#E7654E;padding:8px 14px;font-size:10px}.analogy-copy h1{font-size:22px;line-height:1.22;margin:22px 0}.analogy-copy>p{font-size:13px;line-height:1.3;color:#B8CBD3;margin:0}.example{position:absolute;left:52px;right:62px;bottom:70px;background:#F4F0E8;color:#171714;padding:18px 20px}.example>strong{font-size:12px;color:#E7654E}.example>div{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:12px}.example span{font-size:10px;line-height:1.25}.practice-page{background:#171714;color:#FFFDF7}.practice-head{position:absolute;left:48px;top:34px;display:flex;gap:20px;align-items:center}.practice-head i{display:flex;width:78px;height:78px;align-items:center;justify-content:center;border-radius:50%;background:#E7654E;font-size:24px;font-weight:900;font-style:normal}.practice-head h1{font-size:32px;margin:0}.practice-head h2{font-size:17px;color:#A9C7B8;margin:4px 0}.practice-img{position:absolute;right:54px;top:34px;width:164px;height:164px;border:3px solid #FFFDF7;border-radius:50%}.question{position:absolute;left:58px;top:178px;width:650px}.question h1{font-size:31px;line-height:1.15;margin:0 0 18px}.question p{font-size:17px;line-height:1.25;color:#B8CBD3;margin:0}.answer{position:absolute;left:0;right:0;bottom:42px;height:132px;background:#A9C7B8;color:#171714;padding:20px 58px}.answer>b{font-size:12px}.answer>div{display:grid;grid-template-columns:1fr 1fr;gap:46px;margin-top:14px}.answer strong,.answer span{font-size:12px;line-height:1.3}.answer span{font-weight:400}@media print{body{background:#fff}.page{margin:0}}''' + asset_rules
    document = f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>AI From Scratch Editorial Workbook</title><style>{css}</style></head><body>{"".join(pages)}</body></html>'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")


def slug(topic: dict, idx: int) -> str:
    return f"{idx+1:02d}_{re.sub(r'[^a-z0-9]+', '_', topic['title_en'].lower()).strip('_')}"


def main() -> None:
    PDFS.mkdir(parents=True, exist_ok=True); CANVA.mkdir(parents=True, exist_ok=True)
    all_indexes = list(range(12))
    build_pdf(PDFS / "AIFromScratch_Editorial_Bilingual_Workbook_V2.pdf", all_indexes, True)
    build_html(CANVA / "AIFromScratch_Editorial_Bilingual_Workbook_V2.html", all_indexes, True)
    for idx, topic in enumerate(TOPICS):
        name = slug(topic, idx)
        build_pdf(PDFS / f"AIFromScratch_V2_{name}.pdf", [idx], False)
        build_html(CANVA / f"AIFromScratch_V2_{name}.html", [idx], False)
    print("Generated the editorial V2 master and twelve topic editions.")


if __name__ == "__main__":
    main()
