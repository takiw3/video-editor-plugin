#!/usr/bin/env python3
"""Cutout: the speaker cut out of the J-cut picture -> <project>/assets/subject.webm (VP9 + alpha) and public/.

Needed only when edit.BEHIND puts something behind the speaker's head. ~7s per second of footage on Apple Silicon: run it in the
background right after cut.py and keep working. Verifies the cutout has exactly the frames of aroll.mp4 (a mismatch
drifts the cutout off the speaker).
Run: ve cutout <project> [--again]   (a finished cutout for the same cut is kept)
"""
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HF, project_arg  # noqa: E402

PROGRESS_EVERY = 30                   # seconds between progress lines


def frames(f):
    return subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                           "stream=nb_read_frames", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip().strip(",")


def stamp(project):
    """what the cutout was made from: a new cut means a new cutout"""
    st = os.stat(os.path.join(project, "assets", "aroll.mp4"))
    return f"{st.st_size}:{int(st.st_mtime)}"


def main():
    project = project_arg()
    t0 = time.time()
    if not os.path.exists(os.path.join(project, "assets", "aroll.mp4")):
        sys.exit("No cut yet (assets/aroll.mp4 is missing): run ve cut first.")
    key = os.path.join(project, "assets", "subject.key")
    final = os.path.join(project, "public", "subject.webm")
    if "--again" not in sys.argv and os.path.exists(final) and os.path.exists(key) and open(key).read() == stamp(project):
        print("cutout: already done for this cut (--again to redo it)")
        return
    # the renderer draws a progress spinner on every frame: keep it in a log, print one line every 30s instead
    log_path = os.path.join(project, "work", "cutout.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w") as log:
        p = subprocess.Popen(HF + ["remove-background", "assets/aroll.mp4", "-o", "assets/subject.webm", "--quality",
                                   "best"], cwd=project, stdout=log, stderr=subprocess.STDOUT)
        last = time.time()
        while p.poll() is None:
            time.sleep(1)
            if time.time() - last >= PROGRESS_EVERY:
                last = time.time()
                done = re.findall(r"Frame (\d+)/(\d+)", open(log_path, errors="ignore").read()[-400:])
                print(f"cutout: frame {done[-1][0]}/{done[-1][1]}" if done else "cutout: loading the model", flush=True)
    if p.returncode:
        sys.exit(f"remove-background failed (see {log_path})")
    a, s = frames(os.path.join(project, "assets", "aroll.mp4")), frames(os.path.join(project, "assets", "subject.webm"))
    print(f"aroll frames {a} / cutout frames {s}  ({time.time() - t0:.0f}s)")
    if not a or a != s:
        sys.exit("FRAME MISMATCH: the cutout would drift. Re-run cut.py, then this.")
    shutil.copy(os.path.join(project, "assets", "subject.webm"), final)
    with open(key, "w") as fh:
        fh.write(stamp(project))


if __name__ == "__main__":
    main()
