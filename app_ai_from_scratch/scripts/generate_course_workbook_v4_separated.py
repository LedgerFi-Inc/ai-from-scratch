#!/usr/bin/env python3
"""Generate separate Spanish and English AIFromScratch workbook collections."""

from __future__ import annotations

import base64
import html
import re
import zipfile
from pathlib import Path

from reportlab.pdfgen import canvas

import generate_course_workbook_v3 as brand
from generate_course_workbook import TOPICS


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "workbook-v4-separated"
ASSETS = OUT / "assets"
PAGE_W, PAGE_H = 960, 540


LANG = {
    "es": {
        "folder": "espanol", "name": "Español", "topic": "TEMA",
        "guide": "GUÍA VISUAL DEL CURSO / 2026", "cover_title": "IA desde cero",
        "cover_sub": "12 lecciones visuales para entender y usar la inteligencia artificial.",
        "cover_meta": "CONCEPTOS / EJEMPLOS / PRÁCTICA", "intro": "INTRODUCCIÓN",
        "objective": "OBJETIVO", "mechanism": "CÓMO FUNCIONA", "mechanism_title": "Cómo funciona",
        "analogy": "ANALOGÍA", "example": "EJEMPLO", "practice": "PRÁCTICA",
        "practice_title": "Pruébalo", "answer": "RESPUESTA",
        "title_key": "title_es", "objective_key": "objective_es", "mechanism_key": "mechanism_es",
        "steps_key": "steps_es", "analogy_key": "analogy_es", "example_key": "example_es",
        "practice_key": "practice_es", "answer_key": "answer_es",
    },
    "en": {
        "folder": "english", "name": "English", "topic": "TOPIC",
        "guide": "COURSE FIELD GUIDE / 2026", "cover_title": "AI From Scratch",
        "cover_sub": "12 visual lessons to understand and use artificial intelligence.",
        "cover_meta": "CONCEPTS / EXAMPLES / PRACTICE", "intro": "INTRO",
        "objective": "OBJECTIVE", "mechanism": "HOW IT WORKS", "mechanism_title": "How it works",
        "analogy": "ANALOGY", "example": "EXAMPLE", "practice": "PRACTICE",
        "practice_title": "Try it", "answer": "ANSWER",
        "title_key": "title_en", "objective_key": "objective_en", "mechanism_key": "mechanism_en",
        "steps_key": "steps_en", "analogy_key": "analogy_en", "example_key": "example_en",
        "practice_key": "practice_en", "answer_key": "answer_en",
    },
}


def cfg(lang: str) -> dict:
    return LANG[lang]


def footer(c: canvas.Canvas, lang: str, topic_no: int | None, page_no: int, total: int, *, inverse: bool = False) -> None:
    s = cfg(lang)
    fg = brand.LIGHT_2 if inverse else "#66666B"
    hair = brand.HAIR_DARK if inverse else brand.HAIR_LIGHT
    c.setStrokeColor(brand.C(hair)); c.setLineWidth(.5); c.line(32, 31, PAGE_W - 32, 31)
    c.setFont("MonoBold", 8); c.setFillColor(brand.C(fg))
    left = f"AI FROM SCRATCH / {s['topic']} {topic_no:02d}" if topic_no else f"AI FROM SCRATCH / {s['name'].upper()}"
    c.drawString(32, 16, left); c.drawRightString(PAGE_W - 32, 16, f"{page_no:02d}/{total:02d}")


def cover(c: canvas.Canvas, lang: str, total: int) -> None:
    s = cfg(lang)
    c.setFillColor(brand.C(brand.BLACK)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    brand.brand_mark(c, 42, 457, inverse=True)
    c.setFont("MonoBold", 10); c.setFillColor(brand.C(brand.BLUE)); c.drawString(92, 474, s["guide"])
    if lang == "en":
        c.setFont("UIBlack", 56); c.setFillColor(brand.C(brand.WHITE))
        c.drawString(42, 366, "AI From"); c.drawString(42, 312, "Scratch"); sub_y = 230
    else:
        c.setFont("UIBlack", 57); c.setFillColor(brand.C(brand.WHITE))
        c.drawString(42, 346, s["cover_title"]); sub_y = 250
    brand.draw_text(c, s["cover_sub"], 45, sub_y, 430, font="UIBold", size=21, leading=26, fill=brand.WHITE, max_lines=4)
    c.setStrokeColor(brand.C(brand.BLUE)); c.setLineWidth(2); c.line(45, 122, 456, 122)
    c.setFont("Mono", 10); c.setFillColor(brand.C(brand.LIGHT_3)); c.drawString(45, 96, s["cover_meta"])
    for i, (x, y, w, h) in enumerate(((532, 273, 178, 181), (718, 273, 196, 181), (532, 66, 382, 199)), start=1):
        brand.place_image(c, ASSETS / f"topic-{i:02d}.jpg", x, y, w, h, stroke=brand.BLUE, line=1)
    footer(c, lang, None, 1, total, inverse=True); c.showPage()


def opener(c: canvas.Canvas, lang: str, topic: dict, no: int, page_no: int, total: int) -> None:
    s = cfg(lang)
    c.setFillColor(brand.C(brand.BLACK)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    brand.brand_mark(c, 36, 466, inverse=True)
    c.setFont("MonoBold", 10); c.setFillColor(brand.C(brand.BLUE)); c.drawString(88, 482, f"{s['topic']} {no:02d} / {s['intro']}")
    c.setFont("UIBlack", 94); c.setFillColor(brand.C(brand.PANEL)); c.drawRightString(490, 411, f"{no:02d}")
    brand.draw_text(c, topic[s["title_key"]], 43, 381, 412, font="UIBlack", size=42, leading=46, fill=brand.WHITE, max_lines=3)
    c.setStrokeColor(brand.C(brand.HAIR_DARK)); c.setLineWidth(1); c.line(43, 238, 456, 238)
    brand.label(c, s["objective"], 43, 211, inverse=True)
    brand.draw_text(c, topic[s["objective_key"]], 43, 173, 398, font="UIBold", size=17, leading=22, fill=brand.WHITE, max_lines=6)
    brand.place_image(c, ASSETS / f"topic-{no:02d}.jpg", 502, 49, 416, 441, stroke=brand.BLUE, line=1)
    c.setFillColor(brand.C(brand.YELLOW)); c.circle(902, 474, 5, fill=1, stroke=0)
    footer(c, lang, no, page_no, total, inverse=True); c.showPage()


def mechanism(c: canvas.Canvas, lang: str, topic: dict, no: int, page_no: int, total: int) -> None:
    s = cfg(lang)
    c.setFillColor(brand.C(brand.PAPER)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    brand.brand_mark(c, 36, 466)
    c.setFont("MonoBold", 10); c.setFillColor(brand.C(brand.BLUE_PAPER)); c.drawString(88, 482, f"{s['topic']} {no:02d} / {s['mechanism']}")
    brand.place_image(c, ASSETS / f"topic-{no:02d}.jpg", 36, 76, 344, 368, stroke=brand.INK, line=1)
    c.setFont("UIBlack", 34); c.setFillColor(brand.C(brand.INK)); c.drawString(422, 430, s["mechanism_title"])
    brand.draw_text(c, topic[s["mechanism_key"]], 423, 371, 493, size=16, leading=21, max_lines=7)
    c.setStrokeColor(brand.C(brand.INK)); c.setLineWidth(1); c.line(423, 224, 915, 224)
    for i, step in enumerate(topic[s["steps_key"]]):
        x = 423 + i * 123
        c.setFillColor(brand.C(brand.BLUE_PAPER if i == 0 else brand.INK)); c.rect(x, 180, 29, 29, fill=1, stroke=0)
        c.setFont("MonoBold", 10); c.setFillColor(brand.C(brand.WHITE)); c.drawCentredString(x + 14.5, 190, str(i + 1))
        brand.draw_text(c, step, x, 154, 110, font="UIBold", size=12, leading=14, max_lines=5)
    footer(c, lang, no, page_no, total); c.showPage()


def analogy(c: canvas.Canvas, lang: str, topic: dict, no: int, page_no: int, total: int) -> None:
    s = cfg(lang)
    c.setFillColor(brand.C(brand.BLACK)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    brand.place_image(c, ASSETS / f"topic-{no:02d}.jpg", 0, 0, 480, PAGE_H, stroke=brand.BLUE, line=1)
    c.setFillColor(brand.C(brand.PANEL)); c.rect(480, 0, 480, PAGE_H, fill=1, stroke=0)
    brand.brand_mark(c, 514, 466, inverse=True); brand.label(c, s["analogy"], 568, 482, inverse=True)
    brand.draw_text(c, topic[s["analogy_key"]], 518, 408, 398, font="UIBold", size=24, leading=29, fill=brand.WHITE, max_lines=7)
    c.setFillColor(brand.C(brand.BLACK)); c.setStrokeColor(brand.C(brand.HAIR_DARK)); c.setLineWidth(1)
    c.rect(518, 75, 398, 132, fill=1, stroke=1)
    c.setFont("MonoBold", 10); c.setFillColor(brand.C(brand.BLUE)); c.drawString(538, 177, s["example"])
    brand.draw_text(c, topic[s["example_key"]], 538, 143, 348, font="UIBold", size=12, leading=16, fill=brand.WHITE, max_lines=6)
    footer(c, lang, no, page_no, total, inverse=True); c.showPage()


def practice(c: canvas.Canvas, lang: str, topic: dict, no: int, page_no: int, total: int) -> None:
    s = cfg(lang)
    c.setFillColor(brand.C(brand.PAPER)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    brand.brand_mark(c, 36, 466)
    c.setFont("MonoBold", 10); c.setFillColor(brand.C(brand.BLUE_PAPER)); c.drawString(88, 482, f"{s['topic']} {no:02d} / {s['practice']}")
    c.setFont("UIBlack", 34); c.setFillColor(brand.C(brand.INK)); c.drawString(42, 413, s["practice_title"])
    brand.place_image(c, ASSETS / f"topic-{no:02d}.jpg", 734, 355, 182, 112, stroke=brand.INK, line=1)
    brand.draw_text(c, topic[s["practice_key"]], 42, 328, 650, font="UIBlack", size=30, leading=35, max_lines=5)
    c.setFillColor(brand.C(brand.WHITE)); c.setStrokeColor(brand.C(brand.BLUE_PAPER)); c.setLineWidth(2)
    c.rect(42, 61, 874, 132, fill=1, stroke=1)
    c.setFont("MonoBold", 10); c.setFillColor(brand.C(brand.GREEN)); c.drawString(62, 164, s["answer"])
    brand.draw_text(c, topic[s["answer_key"]], 62, 130, 824, font="UIBold", size=15, leading=19, max_lines=5)
    footer(c, lang, no, page_no, total); c.showPage()


def build_pdf(path: Path, lang: str, indexes: list[int], with_cover: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    total = len(indexes) * 4 + (1 if with_cover else 0)
    c = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    page_no = 1
    if with_cover:
        cover(c, lang, total); page_no += 1
    for idx in indexes:
        topic, no = TOPICS[idx], idx + 1
        opener(c, lang, topic, no, page_no, total); page_no += 1
        mechanism(c, lang, topic, no, page_no, total); page_no += 1
        analogy(c, lang, topic, no, page_no, total); page_no += 1
        practice(c, lang, topic, no, page_no, total); page_no += 1
    c.save()


def data_uri(path: Path) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def H(value: str) -> str:
    return html.escape(brand.clean(value)).replace("\n", "<br>")


def page(content: str, lang: str, topic_no: int | None, page_no: int, total: int, label: str, cls: str) -> str:
    s = cfg(lang)
    tail = f" / {s['topic']} {topic_no:02d}" if topic_no else f" / {s['name'].upper()}"
    return f'<section class="page {cls}" data-document-role="page" data-label="{html.escape(label)}">{content}<footer><span>AI FROM SCRATCH{tail}</span><span>{page_no:02d}/{total:02d}</span></footer></section>'


def mark(inverse: bool = False) -> str:
    return f'<div class="mark{" inverse" if inverse else ""}">IA</div>'


def topic_html(lang: str, topic: dict, no: int, page_no: int, total: int) -> tuple[list[str], int]:
    s = cfg(lang); out: list[str] = []
    intro = f'''{mark(True)}<div class="meta">{s['topic']} {no:02d} / {s['intro']}</div><div class="op-copy"><div class="ghost">{no:02d}</div><h1>{H(topic[s['title_key']])}</h1><hr><b>{s['objective']}</b><p>{H(topic[s['objective_key']])}</p></div><div class="op-img art t{no}"></div><i class="eye"></i>'''
    out.append(page(intro, lang, no, page_no, total, f"{s['topic']} {no} {s['intro']}", "opener")); page_no += 1
    steps = "".join(f'<div class="node"><i>{i+1}</i><strong>{H(step)}</strong></div>' for i, step in enumerate(topic[s['steps_key']]))
    mech = f'''{mark()}<div class="meta">{s['topic']} {no:02d} / {s['mechanism']}</div><div class="mech-img art t{no}"></div><main class="mech-copy"><h1>{s['mechanism_title']}</h1><p>{H(topic[s['mechanism_key']])}</p><div class="process">{steps}</div></main>'''
    out.append(page(mech, lang, no, page_no, total, f"{s['topic']} {no} {s['mechanism']}", "mechanism")); page_no += 1
    ana = f'''<div class="analogy-img art t{no}"></div><main class="analogy-copy">{mark(True)}<div class="meta">{s['analogy']}</div><h1>{H(topic[s['analogy_key']])}</h1><div class="example"><b>{s['example']}</b><p>{H(topic[s['example_key']])}</p></div></main>'''
    out.append(page(ana, lang, no, page_no, total, f"{s['topic']} {no} {s['analogy']}", "analogy-page")); page_no += 1
    prac = f'''{mark()}<div class="meta">{s['topic']} {no:02d} / {s['practice']}</div><h1 class="practice-title">{s['practice_title']}</h1><div class="practice-img art t{no}"></div><div class="question"><h1>{H(topic[s['practice_key']])}</h1></div><div class="answer"><b>{s['answer']}</b><strong>{H(topic[s['answer_key']])}</strong></div>'''
    out.append(page(prac, lang, no, page_no, total, f"{s['topic']} {no} {s['practice']}", "practice-page")); page_no += 1
    return out, page_no


CSS = '''*{box-sizing:border-box}body{margin:0;background:#5a5a5d;font-family:Arial,Helvetica,sans-serif;color:#000}.page{position:relative;width:960px;height:540px;margin:24px auto;background:#F2F2F2;overflow:hidden;page-break-after:always}.page footer{position:absolute;left:32px;right:32px;bottom:14px;padding-top:7px;border-top:1px solid #C7C7CC;display:flex;justify-content:space-between;font:700 8px "Courier New",monospace;color:#66666B}.art{background-size:contain;background-repeat:no-repeat;background-position:center;background-color:#F2F2F2}.mark{position:absolute;left:36px;top:38px;width:36px;height:36px;background:#000;color:#fff;border:1px solid #000;display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:700}.mark.inverse{background:#fff;color:#000;border-color:#fff}.meta{position:absolute;left:88px;top:54px;color:#0A5AD6;font:700 10px "Courier New",monospace}.cover{background:#000;color:#fff}.cover .mark{left:42px;top:45px}.cover .meta{left:92px;top:60px;color:#0A84FF}.cover-copy{position:absolute;left:45px;top:125px;width:440px}.cover-copy h1{font-size:56px;line-height:.94;margin:0}.cover-copy p{font-size:21px;line-height:1.25;font-weight:700;margin:38px 0}.cover-copy small{display:block;border-top:2px solid #0A84FF;padding-top:18px;margin-top:48px;color:#8E8E93;font:10px "Courier New",monospace}.cover-collage .art{position:absolute;border:1px solid #0A84FF}.cover-collage .art:nth-child(1){left:532px;top:86px;width:178px;height:181px}.cover-collage .art:nth-child(2){left:718px;top:86px;width:196px;height:181px}.cover-collage .art:nth-child(3){left:532px;top:293px;width:382px;height:199px}.cover footer,.opener footer,.analogy-page footer{border-color:#3A3A3C;color:#B8B8BE}.opener{background:#000;color:#fff}.opener .meta{color:#0A84FF}.op-copy{position:absolute;left:43px;top:126px;width:420px}.ghost{position:absolute;right:0;top:-32px;color:#0B0B0C;font-size:94px;font-weight:900}.op-copy h1{position:relative;font-size:42px;line-height:1.06;margin:0 0 35px}.op-copy hr{border:0;border-top:1px solid #3A3A3C;margin:0 0 24px}.op-copy b{display:block;color:#0A84FF;font:700 10px "Courier New",monospace;margin-bottom:22px}.op-copy p{font-size:17px;line-height:1.3;font-weight:700;margin:0;max-width:398px}.op-img{position:absolute;left:502px;top:50px;width:416px;height:441px;border:1px solid #0A84FF}.eye{position:absolute;right:52px;top:61px;width:10px;height:10px;background:#FFD60A;border-radius:50%}.mech-img{position:absolute;left:36px;top:96px;width:344px;height:368px;border:1px solid #000}.mech-copy{position:absolute;left:423px;top:104px;width:493px}.mech-copy h1{font-size:34px;margin:0 0 25px}.mech-copy>p{font-size:16px;line-height:1.32;margin:0}.process{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;margin-top:25px;padding-top:20px;border-top:1px solid #000}.node i{display:flex;width:29px;height:29px;align-items:center;justify-content:center;background:#000;color:#fff;font:700 10px "Courier New",monospace;font-style:normal}.node:first-child i{background:#0A5AD6}.node strong{display:block;margin-top:12px;font-size:12px;line-height:1.2}.analogy-img{position:absolute;inset:0 auto 0 0;width:480px;height:540px;border-right:1px solid #0A84FF}.analogy-copy{position:absolute;left:480px;top:0;width:480px;height:540px;background:#0B0B0C;color:#fff;padding:112px 44px}.analogy-copy .mark{top:38px;left:34px}.analogy-copy .meta{left:88px;top:54px;color:#0A84FF}.analogy-copy h1{font-size:24px;line-height:1.24;margin:0}.example{position:absolute;left:38px;right:44px;bottom:75px;height:132px;background:#000;border:1px solid #3A3A3C;padding:20px}.example b{color:#0A84FF;font:700 10px "Courier New",monospace}.example p{font-size:12px;line-height:1.3;font-weight:700;margin:17px 0 0}.practice-title{position:absolute;left:42px;top:105px;font-size:34px;margin:0}.practice-img{position:absolute;right:44px;top:73px;width:182px;height:112px;border:1px solid #000}.question{position:absolute;left:42px;top:205px;width:650px}.question h1{font-size:30px;line-height:1.18;margin:0}.answer{position:absolute;left:42px;right:44px;bottom:61px;height:132px;background:#fff;border:2px solid #0A5AD6;padding:23px 20px}.answer b{display:block;color:#30D158;font:700 10px "Courier New",monospace;margin-bottom:20px}.answer strong{display:block;font-size:15px;line-height:1.28}@media print{body{background:#fff}.page{margin:0}}'''


def build_html(path: Path, lang: str, indexes: list[int], with_cover: bool) -> None:
    s = cfg(lang); total = len(indexes) * 4 + (1 if with_cover else 0); pages: list[str] = []; page_no = 1
    if with_cover:
        collage = "".join(f'<div class="art t{i}"></div>' for i in (1, 2, 3))
        content = f'''{mark(True)}<div class="meta">{s['guide']}</div><div class="cover-copy"><h1>{H(s['cover_title'])}</h1><p>{H(s['cover_sub'])}</p><small>{H(s['cover_meta'])}</small></div><div class="cover-collage">{collage}</div>'''
        pages.append(page(content, lang, None, 1, total, s["cover_title"], "cover")); page_no += 1
    for idx in indexes:
        built, page_no = topic_html(lang, TOPICS[idx], idx + 1, page_no, total); pages.extend(built)
    needed = ({1, 2, 3} if with_cover else set()) | {idx + 1 for idx in indexes}
    assets = "".join(f'.t{i}{{background-image:url("{data_uri(ASSETS / f"topic-{i:02d}.jpg")}")}}' for i in sorted(needed))
    doc = f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>{html.escape(s["cover_title"])}</title><style>{CSS}{assets}</style></head><body>{"".join(pages)}</body></html>'
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(doc, encoding="utf-8")


def slug(topic: dict, idx: int, lang: str) -> str:
    value = topic[cfg(lang)["title_key"]].lower().encode("ascii", "ignore").decode("ascii")
    return f"{idx + 1:02d}_{re.sub(r'[^a-z0-9]+', '_', value).strip('_')}"


def zip_pdfs(lang: str, pdf_dir: Path) -> None:
    target = OUT / f"AIFromScratch_V4_{cfg(lang)['name']}_All_PDFs.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for p in sorted(pdf_dir.glob("*.pdf")):
            archive.write(p, arcname=p.name)


def main() -> None:
    for lang in ("es", "en"):
        s = cfg(lang); base = OUT / s["folder"]; pdf_dir = base / "pdf"; canva_dir = base / "canva"
        pdf_dir.mkdir(parents=True, exist_ok=True); canva_dir.mkdir(parents=True, exist_ok=True)
        indexes = list(range(12))
        build_pdf(pdf_dir / f"AIFromScratch_V4_{s['name']}_Master.pdf", lang, indexes, True)
        build_html(canva_dir / f"AIFromScratch_V4_{s['name']}_Master.html", lang, indexes, True)
        for idx, topic in enumerate(TOPICS):
            name = slug(topic, idx, lang)
            build_pdf(pdf_dir / f"AIFromScratch_V4_{s['name']}_{name}.pdf", lang, [idx], False)
            build_html(canva_dir / f"AIFromScratch_V4_{s['name']}_{name}.html", lang, [idx], False)
        zip_pdfs(lang, pdf_dir)
    print("Generated separate Spanish and English V4 collections.")


if __name__ == "__main__":
    main()
