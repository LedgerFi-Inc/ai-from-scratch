#!/usr/bin/env python3
"""Generate V6 with neutral dark pages and blue accents only on light pages."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import generate_course_workbook_v4_separated as base
from generate_course_workbook import TOPICS


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "workbook-v6-neutral-dark"
ASSETS = OUT / "assets"
SOURCE_ASSETS = ROOT / "output" / "workbook-v5-corporate" / "assets"

DARK_META = "#D1D1D6"
DARK_BORDER = "#48484A"


def cover(c, lang: str, total: int) -> None:
    s = base.cfg(lang)
    c.setFillColor(base.brand.C(base.brand.BLACK)); c.rect(0, 0, base.PAGE_W, base.PAGE_H, fill=1, stroke=0)
    base.brand.brand_mark(c, 42, 457, inverse=True)
    c.setFont("MonoBold", 10); c.setFillColor(base.brand.C(DARK_META)); c.drawString(92, 474, s["guide"])
    if lang == "en":
        c.setFont("UIBlack", 56); c.setFillColor(base.brand.C(base.brand.WHITE))
        c.drawString(42, 366, "AI From"); c.drawString(42, 312, "Scratch"); sub_y = 230
    else:
        c.setFont("UIBlack", 57); c.setFillColor(base.brand.C(base.brand.WHITE))
        c.drawString(42, 346, s["cover_title"]); sub_y = 250
    base.brand.draw_text(c, s["cover_sub"], 45, sub_y, 430, font="UIBold", size=21, leading=26, fill=base.brand.WHITE, max_lines=4)
    c.setStrokeColor(base.brand.C(DARK_BORDER)); c.setLineWidth(2); c.line(45, 122, 456, 122)
    c.setFont("Mono", 10); c.setFillColor(base.brand.C(base.brand.LIGHT_3)); c.drawString(45, 96, s["cover_meta"])
    for i, (x, y, w, h) in enumerate(((532, 273, 178, 181), (718, 273, 196, 181), (532, 66, 382, 199)), start=1):
        base.brand.place_image(c, ASSETS / f"topic-{i:02d}.jpg", x, y, w, h, stroke=DARK_BORDER, line=1)
    base.footer(c, lang, None, 1, total, inverse=True); c.showPage()


def opener(c, lang: str, topic: dict, no: int, page_no: int, total: int) -> None:
    s = base.cfg(lang)
    c.setFillColor(base.brand.C(base.brand.BLACK)); c.rect(0, 0, base.PAGE_W, base.PAGE_H, fill=1, stroke=0)
    base.brand.brand_mark(c, 36, 466, inverse=True)
    c.setFont("MonoBold", 10); c.setFillColor(base.brand.C(DARK_META)); c.drawString(88, 482, f"{s['topic']} {no:02d} / {s['intro']}")
    c.setFont("UIBlack", 94); c.setFillColor(base.brand.C(base.brand.PANEL)); c.drawRightString(490, 411, f"{no:02d}")
    base.brand.draw_text(c, topic[s["title_key"]], 43, 381, 412, font="UIBlack", size=42, leading=46, fill=base.brand.WHITE, max_lines=3)
    c.setStrokeColor(base.brand.C(base.brand.HAIR_DARK)); c.setLineWidth(1); c.line(43, 238, 456, 238)
    base.brand.label(c, s["objective"], 43, 211, color=DARK_META, inverse=True)
    base.brand.draw_text(c, topic[s["objective_key"]], 43, 173, 398, font="UIBold", size=17, leading=22, fill=base.brand.WHITE, max_lines=6)
    base.brand.place_image(c, ASSETS / f"topic-{no:02d}.jpg", 502, 49, 416, 441, stroke=DARK_BORDER, line=1)
    base.footer(c, lang, no, page_no, total, inverse=True); c.showPage()


def analogy(c, lang: str, topic: dict, no: int, page_no: int, total: int) -> None:
    s = base.cfg(lang)
    c.setFillColor(base.brand.C(base.brand.BLACK)); c.rect(0, 0, base.PAGE_W, base.PAGE_H, fill=1, stroke=0)
    base.brand.place_image(c, ASSETS / f"topic-{no:02d}.jpg", 0, 0, 480, base.PAGE_H, stroke=DARK_BORDER, line=1)
    c.setFillColor(base.brand.C(base.brand.PANEL)); c.rect(480, 0, 480, base.PAGE_H, fill=1, stroke=0)
    base.brand.brand_mark(c, 514, 466, inverse=True)
    base.brand.label(c, s["analogy"], 568, 482, color=DARK_META, inverse=True)
    base.brand.draw_text(c, topic[s["analogy_key"]], 518, 408, 398, font="UIBold", size=24, leading=29, fill=base.brand.WHITE, max_lines=7)
    c.setFillColor(base.brand.C(base.brand.BLACK)); c.setStrokeColor(base.brand.C(base.brand.HAIR_DARK)); c.setLineWidth(1)
    c.rect(518, 75, 398, 132, fill=1, stroke=1)
    c.setFont("MonoBold", 10); c.setFillColor(base.brand.C(DARK_META)); c.drawString(538, 177, s["example"])
    base.brand.draw_text(c, topic[s["example_key"]], 538, 143, 348, font="UIBold", size=12, leading=16, fill=base.brand.WHITE, max_lines=6)
    base.footer(c, lang, no, page_no, total, inverse=True); c.showPage()


HTML_NEUTRAL_DARK = """
.cover .meta,.opener .meta,.analogy-copy .meta{color:#D1D1D6}
.cover-copy small{border-top-color:#48484A}
.cover-collage .art,.op-img{border-color:#48484A}
.op-copy b{color:#D1D1D6}
.eye{display:none}
.analogy-img{border-right-color:#48484A}
.example b{color:#D1D1D6}
"""


def zip_pdfs(lang: str, pdf_dir: Path) -> None:
    target = OUT / f"AIFromScratch_V6_{base.cfg(lang)['name']}_Neutral_Dark_All_PDFs.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for pdf in sorted(pdf_dir.glob("*.pdf")):
            archive.write(pdf, arcname=pdf.name)


def prepare() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for source in sorted(SOURCE_ASSETS.glob("topic-*.jpg")):
        shutil.copy2(source, ASSETS / source.name)
    base.OUT = OUT
    base.ASSETS = ASSETS
    base.cover = cover
    base.opener = opener
    base.analogy = analogy
    base.CSS += HTML_NEUTRAL_DARK


def main() -> None:
    prepare()
    for lang in ("es", "en"):
        settings = base.cfg(lang)
        root = OUT / settings["folder"]
        pdf_dir = root / "pdf"
        canva_dir = root / "canva"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        canva_dir.mkdir(parents=True, exist_ok=True)
        indexes = list(range(12))
        base.build_pdf(pdf_dir / f"AIFromScratch_V6_{settings['name']}_Neutral_Dark_Master.pdf", lang, indexes, True)
        base.build_html(canva_dir / f"AIFromScratch_V6_{settings['name']}_Neutral_Dark_Master.html", lang, indexes, True)
        for idx, topic in enumerate(TOPICS):
            name = base.slug(topic, idx, lang)
            base.build_pdf(pdf_dir / f"AIFromScratch_V6_{settings['name']}_Neutral_Dark_{name}.pdf", lang, [idx], False)
            base.build_html(canva_dir / f"AIFromScratch_V6_{settings['name']}_Neutral_Dark_{name}.html", lang, [idx], False)
        zip_pdfs(lang, pdf_dir)
    print("Generated V6 with neutral dark pages and blue only on light pages.")


if __name__ == "__main__":
    main()
