#!/usr/bin/env python3
"""Render one SteadyDollar Short (1080x1920, 15 s) from a spec in specs.json.

Usage: python3 make_short.py <slug> [out.mp4]
Every Short ends on the same product card: Paycheck Budget Planner ($7).
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
W, H, FPS, DUR = 1080, 1920, 30, 15.0

NIGHT = (11, 29, 23); BLOB = (20, 52, 40); WHITE = (255, 255, 255)
INK = (15, 31, 26); GREEN = (34, 197, 94); SUN = (255, 212, 71)
LINE = (225, 232, 227); MUTED = (170, 190, 180); TOTALBG = (232, 247, 222); DKGREEN = (21, 128, 61)

PRODUCT = {
    "name": "Paycheck Budget Planner",
    "price": "$7",
    "url": "https://payhip.com/b/LEfx4",
    "image": os.path.join(REPO, "img", "budget.jpg"),
}


def font(weight, size):
    return ImageFont.truetype(os.path.join(HERE, "fonts", f"Inter-{weight}.otf"), size)


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def background():
    im = Image.new("RGB", (W, H), NIGHT)
    d = ImageDraw.Draw(im)
    d.ellipse((-420, -380, 600, 640), fill=BLOB)
    d.ellipse((450, 1120, 1500, 2170), fill=BLOB)
    return im


def fit_lines(d, lines, weight, max_size, max_w):
    size = max_size
    while size > 40:
        f = font(weight, size)
        if all(d.textlength(l, font=f) <= max_w for l in lines):
            return f
        size -= 4
    return font(weight, 40)


def draw_lines(d, lines, f, y, hi_from, gap=1.18):
    lh = int(f.size * gap)
    for i, l in enumerate(lines):
        col = SUN if i >= hi_from else WHITE
        d.text((W / 2, y + i * lh), l, font=f, fill=col, anchor="ma")
    return y + lh * len(lines)


def pill(d, cx, cy, text, f, bg, fg, padx=44, pady=26):
    tw = d.textlength(text, font=f)
    x0, x1 = cx - tw / 2 - padx, cx + tw / 2 + padx
    y0, y1 = cy - f.size / 2 - pady, cy + f.size / 2 + pady
    d.rounded_rectangle((x0, y0, x1, y1), radius=(y1 - y0) / 2, fill=bg)
    d.text((cx, cy), text, font=f, fill=fg, anchor="mm")


def frame(spec, t, bg, prod_img):
    im = bg.copy()
    d = ImageDraw.Draw(im)
    hook = spec["hook"]
    hi = spec.get("hook_hi", len(hook) - 1)
    small = font("Medium", 34)

    # Scene 1: hook, big and centred (0 - 2.6 s)
    if t < 2.6:
        f = fit_lines(d, hook, "Bold", 112, W - 120)
        total_h = int(f.size * 1.18) * len(hook)
        draw_lines(d, hook, f, (H - total_h) / 2 - 60, hi)
        d.text((W / 2, H - 240), "SteadyDollar", font=small, fill=MUTED, anchor="mm")
        return im

    # Scene 3: product end card (11 - 15 s)
    if t >= 11.0:
        a = ease((t - 11.0) / 0.5)
        top = 250 + int((1 - a) * 60)
        f1 = fit_lines(d, spec.get("end_hook", ["Plan your next paycheck", "in 5 minutes"]), "Bold", 84, W - 140)
        y = draw_lines(d, spec.get("end_hook", ["Plan your next paycheck", "in 5 minutes"]), f1, top, 99)
        pw = 820
        ph = int(prod_img.height * pw / prod_img.width)
        p = prod_img.resize((pw, ph))
        mask = Image.new("L", (pw, ph), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, pw, ph), radius=36, fill=255)
        py = y + 60
        im.paste(p, ((W - pw) // 2, py), mask)
        y = py + ph + 70
        d.text((W / 2, y), PRODUCT["name"], font=font("Bold", 64), fill=SUN, anchor="ma")
        d.text((W / 2, y + 90), "Excel + Google Sheets  ·  " + PRODUCT["price"], font=font("SemiBold", 42), fill=WHITE, anchor="ma")
        pulse = 1.0 + 0.04 * abs(((t * 1.6) % 2) - 1)
        pill(d, W / 2, y + 250, "Link in description", font("Bold", int(56 * pulse)), GREEN, INK)
        d.text((W / 2, H - 200), "SteadyDollar", font=font("Bold", 46), fill=SUN, anchor="mm")
        return im

    # Scene 2: the math card (2.6 - 11 s)
    f = fit_lines(d, hook, "Bold", 66, W - 160)
    y = draw_lines(d, hook, f, 200, hi)
    cx0, cx1 = 110, W - 110
    cy0 = y + 70
    rows = []
    if spec.get("income"):
        rows.append(spec["income"])
    rows += spec["rows"]
    row_h = 104
    head_h = 96
    n = len(rows)
    card_h = head_h + 24 + row_h * n + 150
    d.rounded_rectangle((cx0, cy0, cx1, cy0 + card_h), radius=34, fill=WHITE)
    d.rounded_rectangle((cx0, cy0, cx1, cy0 + head_h), radius=34, fill=GREEN)
    d.rectangle((cx0, cy0 + head_h - 34, cx1, cy0 + head_h), fill=GREEN)
    d.text((cx0 + 40, cy0 + head_h / 2), spec["sheet"], font=font("Bold", 40), fill=WHITE, anchor="lm")

    reveal_start, reveal_end = 3.0, 7.8
    step = (reveal_end - reveal_start) / max(n, 1)
    lf, vf = font("Medium", 42), font("Bold", 44)
    ry = cy0 + head_h + 24
    for i, (label, val) in enumerate(rows):
        a = ease((t - reveal_start - i * step) / 0.35)
        if a <= 0:
            break
        off = int((1 - a) * 30)
        col = tuple(int(255 - (255 - c) * a) for c in INK)
        d.text((cx0 + 40, ry + row_h / 2 + off), str(label), font=lf, fill=col, anchor="lm")
        d.text((cx1 - 40, ry + row_h / 2 + off), str(val), font=vf, fill=col, anchor="rm")
        d.line((cx0 + 30, ry + row_h, cx1 - 30, ry + row_h), fill=LINE, width=3)
        ry += row_h

    if t >= 8.0:
        a = ease((t - 8.0) / 0.4)
        ty = cy0 + head_h + 24 + row_h * n + 20
        d.rounded_rectangle((cx0 + 24, ty, cx1 - 24, ty + 110), radius=24, fill=TOTALBG)
        d.text((cx0 + 60, ty + 55), spec["total"][0], font=font("Bold", 46), fill=INK, anchor="lm")
        s = int(46 + 14 * a)
        d.text((cx1 - 60, ty + 55), str(spec["total"][1]), font=font("Bold", s), fill=DKGREEN, anchor="rm")
    if t >= 9.0 and spec.get("badge"):
        a = ease((t - 9.0) / 0.35)
        bf = fit_lines(d, [spec["badge"]], "Bold", 46, W - 260)
        pill(d, W / 2, cy0 + card_h + 90 + int((1 - a) * 40), spec["badge"], bf, SUN, INK, padx=40, pady=22)
    d.text((W / 2, H - 170), "Example numbers  ·  SteadyDollar", font=small, fill=MUTED, anchor="mm")
    return im


def render(spec, out):
    bg = background()
    prod = Image.open(PRODUCT["image"]).convert("RGB")
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cache = {}
    for i in range(int(DUR * FPS)):
        t = i / FPS
        # static stretches reuse the previous frame
        key = round(t, 2) if (2.6 <= t < 10.0 or 11.0 <= t) else ("hook" if t < 2.6 else "hold")
        if key not in cache:
            cache.clear()
            cache[key] = frame(spec, t, bg, prod).tobytes()
        p.stdin.write(cache[key])
    p.stdin.close()
    if p.wait() != 0:
        sys.exit("ffmpeg failed")


def main():
    slug = sys.argv[1]
    specs = json.load(open(os.path.join(HERE, "specs.json")))
    spec = next((s for s in specs if s["slug"] == slug), None)
    if not spec:
        sys.exit(f"no spec {slug}")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "video", "shorts", slug + ".mp4")
    render(spec, out)
    print(out)


if __name__ == "__main__":
    main()
