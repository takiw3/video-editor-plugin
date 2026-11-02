#!/usr/bin/env python3
"""The verified effects library on a reel page: one edit.py field, every effect routed to the right place by itself.

edit.FXLIB is a list of dicts. The agent names the effect, the moment and the settings; this file works out the rest
from the effect's route, which is the part that goes wrong when done by hand:

    FXLIB = [
        dict(effect="film-grain", params=dict(amount=0.15)),               # no window: the whole video
        dict(effect="digital-glitch", at=5.55, duration=0.35),             # a look or treatment for a moment
        dict(effect="crash-zoom", at=12.0, duration=0.6),                  # camera: carries footage and graphics together
        dict(effect="confetti-burst", at=40.0, duration=1.8),              # overlay: above the footage, under the captions
        dict(effect="word-pop", text="Three things", at=2, duration=2),    # text: makes its own element, in the pack's look
        dict(effect="lower-third", at=3.0, duration=3, text="Sam Lee|Founder"),
        dict(effect="split-screen-stack", src="media/screen.mp4", at=8, duration=4),   # layouts: src is the second layer
    ]

Transitions (the scene-pair effects) go in edit.TRANSITIONS and are pre-rendered by transitions.py.
Audio effects go in edit.AUDIO_FX and are applied by mix.py.

The library itself (effects-library/) is the verified set from the Hermes video editor. Its tool, fx.py, is used
unchanged; this file points it at the reel page and keeps the reel page's rules:
  - the page builds its GSAP timeline in one script, so HFX.run moves just before the timeline registers
  - looks live on the <video> as one attribute, so a look with a window gets its own synced copy of the footage,
    and any cutout playing in that window gets the same treatment so the speaker never changes colour against the room
  - camera effects go on #fxcam, a wrapper around the page's own #cam, so they stack with the page's zooms
  - overlays and text go in #fxunder, above the footage and under the captions
"""
import contextlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
LIB = os.path.join(KIT, "effects-library")
sys.path.insert(0, os.path.join(LIB, "scripts"))
import fx  # noqa: E402  the library's own tool
from pathlib import Path  # noqa: E402

HOME = os.path.expanduser(os.environ.get("VIDEO_EDITOR_HOME", "~/video-editor"))
fx.find_project = lambda arg: Path(arg).expanduser().resolve()      # a reel's public/ folder, not a Hermes workspace
fx.LOCAL_EFFECTS = Path(HOME) / "effects"                           # the creator's own verified effects
fx.LOCAL_RECIPES = Path(HOME) / "effect-recipes"
fx.shader_source = lambda: Path(HOME) / "vendor" / "hyper-shader.js"
fx.pin = lambda: {"npm_version": "0.8.183"}

GRADE_ROUTES = {"hf-media-treatment", "hf-color-grade"}
FOOTAGE = "#v"
CAMERA = "#fxcam"
UNDER = "#fxunder"
COPY_STYLE = "position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover;"
# these take a colour from the creator's pack instead of their default, and a position from the shoot
HUE_PARAMS = {"progress-bar": "hue", "lower-third": "hue", "dip-to-colour": "hue", "callout-box": "hue", "screen-frame": "hue",
              "light-leak-glow": "hue", "highlight-sweep": "hue", "gradient-wash": "hue"}
FACE_PARAMS = {"spotlight-focus", "punch-in"}
ON_THE_FOOTAGE = {"screen-frame"}


def spec_of(effect):
    specs = fx.library()
    if effect not in specs:
        close = [k for k in specs if effect.replace("_", "-") in k or k in effect][:3]
        raise SystemExit(f"FXLIB: there is no effect called {effect!r}" + (f". Closest: {', '.join(close)}" if close else ""))
    return specs[effect]


def pack_defaults(E, effect, params):
    """settings the creator's pack and shoot can answer: the accent colour, where the face is. An explicit value wins."""
    out = dict(params or {})
    hue_key = HUE_PARAMS.get(effect)
    if hue_key and hue_key not in out:
        h = hex_to_hue(((getattr(E, "S", None) or {}).get("colors") or {}).get("accent"))
        if h is not None:
            out[hue_key] = h
    if effect in FACE_PARAMS:
        x, y = getattr(E, "FACE", None) or getattr(E, "CAM_ORIGIN", None) or (540, 760)
        W, H = getattr(E, "CANVAS", (1080, 1920))
        out.setdefault("cx", round(x / W, 3))
        out.setdefault("cy", round(y / H, 3))
    return out


def kind_of(spec):
    return spec.get("target", "wrapper"), spec["implementation_route"]


def hex_to_hue(color):
    if not color:
        return None
    m = re.fullmatch(r"#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})", (color or "").strip())
    if not m:
        return None
    import colorsys
    r, g, b = (int(x, 16) / 255 for x in m.groups())
    return round(colorsys.rgb_to_hsv(r, g, b)[0] * 360)


def _argv(project, inst):
    a = [str(project), "--effect", inst["effect"]]
    for key, flag in (("target", "--target"), ("frm", "--from"), ("to", "--to"), ("container", "--container"), ("iid", "--iid")):
        if inst.get(key):
            a += [flag, inst[key]]
    if inst.get("at") is not None:
        a += ["--at", f"{float(inst['at']):.3f}"]
    if inst.get("duration") is not None:
        a += ["--duration", f"{float(inst['duration']):.3f}"]
    for k, v in (inst.get("params") or {}).items():
        a += ["--param", f"{k}={v}"]
    for spec in inst.get("animate") or []:
        a += ["--animate", spec]
    return a


def _attr(tag, name):
    m = re.search(rf'\s{name}="([^"]*)"', tag)
    return m.group(1) if m else None


def _video_tag(text, vid):
    return re.search(rf'<video\b[^>]*\sid="{re.escape(vid)}"[^>]*>(\s*</video>)?', text)


def _copy_in_window(text, vid, cid, at, dur, track_bump, style=None):
    """a synced copy of a <video> that plays only inside [at, at+dur], right after the original in the page"""
    m = _video_tag(text, vid)
    tag = m.group(0)
    start = float(_attr(tag, "data-start") or 0)
    media0 = float(_attr(tag, "data-media-start") or 0)
    track = int(_attr(tag, "data-track-index") or 0)
    cls = _attr(tag, "class") or ""
    copy = (f'\n      <video id="{cid}" class="{cls}" src="{_attr(tag, "src")}" muted playsinline data-start="{at:.4f}" '
            f'data-media-start="{at - start + media0:.4f}" data-duration="{dur:.4f}" data-track-index="{track + track_bump}" '
            f'style="{style or COPY_STYLE}"></video>')
    end = m.end() if tag.endswith("</video>") else text.index("</video>", m.end()) + len("</video>")
    return text[:end] + copy + text[end:]


def _cutouts(text):
    """(id, start, end) of each cutout <video> on the page"""
    out = []
    for m in re.finditer(r'<video id="(s\d+)"[^>]*src="subject\.webm"[^>]*>', text):
        a = float(_attr(m.group(0), "data-start"))
        out.append((m.group(1), a, a + float(_attr(m.group(0), "data-duration"))))
    return out


def _span(at, dur, total):
    a = float(at or 0)
    return a, a + float(dur or total - a)


def _show(el, w0, w1):
    return f"gsap.set('#{el}', {{ opacity: 0 }}); tl.set('#{el}', {{ opacity: 1 }}, q({w0:.3f})); tl.set('#{el}', {{ opacity: 0 }}, q({w1:.3f}));"


def _media(el, F, w0, w1, track, full=True):
    """the creator's clip or photo as its own layer: full frame, or placed with x, y, w, h"""
    if full:
        style = COPY_STYLE + "opacity:0;"
    else:
        style = (f'position:absolute;left:{F.get("x", 60)}px;top:{F.get("y", 300)}px;width:{F.get("w", 960)}px;'
                 f'height:{F.get("h", 640)}px;object-fit:cover;opacity:0;')
    if F["src"].endswith((".mp4", ".mov", ".webm")):
        return (f'<video id="{el}" src="{F["src"]}" muted playsinline data-start="{w0:.4f}" data-media-start="{F.get("media_start", 0):.4f}" '
                f'data-duration="{w1 - w0:.4f}" data-track-index="{track}" style="{style}"></video>')
    return f'<img id="{el}" src="{F["src"]}" style="{style}">'


def plan(E, instances, text):
    """FXLIB entries -> the exact fx.py calls and the page changes they need. Pure routing, no writes except `text`."""
    out = []
    whole_looks = []
    extra_html, extra_js = [], []
    timed = []
    total = float(fx.root_info(text)["duration"])
    for n, entry in enumerate(instances):
        F = dict(entry)
        spec = spec_of(F["effect"])
        target, route = kind_of(spec)
        at, dur = F.get("at"), F.get("duration")
        if F.get("end") is not None and at is not None:
            dur = float(F["end"]) - float(at)
        params = pack_defaults(E, F["effect"], F.get("params"))
        base = dict(effect=F["effect"], at=at, duration=dur, params=params, animate=F.get("animate"), iid=F.get("iid"))
        if target == "audio":
            raise SystemExit(f"FXLIB: {F['effect']} is an audio effect. Put it in AUDIO_FX; mix.py applies it.")
        if target == "scene-pair":
            raise SystemExit(f"FXLIB: {F['effect']} is a transition. Put it in TRANSITIONS, on the cut it belongs to.")
        if route in GRADE_ROUTES:                                  # media: one attribute on the <video>
            if at is None and dur is None:
                whole_looks.append(dict(base, target=FOOTAGE))
                for sid, a, b in _cutouts(text):
                    whole_looks.append(dict(base, target=f"#{sid}", at=a, duration=b - a, iid=None))
            else:
                timed.append(dict(base, at=float(at or 0), duration=float(dur or total - float(at or 0))))
        elif target == "overlay":
            out.append(dict(base, container=UNDER))
        elif target == "text":
            if not F.get("text"):
                raise SystemExit(f"FXLIB: {F['effect']} needs text=\"...\": the words it animates")
            tid = f"fxt{n}"
            style = (f'position:absolute;left:{F.get("x", 60)}px;top:{F.get("y", 300)}px;width:{F.get("w", 960)}px;'
                     f'text-align:{F.get("align", "center")};font-family:var(--font-display);font-style:var(--display-style);'
                     f'font-weight:var(--display-weight);font-size:{F.get("size", 110)}px;line-height:1.02;'
                     f'color:{F.get("color", "var(--c-light)")};text-shadow:0 3px 22px rgba(0,0,0,.42);opacity:0;')
            extra_html.append(f'<div id="{tid}" data-layout-allow-overlap data-layout-allow-occlusion style="{style}">{F["text"]}</div>')
            w0 = float(at or 0)
            w1 = w0 + float(dur or total - w0)
            extra_js.append(f"tl.set('#{tid}', {{ opacity: 1 }}, q({w0:.3f})); tl.set('#{tid}', {{ opacity: 0 }}, q({w1:.3f}));")
            out.append(dict(base, target=f"#{tid}"))
        elif F["effect"] == "blur-fill-reframe":                   # one piece of media over a blurred copy of itself
            if not F.get("src"):
                raise SystemExit('FXLIB: blur-fill-reframe needs src="media/...": the landscape clip or image to fit into the frame')
            w0, w1 = _span(at, dur, total)
            extra_html.append(_media(f"fxm{n}", F, w0, w1, 500 + 2 * n, full=True))
            extra_html.append(_media(f"fxn{n}", F, w0, w1, 501 + 2 * n, full=True))
            extra_js.append(_show(f"fxm{n}", w0, w1))
            out.append(dict(base, target=f"#fxm{n}", to=f"#fxn{n}"))
        elif target == "composite":                                # a layout: the footage plus a second layer
            if not F.get("src"):
                raise SystemExit(f"FXLIB: {F['effect']} arranges two layers and needs src=\"media/...\": the second one")
            w0, w1 = _span(at, dur, total)
            extra_html.append(_media(f"fxm{n}", F, w0, w1, 500 + n, full=True))
            out.append(dict(base, target=CAMERA, to=f"#fxm{n}"))
        elif F.get("src"):                                         # any move or frame on their own clip or photo
            w0, w1 = _span(at, dur, total)
            extra_html.append(_media(f"fxm{n}", F, w0, w1, 500 + n, full=not {"x", "y", "w", "h"} & set(F)))
            extra_js.append(_show(f"fxm{n}", w0, w1))
            out.append(dict(base, target=f"#fxm{n}", container=UNDER))
        else:                                                      # wrapper: camera moves, filters, callouts
            family = spec.get("family")
            has_markup = os.path.exists(os.path.join(spec["_dir"], "markup.html"))
            if F["effect"] in ON_THE_FOOTAGE:                      # transforms the footage, adds its own markup
                out.append(dict(base, target=CAMERA, container=UNDER))
            elif family in ("camera-and-motion", "image-effects", "looks-and-grades", "keying-and-subject") and not has_markup:
                out.append(dict(base, target=CAMERA))
            elif has_markup:                                       # lower thirds, callouts, tilt-shift: above the footage, under the captions
                out.append(dict(base, target=UNDER, container=UNDER))
                if F.get("text"):
                    out[-1]["_text"] = F["text"]
            else:
                out.append(dict(base, target=CAMERA))
    return whole_looks, timed, out, extra_html, extra_js


def apply(E, pub, quiet=True):
    """E.FXLIB onto <pub>/index.html (already written by build.py). No FXLIB: the page stays as it is."""
    instances = getattr(E, "FXLIB", []) or []
    (Path(pub) / fx.INSTANCES).unlink(missing_ok=True)
    if not instances:
        return []
    index = Path(pub) / "index.html"
    text = index.read_text(encoding="utf-8")
    whole, timed, rest, extra_html, extra_js = plan(E, instances, text)
    if extra_html:
        text = text.replace('<!-- fxunder-end -->', "\n".join(extra_html) + '\n<!-- fxunder-end -->', 1)
    if extra_js:
        text = text.replace("// ---- captions", "\n  ".join(extra_js) + "\n  // ---- captions", 1)
    copies = []
    for k, inst in enumerate(timed):                                # a look for a moment: its own synced copy
        a, d = inst["at"], inst["duration"]
        cid = f"vfx{k}"
        text = _copy_in_window(text, "v", cid, a, d, 40 + k)
        copies.append(dict(inst, target=f"#{cid}"))
        for w in whole:                                             # keep the whole-video looks on the copy too
            if w["target"] == FOOTAGE:
                copies.append(dict(w, target=f"#{cid}", at=a, duration=d, iid=None))
        for sid, sa, sb in _cutouts(text):                          # a cutout inside the window gets the same look
            x0, x1 = max(a, sa), min(a + d, sb)
            if x1 - x0 > 0.01:
                scid = f"sfx{k}{sid}"
                text = _copy_in_window(text, sid, scid, x0, x1 - x0, 60 + k)
                copies.append(dict(inst, target=f"#{scid}", at=x0, duration=x1 - x0, iid=None))
    index.write_text(text, encoding="utf-8")
    results, labels = [], []
    for inst in whole + copies + rest:
        label = inst.pop("_text", None)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                fx.cmd_apply(_argv(pub, inst))
        except SystemExit as e:
            raise SystemExit(f"FXLIB: the library refused {inst['effect']} ({buf.getvalue().strip()[-300:] or e.code})")
        results.append(json.loads(buf.getvalue()))
        if label:
            labels.append((results[-1]["iid"], label))
    for iid, label in labels:                                       # the library rewrites its markup on each apply: last
        _set_label(index, iid, label)
    _reel_safe(index)
    text = index.read_text(encoding="utf-8")
    m = re.search(r'HFX\.run\(window\.__timelines\["[^"]+"\], (.*?)\);\n\s*</script>', text, re.S)
    if m:
        payload = m.group(1)
        text = fx.strip_block(text, "run")
        hook = "window.__timelines['main'] = tl;"
        if hook not in text:
            raise SystemExit("fxlib: the page has no timeline registration line to run the effects from")
        text = text.replace(hook, f"HFX.run(tl, {payload});\n  {hook}", 1)
    index.write_text(text, encoding="utf-8")
    _brand_scripts(E, pub)
    return results


def _set_label(index, iid, label):
    """lower-third and callout text comes from text="Name|Role", in the page rather than the effect's placeholder"""
    text = index.read_text(encoding="utf-8")
    parts = [p.strip() for p in str(label).split("|")]
    block = re.search(rf"<!-- fx:overlay {iid} -->.*?<!-- /fx:overlay {iid} -->", text, re.S)
    if not block:
        return
    body = block.group(0).replace("Name here", parts[0]).replace("Role here", parts[1] if len(parts) > 1 else "")
    body = re.sub(r"Callout|Label here", parts[0], body)
    index.write_text(text[:block.start()] + body + text[block.end():], encoding="utf-8")


def _reel_safe(index):
    """the library's lower third sits at 10% from the bottom, under the app's buttons on a vertical video: lift it to
    just above the captions"""
    text = index.read_text(encoding="utf-8")
    text2 = re.sub(r'(class="fx-\w+-bar" style="position:absolute;left:5%;)bottom:10%', r"\1bottom:34%", text)
    text2 = text2.replace("font:700 11px/1.4 Helvetica,Arial,sans-serif", "font:700 30px/1.3 var(--font-text),sans-serif")   # callout tag: phone-size
    if text2 != text:
        index.write_text(text2, encoding="utf-8")


def _brand_scripts(E, pub):
    """effect scripts carry a default palette: in the project's copy, swap it for the creator's colours"""
    C = (getattr(E, "S", None) or {}).get("colors")
    if not C:
        return
    js = Path(pub) / "assets" / "fx" / "confetti-burst.js"
    if js.is_file():
        src = js.read_text(encoding="utf-8")
        pal = [C["accent"], C["light"], C.get("positive", C["accent"]), C["accent"], C["light"]]
        src = re.sub(r'\[\s*"#[0-9A-Fa-f]{6}"(?:\s*,\s*"#[0-9A-Fa-f]{6}")+\s*\]', json.dumps(pal), src, count=1)
        js.write_text(src, encoding="utf-8")


def main():
    print(__doc__)


if __name__ == "__main__":
    main()
