"""
Lafz o Khayal — daily post generator.
Usage:
  python3 generate_post.py            -> picks poem by day of year (auto-rotation)
  python3 generate_post.py --id 7     -> renders a specific poem
"""
import json
import argparse
import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).parent
SIZE = 1080
CX = SIZE // 2

# ---- Theme: Ivory & Ink (matches profile picture pfp_roman_B_ivory) ----
BG_INNER = (248, 243, 231)   # warm ivory center
BG_OUTER = (233, 224, 203)   # aged paper edge
INK = (32, 42, 68)           # deep ink (frame / branding / shair text)
RED = (158, 62, 52)          # classical manuscript red (accents)
GOLD = INK
GOLD_BRIGHT = RED
GOLD_DIM = RED
TEXT_MAIN = INK

FONT_DISPLAY = str(BASE / "fonts" / "CormorantGaramond.ttf")


def font(px, wght=None, italic=False):
    f = ImageFont.truetype(FONT_DISPLAY, px)
    if wght:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    return f


def radial_bg():
    img = Image.new("RGB", (SIZE, SIZE), BG_OUTER)
    d = ImageDraw.Draw(img)
    for i in range(120, 0, -1):
        t = i / 120
        r = int(SIZE * 0.85 * t)
        col = tuple(int(BG_INNER[c] + (BG_OUTER[c] - BG_INNER[c]) * t) for c in range(3))
        d.ellipse([CX - r, CX - r, CX + r, CX + r], fill=col)
    return img


def wrap(d, text, f, max_width):
    """Word-wrap text to fit max_width."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_font(d, lines, max_width, start_px=64, min_px=40):
    """Find the largest font size where every wrapped line fits nicely."""
    px = start_px
    while px >= min_px:
        f = font(px, 560)
        wrapped = []
        ok = True
        for line in lines:
            ws = wrap(d, line, f, max_width)
            if len(ws) > 2:
                ok = False
                break
            wrapped.append(ws)
        if ok:
            return f, wrapped, px
        px -= 4
    f = font(min_px, 560)
    return f, [wrap(d, line, f, max_width) for line in lines], min_px


def text_center(d, text, f, fill, y, tracking=0):
    if tracking:
        widths = [d.textlength(ch, font=f) for ch in text]
        total = sum(widths) + tracking * (len(text) - 1)
        x = CX - total / 2
        for ch, w in zip(text, widths):
            d.text((x, y), ch, font=f, fill=fill)
            x += w + tracking
    else:
        bbox = d.textbbox((0, 0), text, font=f)
        d.text((CX - (bbox[2] - bbox[0]) / 2 - bbox[0], y), text, font=f, fill=fill)


def diamond(d, x, y, r, fill):
    d.regular_polygon((x, y, r), 4, rotation=0, fill=fill)


def render(poem, out_path):
    img = radial_bg()
    d = ImageDraw.Draw(img)

    # Frame: double rectangle border
    d.rectangle([40, 40, SIZE - 40, SIZE - 40], outline=GOLD, width=4)
    d.rectangle([58, 58, SIZE - 58, SIZE - 58], outline=GOLD_DIM, width=2)

    # Top ornament (red center diamond, ink sides — like the logo)
    diamond(d, CX, 130, 11, RED)
    diamond(d, CX - 44, 130, 6, INK)
    diamond(d, CX + 44, 130, 6, INK)
    d.line([CX - 190, 130, CX - 70, 130], fill=RED, width=2)
    d.line([CX + 70, 130, CX + 190, 130], fill=RED, width=2)

    # Shair text (auto-fit)
    max_w = SIZE - 240
    f_shair, wrapped, px = fit_font(d, poem["lines"], max_w)
    line_h = int(px * 1.42)
    gap_between_misras = int(px * 0.9)

    total_lines = sum(len(w) for w in wrapped)
    block_h = total_lines * line_h + gap_between_misras
    y = CX - block_h / 2 - 40

    for i, misra in enumerate(wrapped):
        for sub in misra:
            text_center(d, sub, f_shair, TEXT_MAIN, y)
            y += line_h
        if i == 0:
            y += gap_between_misras

    # Divider under shair
    y += 30
    d.line([CX - 120, y, CX - 30, y], fill=RED, width=2)
    diamond(d, CX, y, 6, INK)
    d.line([CX + 30, y, CX + 120, y], fill=RED, width=2)

    # Poet name
    f_poet = font(46, 600)
    text_center(d, "— " + poem["poet"] + " —", f_poet, RED, y + 34)

    # Bottom branding
    f_brand = font(34, 560)
    text_center(d, "L A F Z   o   K H A Y A L", f_brand, INK, SIZE - 150)
    f_handle = font(26, 500)
    text_center(d, "@lafz.o.khayal", f_handle, (120, 115, 100), SIZE - 105)

    img.save(out_path)
    return out_path


def make_caption(poem):
    lines = "\n".join(poem["lines"])
    return (
        f"{lines}\n\n"
        f"— {poem['poet']}\n\n"
        f"Meaning: {poem['meaning']}\n\n"
        f"#shayari #urdupoetry #hindipoetry #shairoshairee #rekhta "
        f"#{poem['poet'].split()[-1].lower()} #poetry #lafzokhayal #sher #ghazal"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", type=int, default=None)
    args = ap.parse_args()

    data = json.loads((BASE / "poetry.json").read_text(encoding="utf-8"))
    poems = data["poems"]

    if args.id:
        poem = next(p for p in poems if p["id"] == args.id)
    else:
        # rotate by day of year so each day gets the next poem automatically
        day = datetime.date.today().timetuple().tm_yday
        poem = poems[day % len(poems)]

    out = BASE / "output" / f"post_{poem['id']:03d}.png"
    out.parent.mkdir(exist_ok=True)
    render(poem, out)

    caption = make_caption(poem)
    (BASE / "output" / f"caption_{poem['id']:03d}.txt").write_text(caption, encoding="utf-8")
    print(f"Generated: {out}")
    print("\n--- Caption ---\n" + caption)
