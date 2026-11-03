#!/usr/bin/env python3
"""Card: the steps every card agent repeats, as one command each, so an agent spends its time on the card itself.

  ve card <project> <id> --from <library card> --frames N --ground light|dark
      make cards/<id>/ ready to edit: the library card (yours in HOME/cards win on the same name; "dollar-split/
      index-followup.html" picks one of a card's compositions; no --from starts from kit/template.html), the style
      pack's brand.css and fonts, card.css, GSAP and hyperframes.json, with data-duration and the ground already set
      (no --ground keeps the starting card's own).
      An existing card folder is left alone unless --again.
  ve card <project> <id> --look t1,t2,...
      lint, a still at each card second, still.jpg (the last frame, 1080x1920) and sheet.jpg (every still in a row,
      labelled), and a check that nothing sits in the caption band (y 1170-1430) in any of them
  ve card <project> <id> --render
      render <id>.mp4 and check it is 1080x1920, 30fps and exactly the card's frame count
"""
import math
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FPS, HF, HOME, KIT, project_arg  # noqa: E402

BAND = (1170, 1430)                   # the caption band: ground only (kit/CARD_BRIEF.md)


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def library(name):
    """the library card's folder and the composition in it to start from"""
    folder, _, page = name.partition("/")
    for root in (os.path.join(HOME, "cards"), os.path.join(KIT, "cards")):
        if os.path.isdir(os.path.join(root, folder)):
            return os.path.join(root, folder), page or "index.html"
    have = sorted(d for d in os.listdir(os.path.join(KIT, "cards")) if os.path.isdir(os.path.join(KIT, "cards", d)))
    sys.exit(f"no library card called {folder}. The library: {', '.join(have)}")


def copy_in(src, dst):
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
    elif os.path.exists(src):
        shutil.copy(src, dst)


def frames_of(page):
    m = re.search(r'id="root"[^>]*data-duration="([\d.]+)"', open(page).read())
    return round(float(m.group(1)) * FPS) if m else None


def scaffold(project, cid, d):
    if os.path.exists(os.path.join(d, "index.html")) and "--again" not in sys.argv:
        sys.exit(f"{d} already has a card (--again starts it over)")
    frames = int(arg("--frames", "0")) or sys.exit("--frames N: the card's length in frames (its window x 30)")
    ground = arg("--ground")                            # none given: the starting card's own
    if ground not in (None, "light", "dark"):
        sys.exit("--ground light or dark")
    src = arg("--from")
    folder, page = library(src) if src and src != "none" else (None, None)
    os.makedirs(d, exist_ok=True)
    if folder:
        for f in os.listdir(folder):
            if f == "preview.jpg" or (f.startswith("index") and f.endswith(".html")):
                continue
            copy_in(os.path.join(folder, f), os.path.join(d, f))
        shutil.copy(os.path.join(folder, page), os.path.join(d, "index.html"))
    else:
        shutil.copy(os.path.join(KIT, "kit", "template.html"), os.path.join(d, "index.html"))
    style, pub = os.path.join(project, "style"), os.path.join(project, "public")
    copy_in(os.path.join(style, "brand.css"), d)
    copy_in(os.path.join(style, "fonts"), os.path.join(d, "fonts"))
    copy_in(os.path.join(KIT, "kit", "card.css"), d)
    copy_in(os.path.join(KIT, "kit", "hyperframes.json"), d)
    copy_in(os.path.join(pub, "vendor"), os.path.join(d, "vendor"))
    if not os.path.exists(os.path.join(d, "vendor", "gsap.min.js")):
        print("note: public/vendor/gsap.min.js isn't there yet (ve build puts it in): copy it in before --look")
    page = os.path.join(d, "index.html")
    html = open(page).read()
    if ground:
        html = re.sub(r'(<div id="root"[^>]*?)class="ground-(light|dark)"', rf'\1class="ground-{ground}"', html, count=1)
    ground = (re.search(r'<div id="root"[^>]*class="ground-(light|dark)"', html) or [None, "?"])[1]
    dur = math.floor(frames / FPS * 10000) / 10000      # rounded down: 10.167 s would render 306 frames, not 305
    html = re.sub(r'(<div id="root"[^>]*?)data-duration="[\d.]+"', rf'\g<1>data-duration="{dur:.4f}"', html, count=1)
    open(page, "w").write(html)
    ids = re.findall(r'<(?:div|svg|g|span|path|text|img)[^>]* id="([^"]+)"', html)
    print(f"cards/{cid}/ ready: {frames} frames ({frames / FPS:.3f}s), ground-{ground}, from {src or 'kit/template.html'}")
    print(f"elements with ids: {', '.join(ids[:40])}{' ...' if len(ids) > 40 else ''}")
    print(f"next: edit index.html, then ve card {project} {cid} --look <beat seconds>")


def look(project, cid, d):
    page = os.path.join(d, "index.html")
    n = frames_of(page) or sys.exit(f"no data-duration on #root in {page}")
    chk = subprocess.run(HF + ["check"], cwd=d, capture_output=True, text=True)
    errs = re.search(r"(\d+) error\(s\)", chk.stdout)
    print(f"lint: {errs.group(0) if errs else 'see below'}")
    if chk.returncode or (errs and errs.group(1) != "0"):
        print(chk.stdout[-1500:])
    ts = sorted({min(float(t), (n - 1) / FPS) for t in arg("--look").split(",") if t.strip()} | {(n - 1) / FPS})
    out = os.path.join(d, "look")
    shutil.rmtree(out, ignore_errors=True)
    r = subprocess.run(HF + ["snapshot", "--at", ",".join(f"{t:.3f}" for t in ts), "--no-end", "--describe", "false",
                             "-o", out], cwd=d, capture_output=True, text=True)
    pngs = sorted((os.path.join(out, f) for f in os.listdir(out) if f.endswith(".png")), key=os.path.getmtime) \
        if os.path.isdir(out) else []
    pngs = [p for p in pngs if "sheet" not in os.path.basename(p) and "contact" not in os.path.basename(p)]
    if len(pngs) != len(ts):
        sys.exit(f"snapshot gave {len(pngs)} stills for {len(ts)} times:\n{r.stdout[-800:]}{r.stderr[-800:]}")
    pngs = sorted(pngs, key=lambda p: float(re.findall(r"[\d.]+", os.path.basename(p))[0] or 0)
                  if re.findall(r"[\d.]+", os.path.basename(p)) else 0)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pngs[-1], "-q:v", "2", os.path.join(d, "still.jpg")], check=True)
    from PIL import Image, ImageDraw, ImageFont, ImageStat
    try:
        font = ImageFont.load_default(size=30)
    except TypeError:                                  # Pillow before 10.1
        font = ImageFont.load_default()
    tiles, busy = [], []
    for t, p in zip(ts, pngs):
        im = Image.open(p).convert("RGB").resize((1080, 1920))
        band = im.crop((0, BAND[0], 1080, BAND[1])).convert("L")
        if ImageStat.Stat(band).stddev[0] > 6:
            busy.append(f"{t:.2f}s")
        tile = im.resize((360, 640))
        ImageDraw.Draw(tile).text((12, 8), f"{t:.2f}s", fill=(255, 0, 255), font=font)
        tiles.append(tile)
    sheet = Image.new("RGB", (360 * len(tiles), 640))
    for k, tile in enumerate(tiles):
        sheet.paste(tile, (360 * k, 0))
    sheet.save(os.path.join(d, "sheet.jpg"), quality=88)
    print(f"stills at {', '.join(f'{t:.2f}s' for t in ts)} -> cards/{cid}/sheet.jpg, final frame -> cards/{cid}/still.jpg")
    print("caption band: " + (f"something sits in y {BAND[0]}-{BAND[1]} at {', '.join(busy)}: move it out" if busy
                             else "clear in every still"))
    print("now look at sheet.jpg and still.jpg yourself: reads in the order it's said, nothing twice, the hero wide")


def render(project, cid, d):
    n = frames_of(os.path.join(d, "index.html"))
    out = f"{cid}.mp4"
    args = ["render", "-q", "delivery", "--quiet", "-o", out]
    r = subprocess.run(HF + args + (["--gpu"] if sys.platform == "darwin" else []), cwd=d, capture_output=True, text=True)
    if r.returncode or not os.path.exists(os.path.join(d, out)):
        r = subprocess.run(HF + args, cwd=d, capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"render failed:\n{r.stdout[-1200:]}{r.stderr[-1200:]}")
    got = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate,nb_read_frames", "-of", "csv=p=0", os.path.join(d, out)],
                         capture_output=True, text=True).stdout.strip()
    want = f"1080,1920,30/1,{n}"
    print(f"cards/{cid}/{out}: {got}" + ("  OK" if got == want else f"  WRONG (want {want})"))
    shutil.rmtree(os.path.join(d, ".hyperframes", "artifacts"), ignore_errors=True)
    if got != want:
        sys.exit(1)


def main():
    project = project_arg()
    rest = [a for a in sys.argv[2:] if not a.startswith("--")]
    cid = rest[0] if rest else sys.exit(__doc__)
    d = os.path.join(project, "cards", cid)
    if "--look" in sys.argv:
        look(project, cid, d)
    elif "--render" in sys.argv:
        render(project, cid, d)
    else:
        scaffold(project, cid, d)


if __name__ == "__main__":
    main()
