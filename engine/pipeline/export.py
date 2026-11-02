#!/usr/bin/env python3
"""Export: one finished vertical video, in the shapes other places want. Every file is checked after it's written.

  9:16  1080x1920  Reels, TikTok, Shorts (the master)
  4:5   1080x1350  Instagram and LinkedIn feed: cropped around the face
  1:1   1080x1080  feeds, ads: cropped around the face
  16:9  1920x1080  YouTube, LinkedIn: the vertical video centred, with a soft blurred copy of itself filling the sides

Run: ve export <project> <render> [--formats 4:5,1:1,16:9]
A crop can cut off what sits near the top or bottom of the frame, so a text hook or a CTA low in frame may need a re-edit.
This prints where each crop lands so that can be checked by eye.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_edit, project_arg  # noqa: E402

SHAPES = {"9:16": (1080, 1920), "4:5": (1080, 1350), "1:1": (1080, 1080), "16:9": (1920, 1080)}


def crop_y(h, cap_bottom=1470, face_y=760):
    """the top of a crop of height h: keep the captions in if it can, else centre on the face"""
    top = max(0, min(1920 - h, cap_bottom + 30 - h))
    if top > face_y - 200:
        top = max(0, face_y - h // 2)
    return top


def export_one(render, shape, dest, face_y=760):
    W, H = SHAPES[shape]
    if shape == "9:16":
        vf = f"scale={W}:{H}"
    elif shape == "16:9":
        vf = None
    else:
        vf = f"crop=1080:{H}:0:{crop_y(H, face_y=face_y)}"
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", render]
    if vf:
        cmd += ["-vf", vf]
    else:
        cmd += ["-filter_complex", f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                f"boxblur=40:2,eq=brightness=-0.12[bg];[b]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0,format=yuv420p[v]",
                "-map", "[v]", "-map", "0:a"]
    cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k",
            "-movflags", "+faststart", dest]
    subprocess.run(cmd, check=True)
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "json", dest], capture_output=True, text=True).stdout
    s = json.loads(out)["streams"][0]
    if (s["width"], s["height"]) != (W, H):
        raise SystemExit(f"{dest} came out {s['width']}x{s['height']}, expected {W}x{H}")
    return dest


def main():
    project = project_arg()
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    render = sys.argv[2] if os.path.isabs(sys.argv[2]) else os.path.join(project, sys.argv[2])
    E = load_edit(project)
    a = sys.argv
    formats = a[a.index("--formats") + 1].split(",") if "--formats" in a else ["4:5", "1:1", "16:9"]
    for f in formats:
        if f not in SHAPES:
            sys.exit(f"{f} isn't a shape I export. Choose from {', '.join(SHAPES)}")
    face_y = getattr(E, "CAM_ORIGIN", (540, 760))[1]
    base = os.path.splitext(render)[0]
    for f in formats:
        dest = f"{base}-{f.replace(':', 'x')}.mp4"
        export_one(render, f, dest, face_y)
        note = "" if f in ("9:16", "16:9") else f"  (keeps y {crop_y(SHAPES[f][1], face_y=face_y)} to {crop_y(SHAPES[f][1], face_y=face_y) + SHAPES[f][1]} of 1920)"
        print(f"{f}: {dest}  {os.path.getsize(dest) / 1e6:.1f} MB{note}")


if __name__ == "__main__":
    main()
