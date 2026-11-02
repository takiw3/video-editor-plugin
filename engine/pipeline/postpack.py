#!/usr/bin/env python3
"""Post pack: everything needed to post a finished video, next to it, in <render name>-post/:
  cover.jpg        the 9:16 cover, the frame with the hook on it (--cover <seconds> picks another)
  cover-4x5.jpg    the same frame cropped for the Instagram grid
  captions.srt     for platforms that take a caption file (YouTube, LinkedIn)
  transcript.txt   the spoken words as plain text, to write the post copy from
  post.md          the post copy, written by the agent from transcript.txt (kit/POSTING.md says how)

Run: ve post <project> <render> [--cover 1.2]
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_edit, project_arg  # noqa: E402


def tc(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def srt(words, max_chars=38, gap=0.6):
    """words -> subtitle cards, broken on punctuation, pauses and length"""
    cards, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        text = " ".join(x["text"] for x in cur)
        if nxt is None or w["text"][-1:] in ".?!," or nxt["start"] - w["end"] > gap or len(text) + 1 + len(nxt["text"]) > max_chars:
            cards.append((cur[0]["start"], cur[-1]["end"], text))
            cur = []
    return "".join(f"{k + 1}\n{tc(a)} --> {tc(b)}\n{t}\n\n" for k, (a, b, t) in enumerate(cards))


def main():
    project = project_arg()
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    render = sys.argv[2] if os.path.isabs(sys.argv[2]) else os.path.join(project, sys.argv[2])
    E = load_edit(project)
    a = sys.argv
    words = json.load(open(os.path.join(project, "words.json")))
    default = 0.6 if getattr(E, "HOOK", None) or getattr(E, "BOXES", None) or getattr(E, "FX", None) else 1.0
    at = float(a[a.index("--cover") + 1]) if "--cover" in a else default
    out = os.path.splitext(render)[0] + "-post"
    os.makedirs(out, exist_ok=True)
    cover = os.path.join(out, "cover.jpg")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.3f}", "-i", render, "-frames:v", "1", "-q:v", "2", cover], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", cover, "-vf", "crop=1080:1350:0:150", "-q:v", "2", os.path.join(out, "cover-4x5.jpg")], check=True)
    with open(os.path.join(out, "captions.srt"), "w", encoding="utf-8") as fh:
        fh.write(srt(words))
    with open(os.path.join(out, "transcript.txt"), "w", encoding="utf-8") as fh:
        fh.write(" ".join(w["text"] for w in words) + "\n")
    print(out)
    for f in sorted(os.listdir(out)):
        print(" ", f)


if __name__ == "__main__":
    main()
