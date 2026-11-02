#!/usr/bin/env python3
"""Faces: where the speaker's face is, so nothing has to be measured by hand for the common case.

Samples frames across a clip, finds the largest frontal face in each, takes the median. new.py uses it to seed edit.py:
FACE (what effects aim at), CAPTION_Y (just under the chin) and, for a horizontal clip, 9:16 crops centred on the person.
It proposes; a look at a still confirms it. No face found (a profile, a screen recording): the defaults stand.

Run: ve py pipeline/faces.py <clip>
"""
import json
import os
import statistics
import subprocess
import sys

SAMPLES = 9


def probe_size(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                          "-of", "json", path], capture_output=True, text=True).stdout
    d = json.loads(out)
    return d["streams"][0]["width"], d["streams"][0]["height"], float(d["format"]["duration"])


def find(path):
    """-> dict(x, y, w, h, hits) in source pixels (x, y = face centre), or None"""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    W, H, dur = probe_size(path)
    scale = 480 / max(W, H)
    w2, h2 = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2
    casc = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    found = []
    for k in range(SAMPLES):
        t = dur * (k + 0.5) / SAMPLES
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-vf", f"scale={w2}:{h2}",
                              "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
        if len(raw) != w2 * h2:
            continue
        img = np.frombuffer(raw, np.uint8).reshape(h2, w2)
        faces = casc.detectMultiScale(img, scaleFactor=1.1, minNeighbors=6, minSize=(max(24, w2 // 12), max(24, w2 // 12)))
        if len(faces):
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            found.append(((x + w / 2) / scale, (y + h / 2) / scale, w / scale, h / scale))
    if len(found) < 3:
        return None
    return dict(x=round(statistics.median(f[0] for f in found)), y=round(statistics.median(f[1] for f in found)),
                w=round(statistics.median(f[2] for f in found)), h=round(statistics.median(f[3] for f in found)), hits=len(found))


def seed(path):
    """FACE and CAPTION_Y on the 1080x1920 frame for the full-frame WIDE crop, the crops themselves for a horizontal clip"""
    try:
        f = find(path)
        W, H, _ = probe_size(path)
    except Exception as e:                                       # a helper: it must never stop an edit
        print(f"note: couldn't look for a face ({e})", file=sys.stderr)
        return None
    if not f:
        return None
    if W > H:                                                    # a 9:16 window on the person, and a tighter one
        ww = round(H * 9 / 16) // 2 * 2
        x0 = max(0, min(W - ww, f["x"] - ww // 2))
        cw, ch = round(ww / 1.5) // 2 * 2, round(H / 1.5) // 2 * 2
        cx0 = max(0, min(W - cw, f["x"] - cw // 2))
        cy0 = max(0, min(H - ch, f["y"] - round(ch * 0.38)))
        k = 1920 / H
        return dict(frames={"WIDE": (ww, H, x0, 0), "CLOSE": (cw, ch, cx0, cy0)}, face=(round((f["x"] - x0) * k), round(f["y"] * k)),
                    chin=round((f["y"] + f["h"] * 0.62) * k), head_top=round((f["y"] - f["h"] * 0.78) * k))
    k = 1080 / W
    return dict(frames=None, face=(round(f["x"] * k), round(f["y"] * k)), chin=round((f["y"] + f["h"] * 0.62) * k), head_top=round((f["y"] - f["h"] * 0.78) * k))


def caption_y(chin):
    """just under the chin, clear of the app's buttons below 1470 and of the face above"""
    return max(1040, min(1385, chin + 36))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print(json.dumps(seed(os.path.abspath(os.path.expanduser(sys.argv[1])))))


if __name__ == "__main__":
    main()
