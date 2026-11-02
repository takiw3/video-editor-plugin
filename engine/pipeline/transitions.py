#!/usr/bin/env python3
"""Transitions: every transition in the library on a real cut of a talking-head video.

The library's 27 transitions need two scenes. A reel is one continuous picture, so a transition is pre-rendered as its
own short clip and hard-cut over the footage for exactly its window, under the captions and the top graphics:

    TRANSITIONS = [
        dict(effect="whip-pan", at=12.30),                     # at = the picture cut it sits on
        dict(effect="zoom-through", at=25.60, duration=0.5),
        dict(effect="dip-to-colour", at=40.10, params=dict(hue=14)),
    ]

The clip plays the outgoing shot up to the cut and holds its last frame, the incoming shot holds its first frame and
then plays. The hold sits inside the moving part of the transition, so it doesn't read as a freeze. The voice runs
underneath untouched, so lip sync can't move. Rendered clips are cached by their settings.

Run: ve transitions <project>
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FPS, HOME, VENDOR, hf, load_edit, project_arg, q, timeline  # noqa: E402
import fxlib  # noqa: E402
import style as ST  # noqa: E402

fx = fxlib.fx
HOLD_PAD = 2 / FPS


def page(W, H, dur):
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>transition</title>
<style>html,body{{margin:0;background:#000}} .scene{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;background-color:#000000;overflow:hidden}}
video{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;object-fit:cover}}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur:.4f}" data-fps="{FPS}" data-width="{W}" data-height="{H}" style="position:relative;width:{W}px;height:{H}px;overflow:hidden">
  <div id="sa" class="scene" style="background-color:#000000"><video id="va" src="a.mp4" muted playsinline data-start="0" data-media-start="0" data-duration="{dur:.4f}" data-track-index="1"></video></div>
  <div id="sb" class="scene" style="background-color:#000000"><video id="vb" src="b.mp4" muted playsinline data-start="0" data-media-start="0" data-duration="{dur:.4f}" data-track-index="2"></video></div>
</div>
<script src="vendor/gsap.min.js"></script>
<script>
  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{ paused: true }});
  tl.set({{}}, {{}}, {dur:.4f});
  window.__timelines["main"] = tl;
</script>
</body></html>
"""


def slice_shots(clean, at, half, adir):
    """a.mp4: the outgoing shot up to the cut, last frame held. b.mp4: the incoming shot's first frame held, then playing."""
    d = 2 * half
    n_a = round(half * FPS)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, at - half):.4f}", "-t", f"{half:.4f}", "-i", clean,
                    "-vf", f"tpad=stop_mode=clone:stop_duration={half + HOLD_PAD:.4f},fps={FPS}", "-an",
                    "-c:v", "libx264", "-crf", "12", "-preset", "veryfast", "-g", "1", "-pix_fmt", "yuv420p",
                    os.path.join(adir, "a.mp4")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.4f}", "-t", f"{half + HOLD_PAD:.4f}", "-i", clean,
                    "-vf", f"tpad=start_mode=clone:start_duration={half:.4f},fps={FPS}", "-an",
                    "-c:v", "libx264", "-crf", "12", "-preset", "veryfast", "-g", "1", "-pix_fmt", "yuv420p",
                    os.path.join(adir, "b.mp4")], check=True)
    return d, n_a


def key_of(project, T, E):
    """the cache key: anything that changes the picture of this clip"""
    clean = os.path.join(project, "public", "clean.mp4")
    return hashlib.sha1(json.dumps([T.get("effect"), T.get("at"), T.get("duration"), fxlib.pack_defaults(E, T["effect"], T.get("params")),
                                    os.path.getsize(clean), int(os.path.getmtime(clean))], sort_keys=True).encode()).hexdigest()[:10]


def duration_of(T, spec):
    return q(float(T.get("duration") or spec.get("default_duration") or 0.6))


def window(T, spec):
    """the clip's [start, end] on the output timeline, frame-exact and centred on the cut"""
    d = duration_of(T, spec)
    half = round(d * FPS / 2) / FPS
    a = q(float(T["at"])) - half
    return a, a + 2 * half, half


def clip_name(T, i):
    return f"tr{i:02d}-{T['effect']}.mp4"


def render_one(project, E, T, i):
    spec = fxlib.spec_of(T["effect"])
    if spec.get("target") != "scene-pair":
        raise SystemExit(f"TRANSITIONS: {T['effect']} isn't a transition. It belongs in FXLIB.")
    W, H = E.CANVAS
    a, b, half = window(T, spec)
    if a < 0:
        raise SystemExit(f"TRANSITIONS: {T['effect']} at {T['at']} starts before the video does: move it past {half:.2f}s")
    key = key_of(project, T, E)
    out_dir = os.path.join(project, "public", "tr")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, clip_name(T, i))
    stamp = out + ".key"
    if os.path.exists(out) and os.path.exists(stamp) and open(stamp).read() == key:
        return out, a, b, False
    work = os.path.join(project, "work", "tr", f"{i:02d}")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(os.path.join(work, "vendor"))
    shutil.copy(os.path.join(VENDOR, "gsap.min.js"), os.path.join(work, "vendor", "gsap.min.js"))
    clean = os.path.join(project, "public", "clean.mp4")
    slice_shots(clean, q(float(T["at"])), half, work)
    d = b - a
    with open(os.path.join(work, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page(W, H, d))
    args = [work, "--effect", T["effect"], "--from", "#sa", "--to", "#sb", "--at", "0.000", "--duration", f"{d:.4f}"]
    for k, v in fxlib.pack_defaults(E, T["effect"], T.get("params")).items():
        args += ["--param", f"{k}={v}"]
    import contextlib
    import io
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            fx.cmd_apply(args)
    except SystemExit as e:
        raise SystemExit(f"TRANSITIONS: the library refused {T['effect']} ({buf.getvalue().strip()[-300:] or e.code})")
    _finish_page(work)
    _brand_shader(work, E)
    hf(["render", "-q", "delivery", "--quiet", "-o", "out.mp4"], work)
    shutil.copy(os.path.join(work, "out.mp4"), out)
    with open(stamp, "w") as fh:
        fh.write(key)
    return out, a, b, True


def _brand_shader(work, E):
    """the shader transitions burn through to one accent colour: the creator's, not white"""
    accent = ((getattr(E, "S", None) or {}).get("colors") or {}).get("accent")
    index = os.path.join(work, "index.html")
    text = open(index, encoding="utf-8").read()
    if accent and '"accentColor": "#ffffff"' in text:
        open(index, "w", encoding="utf-8").write(text.replace('"accentColor": "#ffffff"', f'"accentColor": "{accent}"'))


def _finish_page(work):
    """the same move as fxlib: HFX.run before the timeline registers"""
    index = os.path.join(work, "index.html")
    text = open(index, encoding="utf-8").read()
    m = re.search(r'HFX\.run\(window\.__timelines\["[^"]+"\], (.*?)\);\n\s*</script>', text, re.S)
    if m:
        payload = m.group(1)
        text = fx.strip_block(text, "run")
        text = text.replace('window.__timelines["main"] = tl;', f'HFX.run(tl, {payload});\n  window.__timelines["main"] = tl;', 1)
        open(index, "w", encoding="utf-8").write(text)


def entries(E):
    """[(T, index, start, end, published path)] for build.py: the clip goes in once it exists"""
    out = []
    for i, T in enumerate(getattr(E, "TRANSITIONS", []) or []):
        spec = fxlib.spec_of(T["effect"])
        a, b, _ = window(T, spec)
        out.append((T, i, a, b, f"tr/{clip_name(T, i)}"))
    return out


def main():
    project = project_arg()
    E = load_edit(project)
    E.S = ST.load(os.path.join(project, "style", "style.json"))
    TL = timeline(project)
    items = getattr(E, "TRANSITIONS", []) or []
    if not items:
        print("no TRANSITIONS in edit.py")
        return
    cuts = TL.get("picture_cuts", []) + TL.get("reframes", [])
    for i, T in enumerate(items):
        near = min((abs(c - float(T["at"])) for c in cuts), default=99)
        if near > 0.05:
            print(f"note: {T['effect']} at {T['at']} isn't on a picture cut (nearest is {near:.2f}s away): it plays over a single shot")
        out, a, b, made = render_one(project, E, T, i)
        print(f"{'rendered' if made else 'cached  '} {os.path.basename(out)}  {a:.3f}-{b:.3f}", flush=True)


if __name__ == "__main__":
    main()
