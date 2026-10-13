"""Draws the port's own icon (a feather on a dusk-blue field) as .ico and .png. Needs Pillow.
The official game art is read from the player's dump at run time; this icon ships with the build.
usage: make_icon.py launcher/tlg.ico launcher/tlg.png"""
import math
import sys
from PIL import Image, ImageDraw, ImageFilter

S = 1024  # drawn large, scaled down for every icon size


def feather_points(cx, cy, length, width, angle, steps=90):
    """Outline of a feather vane: a pointed leaf shape along an axis tilted by `angle`."""
    left, right = [], []
    for i in range(steps + 1):
        t = i / steps
        # Wider near the lower third, pointed at the tip, narrow at the quill.
        half = width * math.sin(math.pi * t) ** 0.8 * (1.0 - 0.35 * t)
        along = (t - 0.5) * length
        left.append((along, -half))
        right.append((along, half))
    ca, sa = math.cos(angle), math.sin(angle)
    def place(p):
        x, y = p
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)
    return [place(p) for p in left + right[::-1]]


def draw():
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((24, 24, S - 24, S - 24), radius=190, fill=255)

    field = Image.new('RGBA', (S, S))
    fd = ImageDraw.Draw(field)
    for y in range(S):
        t = y / S
        fd.line((0, y, S, y), fill=(int(28 + 30 * t), int(52 + 22 * t), int(92 - 30 * t), 255))
    glow = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((180, 120, 844, 784), fill=(250, 214, 150, 90))
    field.alpha_composite(glow.filter(ImageFilter.GaussianBlur(110)))

    angle = math.radians(-58)
    feather = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    fe = ImageDraw.Draw(feather)
    fe.polygon(feather_points(512, 500, 700, 150, angle), fill=(242, 236, 224, 255))
    # Barbs: thin darker strokes across the vane.
    ca, sa = math.cos(angle), math.sin(angle)
    for i in range(-9, 10):
        along = i * 30
        bx, by = 512 + along * ca, 500 + along * sa
        for side in (-1, 1):
            reach = 120 * (1 - abs(i) / 11)
            ex = bx + (along * 0.0 + reach * 0.5) * ca - side * reach * sa
            ey = by + (reach * 0.5) * sa + side * reach * ca
            fe.line((bx, by, ex, ey), fill=(196, 186, 170, 255), width=6)
    # The shaft, running past the vane into the quill.
    x0, y0 = 512 - 420 * ca, 500 - 420 * sa
    x1, y1 = 512 + 340 * ca, 500 + 340 * sa
    fe.line((x0, y0, x1, y1), fill=(150, 120, 90, 255), width=16)

    shadow = Image.composite(Image.new('RGBA', (S, S), (0, 0, 0, 160)), Image.new('RGBA', (S, S), (0, 0, 0, 0)),
                             feather.getchannel('A')).filter(ImageFilter.GaussianBlur(20))
    field.alpha_composite(shadow, (10, 18))
    field.alpha_composite(feather)

    image = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    image.paste(field, (0, 0), mask)
    return image


def main():
    ico, png = sys.argv[1], sys.argv[2]
    image = draw()
    image.resize((256, 256), Image.LANCZOS).save(png)
    image.save(ico, sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])


if __name__ == '__main__':
    main()
