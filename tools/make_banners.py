"""
Renders the big pixel-art chapter banners for the quest book using Minecraft's own font texture,
so they look native but much larger than normal text.

Needs Pillow (any Python with PIL). Run:  <python-with-pillow> tools/make_banners.py
Writes kubejs/assets/economypack/textures/quests/*.png (KubeJS serves that folder as a resource pack).
Banner definitions (text, subtitle, colours) come from tools/quest_content.py (BANNERS).
"""
import io
import os
import sys
import zipfile

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import quest_content as C  # noqa: E402

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(PACK, 'kubejs', 'assets', 'economypack', 'textures', 'quests')
CLIENT_JAR = os.path.expanduser('~/Library/Application Support/PrismLauncher/libraries/com/mojang/minecraft/1.21.1/minecraft-1.21.1-client.jar')


def load_font():
    sheet = Image.open(io.BytesIO(zipfile.ZipFile(CLIENT_JAR).read('assets/minecraft/textures/font/ascii.png'))).convert('RGBA')
    glyphs = {}
    for code in range(32, 127):
        gx, gy = (code % 16) * 8, (code // 16) * 8
        g = sheet.crop((gx, gy, gx + 8, gy + 8))
        if code == 32:
            glyphs[' '] = (g, 4)
            continue
        cols = [x for x in range(8) if any(g.getpixel((x, y))[3] > 0 for y in range(8))]
        width = (max(cols) + 1) if cols else 4
        glyphs[chr(code)] = (g, width)
    return glyphs


FONT = load_font()


def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def text_mask(text, scale):
    """White-on-transparent mask of the text at an integer pixel scale (1 px gap between glyphs)."""
    width = sum(FONT.get(ch, FONT['?'])[1] + 1 for ch in text)
    img = Image.new('RGBA', (width, 8), (0, 0, 0, 0))
    x = 0
    for ch in text:
        g, w = FONT.get(ch, FONT['?'])
        img.alpha_composite(g, (x, 0))
        x += w + 1
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def gradient_fill(mask, top, bottom):
    """Colour a mask with a vertical gradient (pixel-stepped so it stays crisp)."""
    out = Image.new('RGBA', mask.size, (0, 0, 0, 0))
    t, b = hex_rgb(top), hex_rgb(bottom)
    px, mp = out.load(), mask.load()
    for y in range(mask.height):
        k = y / max(1, mask.height - 1)
        col = tuple(int(t[i] + (b[i] - t[i]) * k) for i in range(3))
        for x in range(mask.width):
            if mp[x, y][3]:
                px[x, y] = col + (255,)
    return out


def tint(mask, rgb):
    out = Image.new('RGBA', mask.size, (0, 0, 0, 0))
    px, mp = out.load(), mask.load()
    for y in range(mask.height):
        for x in range(mask.width):
            if mp[x, y][3]:
                px[x, y] = rgb + (255,)
    return out


def banner(title, subtitle, top, bottom, accent):
    big = text_mask(title, 6)
    small = text_mask(subtitle, 3) if subtitle else None
    pad = 18
    w = max(big.width, small.width if small else 0) + pad * 2
    h = big.height + (small.height + 10 if small else 0) + pad * 2 + 6
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))

    # Soft dark plate behind the text, with accent rules top and bottom.
    plate = Image.new('RGBA', (w, h), (16, 16, 24, 170))
    img.alpha_composite(plate)
    ar = hex_rgb(accent)
    for y in (0, 1, h - 2, h - 1):
        for x in range(w):
            img.putpixel((x, y), ar + (255,))

    bx = (w - big.width) // 2
    by = pad
    # Outline + drop shadow, then the gradient text.
    outline = tint(big, (20, 14, 8))
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
        img.alpha_composite(outline, (bx + dx, by + dy))
    img.alpha_composite(tint(big, (0, 0, 0)), (bx + 6, by + 6))
    img.alpha_composite(gradient_fill(big, top, bottom), (bx, by))

    if small:
        sx = (w - small.width) // 2
        sy = by + big.height + 14
        img.alpha_composite(tint(small, (0, 0, 0)), (sx + 3, sy + 3))
        img.alpha_composite(tint(small, hex_rgb(accent)), (sx, sy))
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    for key, b in C.BANNERS.items():
        img = banner(b['title'], b.get('subtitle', ''), b['top'], b['bottom'], b['accent'])
        img.save(os.path.join(OUT, f'{key}.png'))
        print(f'{key}.png {img.size}')


if __name__ == '__main__':
    main()
