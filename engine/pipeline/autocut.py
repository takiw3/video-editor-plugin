#!/usr/bin/env python3
"""Autocut: a first pass at the cut, so nobody starts from a blank KEEP.

Transcribes the whole take with word timings and proposes what to keep:
  - dead air: any pause over --pause seconds (default 0.35) closes up
  - fillers: um, uh, erm, hmm, on their own between words
  - retakes: when a sentence is restarted (the same opening words again), the LAST take stays, since people repeat a
    line until it lands; a sentence that trails off into a restart goes too

Writes <project>/work/autocut.json and prints KEEP with the words of each range beside it, ready to paste into edit.py.
It proposes, you decide: read it against the transcript. It can't tell a deliberate repeat ("again and again") from a
retake, so anything it removes as a retake is listed for a look. Cutting must never change what someone meant.

Run: ve autocut <project> [--pause 0.35] [--pad 0.05] [--write]    --write puts KEEP straight into edit.py
"""
import difflib
import json
import os
import re
import subprocess
import sys

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import WHISPER, load_edit, project_arg  # noqa: E402

FILLERS = {"um", "uh", "umm", "uhh", "erm", "er", "ah", "hmm", "mm", "mhm"}
ENDS = ".?!"


def norm(w):
    return re.sub(r"[^\w']+", "", w.lower())


def transcribe(E, project):
    """the whole take, cached: [[start, end, text], ...] in source seconds"""
    cache = os.path.join(project, "work", "autocut_words.json")
    if os.path.exists(cache):
        d = json.load(open(cache))
        if d.get("src") == E.SRC:
            return d["words"]
    from faster_whisper import WhisperModel
    work = os.path.join(project, "work")
    os.makedirs(work, exist_ok=True)
    wav = os.path.join(work, "whole.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", E.SRC, "-ar", "16000", "-ac", "1", wav], check=True)
    sr, pcm = wavfile.read(wav)
    print(f"transcribing the whole take with Whisper {WHISPER} ...", flush=True)
    model = WhisperModel(WHISPER, compute_type="int8")
    segs, info = model.transcribe(pcm.astype(np.float32) / 32768.0, language=getattr(E, "LANGUAGE", None), word_timestamps=True,
                                  vad_filter=False, initial_prompt=E.PROMPT or None, condition_on_previous_text=False)
    words = [[round(w.start, 3), round(w.end, 3), w.word.strip()] for s in segs for w in s.words]
    json.dump({"src": E.SRC, "language": info.language, "words": words}, open(cache, "w"))
    os.remove(wav)
    return words


def sentences(words, gap=0.7):
    """word indexes grouped into sentences: end punctuation, or a long pause"""
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if w[2][-1:] in ENDS or nxt is None or nxt[0] - w[1] > gap:
            out.append(cur)
            cur = []
    return out


def find_retakes(words, sents):
    """a sentence whose opening matches the opening of one of the next few: an earlier take of the same line"""
    drop, why = set(), []
    for k, s in enumerate(sents):
        a = [norm(words[i][2]) for i in s]
        if len(a) < 3:
            continue
        for later in sents[k + 1:k + 4]:
            b = [norm(words[i][2]) for i in later]
            n = min(len(a), len(b), 5)
            if n >= 3 and difflib.SequenceMatcher(None, a[:n], b[:n]).ratio() >= 0.8:
                drop.update(s)
                why.append(" ".join(words[i][2] for i in s))
                break
    return drop, why


def propose(words, pause=0.35, pad=0.05):
    sents = sentences(words)
    retake, why = find_retakes(words, sents)
    fillers = {i for i, w in enumerate(words) if norm(w[2]) in FILLERS and i not in retake}
    keep = [i for i in range(len(words)) if i not in retake and i not in fillers]
    ranges, cur = [], None
    for i in keep:
        a, b = words[i][0], words[i][1]
        if cur and a - cur["end"] <= pause and i - cur["last"] == 1:
            cur["end"], cur["last"] = b, i
            cur["ids"].append(i)
        else:
            if cur:
                ranges.append(cur)
            cur = {"start": a, "end": b, "last": i, "ids": [i]}
    if cur:
        ranges.append(cur)
    out = []
    for r in ranges:
        out.append((round(max(0, r["start"] - pad), 2), round(r["end"] + pad, 2), " ".join(words[i][2] for i in r["ids"])))
    return out, [words[i][2] for i in sorted(fillers)], why


def main():
    project = project_arg()
    E = load_edit(project)
    a = sys.argv
    pause = float(a[a.index("--pause") + 1]) if "--pause" in a else 0.35
    pad = float(a[a.index("--pad") + 1]) if "--pad" in a else 0.05
    words = transcribe(E, project)
    if not words:
        sys.exit("No speech found in this clip.")
    ranges, fillers, retakes = propose(words, pause, pad)
    before = words[-1][1] - words[0][0]
    after = sum(b - s for s, b, _ in ranges)
    json.dump(dict(keep=[r[:2] for r in ranges], fillers=fillers, retakes=retakes), open(os.path.join(project, "work", "autocut.json"), "w"), indent=1)
    body = "KEEP = [\n" + "".join(f"    ({s:.2f}, {b:.2f}),   # {t[:90]}\n" for s, b, t in ranges) + "]\n"
    print(body)
    print(f"{before:.0f}s of talking becomes {after:.0f}s. {len(fillers)} filler words out. {len(retakes)} retakes out:")
    for r in retakes:
        print(f"  - {r}")
    if "--write" in a:
        path = os.path.join(project, "edit.py")
        s = open(path).read()
        s2, n = re.subn(r"^KEEP = \[.*?^\]\n|^KEEP = \[\]\n", lambda _: body, s, count=1, flags=re.S | re.M)
        if not n:
            sys.exit("no KEEP line found in edit.py")
        open(path, "w").write(s2)
        print("wrote KEEP to edit.py")


if __name__ == "__main__":
    main()
