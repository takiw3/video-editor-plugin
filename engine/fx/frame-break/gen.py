#!/usr/bin/env python3
"""frame-break: pull frame.jpg, the still the shards are cut from: the frame of clean.mp4 at the burst (the cue word
HIT_ON in the effect's window, plus CRACK), read from this effect's fx.js. The build runs it the first time the effect
is used (AUTO); rerun it when the window or HIT_ON moves.

Run: ve py fx/<id>/gen.py <project> [<id>]
"""
import importlib.util
import json
import os
import re
import subprocess
import sys

AUTO = True


def main():
    project = os.path.abspath(os.path.expanduser(sys.argv[1]))
    fid = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location("edit", os.path.join(project, "edit.py"))
    E = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(E)
    F = next((F for F in getattr(E, "FX", []) if F["id"] == fid), None)
    if not F:
        sys.exit(f"no FX entry with id {fid!r} in {project}/edit.py")
    d = os.path.join(project, "fx", fid)
    js = open(os.path.join(d, "fx.js"), encoding="utf-8").read()
    word = re.search(r"var HIT_ON = '([^']*)', HIT_AT = ([0-9.]+)", js)
    crack = float(re.search(r"var CRACK = ([0-9.]+)", js).group(1))
    a = F["at"]
    b = F["end"] if isinstance(F["end"], (int, float)) else a + 2
    t = a + float(word.group(2)) * (b - a)
    want = re.sub(r"[^a-z0-9%$']", "", word.group(1).lower())
    words = json.load(open(os.path.join(project, "words.json")))
    for w in words:
        if want and w["start"] >= a - 0.001 and w["start"] < b - 0.3 and re.sub(r"[^a-z0-9%$']", "", w["text"].lower()) == want:
            t = w["start"]
            break
    t += crack
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", os.path.join(project, "public", "clean.mp4"),
                    "-frames:v", "1", "-q:v", "3", os.path.join(d, "frame.jpg")], check=True)
    print(f"frame.jpg at {t:.3f}s")


if __name__ == "__main__":
    main()
