from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ROOT / "frames"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920
BLACK = (5, 5, 6)
PAPER = (244, 244, 240)
MUTED = (158, 158, 164)
HAIR = (48, 48, 52)
BLUE = (10, 132, 255)

HELV = "/System/Library/Fonts/HelveticaNeue.ttc"
MONO = "/System/Library/Fonts/SFNSMono.ttf"


def font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    idx = {"regular": 0, "bold": 1, "medium": 10, "condensed": 4}.get(weight, 0)
    return ImageFont.truetype(HELV, size=size, index=idx)


def mono(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(MONO, size=size)


def tracked(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str,
            fnt: ImageFont.FreeTypeFont, fill, tracking: int = 4) -> int:
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += int(draw.textlength(ch, font=fnt)) + tracking
    return x


def fit(text: str, max_width: int, start: int, weight: str = "bold") -> ImageFont.FreeTypeFont:
    size = start
    probe = Image.new("RGB", (4, 4))
    d = ImageDraw.Draw(probe)
    while size > 20:
        fnt = font(size, weight)
        if d.textbbox((0, 0), text, font=fnt)[2] <= max_width:
            return fnt
        size -= 2
    return font(size, weight)


def base(page: str, progress: float) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGB", (W, H), BLACK)
    d = ImageDraw.Draw(im)
    # Editorial grid from the real site.
    for x in range(0, W + 1, 180):
        d.line((x, 0, x, H), fill=(18, 18, 20), width=1)
    for y in range(0, H + 1, 240):
        d.line((0, y, W, y), fill=(14, 14, 16), width=1)
    d.line((0, 86, W, 86), fill=HAIR, width=1)
    d.rectangle((0, 0, int(W * progress), 3), fill=BLUE)
    d.rectangle((48, 25, 87, 64), outline=PAPER, width=2)
    d.text((59, 31), "IA", font=font(17, "bold"), fill=PAPER)
    d.text((105, 27), "IA DESDE CERO", font=font(22, "bold"), fill=PAPER)
    tracked(d, (105, 53), "FUNDAMENTOS · VOL. 1", mono(10), MUTED, 3)
    tracked(d, (886, 35), page, mono(13), MUTED, 3)
    return im, d


def add_grain(im: Image.Image, amount: float = 0.045) -> Image.Image:
    grain = Image.effect_noise((W, H), 18).convert("L")
    grain = ImageEnhance.Contrast(grain).enhance(0.45)
    layer = Image.merge("RGB", (grain, grain, grain))
    return Image.blend(im, layer, amount)


def rounded_media(im: Image.Image, box: tuple[int, int, int, int], radius: int = 28,
                  border: tuple[int, int, int] = HAIR) -> None:
    x0, y0, x1, y1 = box
    src = ImageOps.fit(im, (x1 - x0, y1 - y0), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", src.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, src.width - 1, src.height - 1), radius=radius, fill=255)
    im_canvas = Image.new("RGB", (W, H), BLACK)
    im_canvas.paste(src, (x0, y0), mask)
    im.paste(im_canvas.crop(box), (x0, y0))
    ImageDraw.Draw(im).rounded_rectangle(box, radius=radius, outline=border, width=2)


def cover_crop(src: Image.Image, top: int, bottom: int) -> Image.Image:
    top = max(0, top)
    bottom = min(src.height, bottom)
    return src.crop((0, top, src.width, bottom))


def contain_frame(src: Image.Image, size: tuple[int, int], bg=BLACK) -> Image.Image:
    fitted = ImageOps.contain(src, size, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, bg)
    canvas.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return canvas


def save(im: Image.Image, name: str) -> None:
    add_grain(im).save(OUT / name, quality=95)


cover = Image.open(ASSETS / "producto-portada-es.png").convert("RGB")
demo = Image.open(ASSETS / "producto-demo.png").convert("RGB")
offer = Image.open(ASSETS / "producto-oferta.png").convert("RGB")


# 01 — Hook: one idea, one visual hierarchy.
im, d = base("01 / 06", 0.08)
tracked(d, (66, 220), "LA DIFERENCIA ENTRE USARLA Y DOMINARLA", mono(14), BLUE, 3)
d.text((66, 320), "USAR", font=font(142, "bold"), fill=PAPER)
d.text((66, 474), "CHATGPT", font=font(142, "bold"), fill=PAPER)
d.text((66, 650), "NO ES", font=font(86, "medium"), fill=MUTED)
d.text((66, 758), "ENTENDER", font=font(126, "bold"), fill=BLUE)
d.text((66, 890), "LA IA.", font=font(146, "bold"), fill=PAPER)
d.line((66, 1120, 1014, 1120), fill=HAIR, width=2)
d.text((66, 1185), "Si no sabes por qué falla,", font=font(48, "regular"), fill=MUTED)
d.text((66, 1248), "sigues usándola a ciegas.", font=font(48, "bold"), fill=PAPER)
for i, label in enumerate(("INVENTA DATOS", "SALE GENÉRICO", "PIERDE CONTEXTO")):
    y = 1472 + i * 112
    d.text((66, y), f"0{i+1}", font=mono(18), fill=BLUE)
    d.text((134, y - 4), label, font=font(30, "medium"), fill=PAPER)
    d.line((66, y + 50, 1014, y + 50), fill=HAIR, width=1)
save(im, "01-hook.png")


# 02 — Real pain section from the actual landing page.
im, d = base("02 / 06", 0.25)
pain = cover_crop(cover, 760, 1750)
pain = ImageEnhance.Contrast(pain).enhance(1.08)
rounded_media(im, (54, 340, 1026, 1550), radius=26)
# rounded_media works from the supplied image; replace its temporary source with pain.
src = contain_frame(pain, (972, 1210))
mask = Image.new("L", src.size, 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, 971, 1209), radius=26, fill=255)
im.paste(src, (54, 340), mask)
d = ImageDraw.Draw(im)
d.rounded_rectangle((54, 340, 1026, 1550), radius=26, outline=HAIR, width=2)
tracked(d, (66, 174), "EL PROBLEMA NO ES LA HERRAMIENTA", mono(14), BLUE, 3)
d.text((66, 218), "Es usarla sin entenderla.", font=font(55, "bold"), fill=PAPER)
d.rounded_rectangle((66, 1610, 1014, 1782), radius=20, fill=(12, 12, 14), outline=HAIR, width=2)
d.text((102, 1647), "DATOS FALSOS  ·  RESPUESTAS GENÉRICAS", font=font(30, "bold"), fill=PAPER)
d.text((102, 1703), "CHATS QUE PIERDEN EL HILO", font=font(30, "bold"), fill=BLUE)
save(im, "02-problema.png")


# 03 — Product hero, using the actual interface.
im, d = base("03 / 06", 0.43)
hero = cover_crop(cover, 0, 930)
shadow = Image.new("RGBA", (940, 1070), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.rounded_rectangle((32, 32, 908, 1038), radius=34, fill=(0, 0, 0, 190))
shadow = shadow.filter(ImageFilter.GaussianBlur(24))
im.paste(shadow.convert("RGB"), (70, 310))
src = contain_frame(hero, (908, 1000))
mask = Image.new("L", src.size, 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, 907, 999), radius=28, fill=255)
im.paste(src, (86, 330), mask)
d = ImageDraw.Draw(im)
d.rounded_rectangle((86, 330, 994, 1330), radius=28, outline=HAIR, width=2)
tracked(d, (66, 174), "EL CURSO QUE VA AL PUNTO", mono(14), BLUE, 3)
d.text((66, 1398), "ENTIENDE LA IA", font=font(78, "bold"), fill=PAPER)
d.text((66, 1483), "EN UNA TARDE.", font=font(86, "bold"), fill=BLUE)
d.text((66, 1608), "12 lecciones visuales  ·  40 minutos", font=font(34, "medium"), fill=PAPER)
d.text((66, 1662), "Sin código. Sin fórmulas. Sin relleno.", font=font(32, "regular"), fill=MUTED)
save(im, "03-solucion.png")


# 04 — Interactive proof.
im, d = base("04 / 06", 0.62)
proof = cover_crop(demo, 70, 980)
src = contain_frame(proof, (972, 1120))
mask = Image.new("L", src.size, 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, 971, 1119), radius=26, fill=255)
im.paste(src, (54, 430), mask)
d = ImageDraw.Draw(im)
d.rounded_rectangle((54, 430, 1026, 1550), radius=26, outline=HAIR, width=2)
tracked(d, (66, 174), "NO SOLO MIRAS", mono(14), BLUE, 3)
d.text((66, 218), "LO TOCAS.", font=font(76, "bold"), fill=PAPER)
d.text((66, 298), "LO ENTIENDES.", font=font(76, "bold"), fill=BLUE)
d.text((66, 1624), "Ejemplos interactivos que convierten", font=font(37, "regular"), fill=MUTED)
d.text((66, 1677), "conceptos difíciles en algo evidente.", font=font(37, "bold"), fill=PAPER)
save(im, "04-demo.png")


# 05 — Value stack, designed like the product's index.
im, d = base("05 / 06", 0.80)
tracked(d, (66, 174), "TODO INCLUIDO EN TU SUSCRIPCIÓN", mono(14), BLUE, 3)
d.text((66, 242), "DEJA DE", font=font(92, "bold"), fill=PAPER)
d.text((66, 336), "IMPROVISAR.", font=font(102, "bold"), fill=BLUE)
items = [
    ("01", "12 LECCIONES VISUALES", "Fundamentos que sí entiendes"),
    ("02", "36 LABS PARA PRACTICAR", "Aprender haciendo, no memorizando"),
    ("03", "9 PROMPTS LISTOS", "Copiar, ajustar y usar"),
    ("04", "ESPAÑOL + INGLÉS", "El contenido completo en ambos idiomas"),
    ("05", "ACTUALIZACIONES DEL VOL. 1", "Mientras tu suscripción esté activa"),
]
start = 590
for i, (n, title, body) in enumerate(items):
    y = start + i * 218
    d.text((66, y), n, font=mono(22), fill=BLUE)
    d.text((150, y - 8), title, font=fit(title, 840, 41, "bold"), fill=PAPER)
    d.text((150, y + 56), body, font=font(28, "regular"), fill=MUTED)
    d.line((66, y + 140, 1014, y + 140), fill=HAIR, width=1)
save(im, "05-valor.png")


# 06 — Offer and CTA, based on the real price panel.
im, d = base("06 / 06", 1.0)
offer_top = cover_crop(offer, 55, 780)
src = contain_frame(offer_top, (972, 720), PAPER)
mask = Image.new("L", src.size, 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, 971, 719), radius=28, fill=255)
im.paste(src, (54, 180), mask)
d = ImageDraw.Draw(im)
d.rounded_rectangle((54, 180, 1026, 900), radius=28, outline=(100, 100, 104), width=2)
tracked(d, (66, 990), "ACCESO INMEDIATO · CANCELAS CUANDO QUIERAS", mono(13), BLUE, 3)
d.text((66, 1065), "$35.000", font=font(156, "bold"), fill=PAPER)
d.text((70, 1228), "COP / MES", font=font(39, "medium"), fill=MUTED)
d.rounded_rectangle((66, 1340, 1014, 1520), radius=24, fill=PAPER)
cta = "EMPIEZA HOY"
cta_f = fit(cta, 840, 58, "bold")
tw = d.textbbox((0, 0), cta, font=cta_f)[2]
d.text(((W - tw) // 2, 1391), cta, font=cta_f, fill=BLACK)
d.text((66, 1600), "14 DÍAS DE GARANTÍA", font=font(40, "bold"), fill=PAPER)
d.text((66, 1660), "Si no es para ti, se devuelve completo.", font=font(30, "regular"), fill=MUTED)
d.line((66, 1760, 1014, 1760), fill=HAIR, width=1)
d.text((66, 1801), "LA IA NO SE VA A IR.  ENTENDERLA ES TU VENTAJA.", font=mono(17), fill=BLUE)
save(im, "06-oferta.png")

print("\n".join(str(p) for p in sorted(OUT.glob("*.png"))))
