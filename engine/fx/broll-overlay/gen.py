#!/usr/bin/env python3
"""broll-overlay: put a real clip in the card.

Cuts <clip> (from [start], as long as the effect's window) into <project>/fx/<id>/clip.mp4 at 940 px wide, points the
card's <video> at it (fx/<id>/clip.mp4 from 0) and sets PLACEHOLDER = false in fx.js.

Run: ve py fx/<id>/gen.py <project> <id> <clip> [start]
"""
import importlib.util
import os
import re
import subprocess
import sys


def main():
    project, fid, clip = os.path.abspath(os.path.expanduser(sys.argv[1])), sys.argv[2], os.path.expanduser(sys.argv[3])
    start = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    spec = importlib.util.spec_from_file_location("edit", os.path.join(project, "edit.py"))
    E = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(E)
    F = next((F for F in getattr(E, "FX", []) if F["id"] == fid), None)
    if not F:
        sys.exit(f"no FX entry with id {fid!r} in {project}/edit.py")
    end = F["end"] if isinstance(F["end"], (int, float)) else F["at"] + 3
    d = os.path.join(project, "fx", fid)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i", clip, "-t", f"{end - F['at'] + 0.2:.3f}", "-an",
                    "-vf", "scale=940:-2,fps=30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-g", "1", "-crf", "20",
                    os.path.join(d, "clip.mp4")], check=True)
    html = open(os.path.join(d, "fx.html"), encoding="utf-8").read()
    html = re.sub(r'src="[^"]*" muted playsinline data-start="\{\{START\}\}" data-media-start="[^"]*"',
                  'src="fx/{{ID}}/clip.mp4" muted playsinline data-start="{{START}}" data-media-start="0"', html)
    open(os.path.join(d, "fx.html"), "w", encoding="utf-8").write(html)
    js = open(os.path.join(d, "fx.js"), encoding="utf-8").read().replace("var PLACEHOLDER = true;", "var PLACEHOLDER = false;")
    open(os.path.join(d, "fx.js"), "w", encoding="utf-8").write(js)
    print(os.path.join(d, "clip.mp4"))


if __name__ == "__main__":
    main()
