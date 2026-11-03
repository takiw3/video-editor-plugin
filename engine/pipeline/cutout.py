#!/usr/bin/env python3
"""Cutout: the speaker cut out of the J-cut picture -> <project>/assets/subject.webm (VP9 + alpha) and public/.

Only the moments that use it are cut out: every CUT_WINDOWS window and every hand-built effect that reads the cutout,
half a second either side. The rest of the file is transparent, so it stays frame for frame with aroll.mp4 and every
effect that reads it by time keeps working. The model runs at ~2 frames a second on a laptop, so this is the difference
between minutes and a quarter of an hour. Run it once edit.py has its windows; run it again after they move and only the
new frames are cut out. --all cuts out the whole video (the old way).
Verifies the cutout has exactly the frames of aroll.mp4 (a mismatch drifts the cutout off the speaker).
Run: ve cutout <project> [--all] [--again]
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FPS, HF, HOME, KIT, load_edit, project_arg, q  # noqa: E402

PROGRESS_EVERY = 30                   # seconds between progress lines
PAD = 15                              # frames either side of a window: small timing changes don't need another cutout
CHUNK = 90                            # frames in an encoded piece: short enough to spread over the cores
VP9 = ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "12", "-deadline", "good", "-row-mt", "1", "-cpu-used", "4",
       "-auto-alt-ref", "0", "-pix_fmt", "yuva420p", "-colorspace", "bt709", "-color_primaries", "bt709",
       "-color_trc", "bt709", "-color_range", "tv", "-metadata:s:v:0", "alpha_mode=1"]   # HyperFrames' own "best"


def frames(f):
    return subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                           "stream=nb_read_frames", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip().strip(",")


def packets(f):
    """frames in an mp4 without decoding it"""
    out = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                          "stream=nb_read_packets", "-of", "csv=p=0", f], capture_output=True, text=True).stdout
    return int(out.strip().strip(",") or 0)


def last_time(f):
    """when the last frame of a video shows, from its packets (no decode)"""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time", "-of",
                          "csv=p=0", f], capture_output=True, text=True).stdout.split()
    return float(out[-1].strip(",")) if out else 0.0


def stamp(project):
    """what the cutout was made from: a new cut means a new cutout"""
    st = os.stat(os.path.join(project, "assets", "aroll.mp4"))
    return f"{st.st_size}:{int(st.st_mtime)}"


def merge(ranges, gap=0):
    out = []
    for a, b in sorted(ranges):
        if out and a <= out[-1][1] + 1 + gap:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def subtract(need, done):
    """the frames of `need` that no range in `done` covers"""
    out = []
    for a, b in need:
        cur = a
        for c, d in merge(done):
            if d < cur or c > b:
                continue
            if c > cur:
                out.append([cur, c - 1])
            cur = max(cur, d + 1)
        if cur <= b:
            out.append([cur, b])
    return out


def uses_subject(project, F):
    """does this hand-built effect read the cutout (its files name subject.webm)?"""
    name = F.get("like") or F["id"]
    for d in (os.path.join(project, "fx", F["id"]), os.path.join(HOME, "fx", name), os.path.join(KIT, "fx", name)):
        if os.path.isdir(d):
            return any("subject.webm" in open(os.path.join(d, f), errors="ignore").read()
                       for f in os.listdir(d) if f.endswith((".js", ".html", ".py")))
    return False


def needed(project, E, n, pad=PAD):
    """frame ranges the edit needs cut out, pad frames either side, merged"""
    wins = [(a, b) for a, b in E.CUT_WINDOWS]
    wins += [(F["at"], F["end"]) for F in getattr(E, "FX", []) if uses_subject(project, F)]
    ranges = [[max(0, round(q(a) * FPS) - pad), n - 1 if b == "end" else min(n - 1, round(q(b) * FPS) + pad)]
              for a, b in wins]
    return merge(ranges, gap=2 * pad)


def missing(project, E):
    """the stretches (in seconds) the edit uses that public/subject.webm doesn't cover yet: build and the storyboard
    warn about them, render won't start with any"""
    aroll = os.path.join(project, "assets", "aroll.mp4")
    if not os.path.exists(aroll):
        return []
    n = packets(aroll)
    return [(a / FPS, (b + 1) / FPS) for a, b in subtract(needed(project, E, n, pad=0), covered(project, n))]


def read_key(project):
    """{"aroll": stamp, "parts": [{"file", "ranges": [[f0, f1, at]]}]}, or None. A key from before 1.3.0 is a bare stamp
    for a whole-video cutout"""
    p = os.path.join(project, "assets", "subject.key")
    if not os.path.exists(p):
        return None
    raw = open(p).read()
    try:
        return json.loads(raw)
    except ValueError:
        return {"aroll": raw.strip(), "whole": True, "parts": []}


def write_key(project, key):
    with open(os.path.join(project, "assets", "subject.key"), "w") as fh:
        json.dump(key, fh, indent=1)


def covered(project, n=None):
    """the frame ranges public/subject.webm covers for the current cut ([] when it's stale or missing)"""
    key = read_key(project)
    sub = os.path.join(project, "public", "subject.webm")
    if not key and os.path.exists(sub):                 # made before there was a key: whole if it has every frame
        n = n or packets(os.path.join(project, "assets", "aroll.mp4"))
        return [[0, n - 1]] if packets(sub) == n else []
    if not key or key.get("aroll") != stamp(project) or not os.path.exists(sub):
        return []
    if key.get("whole"):
        n = n or packets(os.path.join(project, "assets", "aroll.mp4"))
        return [[0, n - 1]]
    return merge([[f0, f1] for p in key["parts"] for f0, f1, _ in p["ranges"]])


def remove_background(project, src, out, log_path):
    """the model over one file; prints a progress line every 30 s"""
    with open(log_path, "w") as log:
        p = subprocess.Popen(HF + ["remove-background", src, "-o", out, "--quality", "best"], cwd=project,
                             stdout=log, stderr=subprocess.STDOUT)
        last = time.time()
        while p.poll() is None:
            time.sleep(1)
            if time.time() - last >= PROGRESS_EVERY:
                last = time.time()
                done = re.findall(r"Frame (\d+)/(\d+)", open(log_path, errors="ignore").read()[-400:])
                print(f"cutout: frame {done[-1][0]}/{done[-1][1]}" if done else "cutout: loading the model", flush=True)
    if p.returncode:
        sys.exit(f"remove-background failed (see {log_path})")


def cut_out(project, ranges, k):
    """the model over just these frames of aroll.mp4, packed end to end -> assets/subject-parts/p<k>.mov
    (ProRes 4444: lossless enough that the one VP9 encode below is the only loss, as before)"""
    work = os.path.join(project, "work")
    os.makedirs(work, exist_ok=True)
    packed = os.path.join(work, "cutout-in.mp4")
    sel = "+".join(f"between(n\\,{a}\\,{b})" for a, b in ranges)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(project, "assets", "aroll.mp4"), "-vf",
                    f"select='{sel}',setpts=N/{FPS}/TB", "-fps_mode", "cfr", "-an", "-c:v", "libx264", "-qp", "0",
                    "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-r", str(FPS), packed], check=True)
    want = sum(b - a + 1 for a, b in ranges)
    if packets(packed) != want:
        sys.exit(f"cutout: picked {packets(packed)} frames, expected {want}")
    os.makedirs(os.path.join(project, "assets", "subject-parts"), exist_ok=True)
    part = os.path.join("assets", "subject-parts", f"p{k}.mov")
    remove_background(project, os.path.relpath(packed, project), part, os.path.join(work, "cutout.log"))
    got = frames(os.path.join(project, part))
    if str(got) != str(want):
        sys.exit(f"FRAME MISMATCH in the cutout ({got} of {want} frames): run ve cutout {project} --again")
    os.remove(packed)
    at, out = 0, []
    for a, b in ranges:
        out.append([a, b, at])
        at += b - a + 1
    return {"file": part, "ranges": out}


def size(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip().strip(",")
    return out.replace(",", "x")


def piece(out, m, src=None, at=0, wh="1080x1920"):
    """m frames of VP9 + alpha: transparent (wh), or frames at.. of a cut-out part (seeked half a frame early: ProRes
    is all-intra, so that lands on the exact frame and decodes only these)"""
    if src is None:
        args = ["-f", "lavfi", "-i", f"color=c=black@0.0:s={wh}:r={FPS},format=yuva444p10le"]
    else:
        args = ["-ss", f"{(at - 0.5) / FPS:.6f}", "-i", src]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-frames:v", str(m), "-r", str(FPS), *VP9, "-an", out + ".tmp.webm"],
                   check=True)
    os.replace(out + ".tmp.webm", out)
    return out


def assemble(project, parts, n):
    """every cut-out stretch at its own frames, transparent everywhere else -> assets/subject.webm (n frames).
    Encoded as pieces of up to 3 seconds, several at once, then joined without re-encoding (VP9 keeps its alpha through
    the join). Pieces are kept: after a window moves, only its new pieces are encoded"""
    pdir = os.path.join(project, "assets", "subject-parts")
    wh = size(os.path.join(project, "assets", "aroll.mp4"))
    spans = sorted((f0, f1, p["file"], at) for p in parts for f0, f1, at in p["ranges"])
    jobs, cur = [], 0                                       # (piece file, frames, part or None, first frame in the part)

    def chunks(m):
        k = -(-m // CHUNK)
        return [m // k + (1 if i < m % k else 0) for i in range(k)]
    for f0, f1, f, at in spans + [(n, n - 1, None, 0)]:
        for m in chunks(f0 - cur) if f0 > cur else []:
            jobs.append((os.path.join(pdir, f"gap{wh}-{m}.webm"), m, None, 0))
        if f is None:
            break
        for m in chunks(f1 - f0 + 1):
            jobs.append((os.path.join(pdir, f"{os.path.basename(f)[:-4]}-{at}-{m}.webm"), m, os.path.join(project, f), at))
            at += m
        cur = f1 + 1
    todo = {j[0]: j for j in jobs if not os.path.exists(j[0])}
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max(2, (os.cpu_count() or 4) // 3)) as ex:
        list(ex.map(lambda j: piece(j[0], j[1], j[2], j[3], wh), todo.values()))
    keep = {os.path.basename(j[0]) for j in jobs}
    for f in os.listdir(pdir):
        if f.endswith(".webm") and f not in keep:
            os.remove(os.path.join(pdir, f))
    lst = os.path.join(pdir, "join.txt")
    with open(lst, "w") as fh:
        # each piece's exact length: left to itself the join offsets every piece by its rounded container duration,
        # and over 16 pieces that drifts the cutout ~8 frames late
        fh.write("".join(f"file '{os.path.basename(j[0])}'\nduration {j[1] / FPS:.6f}\n" for j in jobs))
    out = os.path.join(project, "assets", "subject.webm")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    return out


def main():
    project = project_arg()
    t0 = time.time()
    aroll = os.path.join(project, "assets", "aroll.mp4")
    if not os.path.exists(aroll):
        sys.exit("No cut yet (assets/aroll.mp4 is missing): run ve cut first.")
    n = packets(aroll)
    E = load_edit(project) if os.path.exists(os.path.join(project, "edit.py")) else None
    need = [[0, n - 1]] if "--all" in sys.argv else needed(project, E, n) if E else []
    if not need:
        print("cutout: nothing in edit.py uses it yet (no CUT_WINDOWS, no effect that reads the cutout). Write the "
              "windows first, then run this again (--all cuts out the whole video).")
        return
    if "--again" not in sys.argv and not subtract(need if "--all" in sys.argv else needed(project, E, n, pad=0),
                                                  covered(project, n)):
        print("cutout: already done for these windows (--again to redo it)")
        return
    key = read_key(project)
    if "--again" in sys.argv or not key or key.get("aroll") != stamp(project) or key.get("whole"):
        shutil.rmtree(os.path.join(project, "assets", "subject-parts"), ignore_errors=True)
        key = {"aroll": stamp(project), "parts": []}
    todo = subtract(need, covered(project, n) if key["parts"] else [])
    if not todo:
        print("cutout: already done for these windows (--again to redo it)")
        return
    secs = sum(b - a + 1 for a, b in todo) / FPS
    lo = max(1, round(secs * 0.17 + 0.5))
    print(f"cutout: {secs:.1f}s of {n / FPS:.1f}s ({len(todo)} stretch{'es' if len(todo) > 1 else ''}), "
          f"about {lo}-{max(lo + 1, round(secs * 0.3 + 1))} min", flush=True)
    key["parts"].append(cut_out(project, todo, len(key["parts"]) + 1))
    out = assemble(project, key["parts"], n)
    s = frames(out)
    print(f"aroll frames {n} / cutout frames {s}  ({time.time() - t0:.0f}s)")
    if str(n) != str(s):
        sys.exit("FRAME MISMATCH: the cutout would drift. Re-run cut.py, then this.")
    if abs(last_time(out) - (n - 1) / FPS) > 0.6 / FPS:
        sys.exit(f"TIMING MISMATCH: the cutout's last frame shows at {last_time(out):.3f}s, not {(n - 1) / FPS:.3f}s, "
                 f"so it would drift. Run ve cutout {project} --again")
    shutil.copy(out, os.path.join(project, "public", "subject.webm"))
    write_key(project, key)


if __name__ == "__main__":
    main()
