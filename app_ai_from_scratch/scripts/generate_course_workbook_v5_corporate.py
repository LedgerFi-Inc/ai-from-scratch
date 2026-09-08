#!/usr/bin/env python3
"""Generate the simplified corporate Spanish and English workbook collections."""

from __future__ import annotations

import zipfile
from pathlib import Path

import generate_course_workbook_v4_separated as base
from generate_course_workbook import TOPICS


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "workbook-v5-corporate"
ASSETS = OUT / "assets"


def zip_pdfs(lang: str, pdf_dir: Path) -> None:
    target = OUT / f"AIFromScratch_V5_{base.cfg(lang)['name']}_Corporate_All_PDFs.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for pdf in sorted(pdf_dir.glob("*.pdf")):
            archive.write(pdf, arcname=pdf.name)


def main() -> None:
    base.OUT = OUT
    base.ASSETS = ASSETS
    for lang in ("es", "en"):
        settings = base.cfg(lang)
        root = OUT / settings["folder"]
        pdf_dir = root / "pdf"
        canva_dir = root / "canva"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        canva_dir.mkdir(parents=True, exist_ok=True)
        indexes = list(range(12))
        base.build_pdf(pdf_dir / f"AIFromScratch_V5_{settings['name']}_Corporate_Master.pdf", lang, indexes, True)
        base.build_html(canva_dir / f"AIFromScratch_V5_{settings['name']}_Corporate_Master.html", lang, indexes, True)
        for idx, topic in enumerate(TOPICS):
            name = base.slug(topic, idx, lang)
            base.build_pdf(pdf_dir / f"AIFromScratch_V5_{settings['name']}_Corporate_{name}.pdf", lang, [idx], False)
            base.build_html(canva_dir / f"AIFromScratch_V5_{settings['name']}_Corporate_{name}.html", lang, [idx], False)
        zip_pdfs(lang, pdf_dir)
    print("Generated simplified corporate V5 collections.")


if __name__ == "__main__":
    main()
