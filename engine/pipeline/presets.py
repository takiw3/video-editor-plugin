#!/usr/bin/env python3
"""Style presets: a complete, good-looking style pack in one command, for anyone without a brand guide.

    ve style --list
    ve style --preset bold [--accent "#FD5323"] [--name "Sam"] [--handle "@sam"] [--site sam.co]
    ve style                                      regenerates brand.css and fonts from the current style.json

Writes $VIDEO_EDITOR_HOME/style/style.json and STYLE.md, then brand.css and fonts. Any colour the creator gives becomes the
accent, with a darker shade worked out for light backgrounds. An existing pack is kept as style.backup.json.
"""
import colorsys
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import KIT  # noqa: E402
import style as ST  # noqa: E402

PACKS = os.path.join(KIT, "examples", "packs")
BLURB = {
    "default": "neutral and clean, a safe start",
    "bold": "loud, heavy type, one strong colour, fast",
    "soft": "warm serif, rounded corners, friendly",
    "editorial": "magazine feel, elegant serif, calm pace",
    "minimal": "quiet and modern, lots of space",
    "tech": "dark, sharp, mono details, for AI and software",
}


def shade(hex_color, factor):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(h, max(0, min(1, l * factor)), s)
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def fit(C):
    """make any brand colour work: the brand colour stays wherever it reads, a shade of it where it doesn't, and "losses"
    move away from it when the two would look alike"""
    base = {**ST.DEFAULT["colors"], **C}
    dark, light = ST.rgba(base["dark"]), ST.rgba(base["light"])
    hue = C["accent"]
    for _ in range(12):                                   # a dark brand colour needs a lighter shade on dark grounds
        if ST.contrast(ST.rgba(C["accent"], dark), dark) >= 3.2:
            break
        C["accent"] = shade(C["accent"], 1.18)
    if C["accent"] != hue:
        print(f"note: {hue} is too dark to read on your dark background, so {C['accent']} stands in there.")
    for _ in range(12):                                   # and a pale one needs a darker shade on light grounds
        if ST.contrast(ST.rgba(C["accent_on_light"], light), light) >= 3:
            break
        C["accent_on_light"] = shade(C["accent_on_light"], 0.85)
    if ST.distance(ST.rgba(C["accent"]), ST.rgba(base["negative"])) < 30:
        C["negative"], C["negative_on_light"] = "#8E7CFF", "#5A3FD6"
    if ST.distance(ST.rgba(C["accent_on_light"]), ST.rgba(C.get("negative_on_light", base["negative_on_light"]))) < 30:
        C["negative"], C["negative_on_light"] = "#8E7CFF", "#5A3FD6"


def main():
    a = sys.argv[1:]
    get = lambda f: a[a.index(f) + 1] if f in a else None  # noqa: E731
    if "--list" in a:
        for k, v in BLURB.items():
            print(f"{k}: {v}")
        return
    preset = get("--preset")
    dest = ST.STYLE_DIR
    os.makedirs(dest, exist_ok=True)
    if preset:
        src = os.path.join(PACKS, preset)
        if not os.path.exists(os.path.join(src, "style.json")):
            sys.exit(f"No preset called {preset}. Choose from: {', '.join(BLURB)}")
        cur = os.path.join(dest, "style.json")
        if os.path.exists(cur):
            shutil.copy(cur, os.path.join(dest, "style.backup.json"))
        S = json.load(open(os.path.join(src, "style.json")))
        S.setdefault("creator", {})["name"] = ""
        shutil.copy(os.path.join(src, "STYLE.md"), os.path.join(dest, "STYLE.md"))
    else:
        path = os.path.join(dest, "style.json")
        if not os.path.exists(path):
            sys.exit("No style yet. Run: ve style --list, then ve style --preset <name>")
        S = json.load(open(path))
    for flag, key in (("--name", "name"), ("--handle", "handle"), ("--site", "site")):
        if get(flag):
            S.setdefault("creator", {})[key] = get(flag)
    accent = get("--accent")
    if accent:
        if not (accent.startswith("#") and len(accent) == 7):
            sys.exit('Give the colour as a hex code, like "#FD5323".')
        C = S.setdefault("colors", {})
        old = (C.get("accent") or "").upper()
        for k in ("textbox_bg", "textbox_ink"):           # a text box in the old accent follows the new one
            if (C.get(k) or "").upper() == old:
                C[k] = accent.upper()
        C["accent"] = accent.upper()
        C["accent_on_light"] = shade(accent, 0.72)
        C["series"] = [accent.upper()] + C.get("series", [])[1:]
        fit(C)
        if ST.contrast(ST.rgba(C["textbox_ink"]), ST.rgba(C["textbox_bg"])) < 4.5:
            C["textbox_ink"] = "#0B0B0B" if ST.contrast((11, 11, 11), ST.rgba(C["textbox_bg"])) >= 4.5 else "#FFFFFF"
    json.dump(S, open(os.path.join(dest, "style.json"), "w"), indent=2)
    full = ST.load(os.path.join(dest, "style.json"))
    ST.write(full, dest)
    print(os.path.join(dest, "style.json"))
    for w in ST.check(full):
        print("WARNING", w)


if __name__ == "__main__":
    main()
