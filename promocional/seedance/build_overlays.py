from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


WIDTH, HEIGHT = 1080, 1920
HERE = Path(__file__).resolve().parent
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
CYAN = (0, 225, 255, 255)
WHITE = (255, 255, 255, 255)


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def center_text(
    image: Image.Image,
    text: str,
    y: int,
    typeface: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    *,
    stroke: int = 4,
) -> None:
    draw = ImageDraw.Draw(image)
    box = draw.textbbox((0, 0), text, font=typeface, stroke_width=stroke)
    x = (WIDTH - (box[2] - box[0])) // 2
    draw.text(
        (x, y),
        text,
        font=typeface,
        fill=fill,
        stroke_width=stroke,
        stroke_fill=(0, 0, 0, 220),
    )


def glow_line(image: Image.Image, y: int, width: int = 148) -> None:
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    x0 = (WIDTH - width) // 2
    g.rounded_rectangle((x0, y, x0 + width, y + 8), radius=4, fill=CYAN)
    image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14)))
    image.alpha_composite(glow)


def pill(
    image: Image.Image,
    text: str,
    y: int,
    *,
    typeface: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int] = WHITE,
) -> None:
    draw = ImageDraw.Draw(image)
    box = draw.textbbox((0, 0), text, font=typeface)
    tw, th = box[2] - box[0], box[3] - box[1]
    pad_x, pad_y = 34, 22
    x0 = (WIDTH - tw - pad_x * 2) // 2
    draw.rounded_rectangle(
        (x0, y, x0 + tw + pad_x * 2, y + th + pad_y * 2),
        radius=28,
        fill=(2, 12, 18, 198),
        outline=(0, 225, 255, 180),
        width=2,
    )
    draw.text((x0 + pad_x, y + pad_y - box[1]), text, font=typeface, fill=fill)


def base() -> Image.Image:
    return Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))


def brand(image: Image.Image) -> None:
    center_text(image, "AI FROM SCRATCH", 76, font(BOLD, 30), CYAN, stroke=2)
    glow_line(image, 130, 112)


def scene_one() -> Image.Image:
    image = base()
    brand(image)
    center_text(image, "LA IA YA", 180, font(BOLD, 78), WHITE)
    center_text(image, "CAMBIÓ TODO", 270, font(BOLD, 82), CYAN)
    pill(image, "NO TE QUEDES ATRÁS", 405, typeface=font(BOLD, 31))
    return image


def scene_two() -> Image.Image:
    image = base()
    brand(image)
    center_text(image, "APRENDE IA", 180, font(BOLD, 80), WHITE)
    center_text(image, "DESDE CERO", 274, font(BOLD, 86), CYAN)
    pill(image, "PASO A PASO  ·  SIN TECNICISMOS", 410, typeface=font(BOLD, 27))
    return image


def scene_three() -> Image.Image:
    image = base()
    brand(image)
    center_text(image, "TU MOMENTO", 165, font(BOLD, 77), WHITE)
    center_text(image, "ES AHORA", 255, font(BOLD, 88), CYAN)

    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle((132, 1510, 948, 1662), radius=52, fill=(0, 225, 255, 190))
    image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(24)))

    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((132, 1510, 948, 1662), radius=52, fill=CYAN)
    cta_font = font(BOLD, 47)
    cta = "SUSCRÍBETE AHORA"
    box = draw.textbbox((0, 0), cta, font=cta_font)
    draw.text(
        ((WIDTH - (box[2] - box[0])) // 2, 1562 - box[1]),
        cta,
        font=cta_font,
        fill=(0, 14, 20, 255),
    )
    center_text(image, "EMPIEZA HOY · AVANZA A TU RITMO", 1708, font(BOLD, 27), WHITE, stroke=3)
    return image


for filename, image in (
    ("overlay-01.png", scene_one()),
    ("overlay-02.png", scene_two()),
    ("overlay-03.png", scene_three()),
):
    image.save(HERE / filename)
    print(HERE / filename)
