#!/usr/bin/env python3
"""Doctor: what's wrong, in plain words, with the fix. Nothing here changes anything.
Run: ve doctor [<project>]
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HOME, KIT, VERSION, load_edit  # noqa: E402


def project_report(project):
    project = os.path.abspath(os.path.expanduser(project))
    print(f"\nProject {os.path.basename(project)}")
    E = load_edit(project)
    pub = os.path.join(project, "public")
    steps = [
        ("the clip is still there", os.path.exists(E.SRC), "move it back, or point SRC in edit.py at it"),
        ("the cut is decided", bool(E.KEEP), "ve autocut <project> --write"),
        ("the cut is done", os.path.exists(os.path.join(project, "timeline.json")), "ve cut <project>"),
        ("words are timed", os.path.exists(os.path.join(project, "words.json")), "ve words <project>"),
        ("the picture is in place", os.path.exists(os.path.join(pub, "clean.mp4")), "copy assets/aroll.mp4 to public/clean.mp4"),
        ("the sound is mixed", os.path.exists(os.path.join(pub, "master.wav")), "ve mix <project>"),
    ]
    if E.CUT_WINDOWS:
        steps.append(("the cutout is done", os.path.exists(os.path.join(pub, "subject.webm")), "ve cutout <project>"))
    for c in E.CARDS:
        steps.append((f"card {c[0]} is rendered", os.path.exists(os.path.join(pub, c[1])), f"render cards/{c[0]}"))
    for i, T in enumerate(getattr(E, "TRANSITIONS", []) or []):
        steps.append((f"transition {T['effect']} is rendered", os.path.exists(os.path.join(pub, "tr", f"tr{i:02d}-{T['effect']}.mp4")), "ve transitions <project>"))
    for ok, (name, good, fix) in ((s[1], s) for s in steps):
        print(f"  {'ok     ' if good else 'MISSING'} {name}" + ("" if good else f"  (fix: {fix})"))


def main():
    print(f"Video Editor {VERSION}, home {HOME}")
    marker = os.path.join(HOME, ".setup-version")
    have = open(marker).read().strip() if os.path.exists(marker) else None
    if have != VERSION:
        print(f"Setup hasn't finished for this version ({have or 'never ran'}). Fix: run /video-editor:setup")
    r = subprocess.run(["sh", os.path.join(KIT, "setup", "setup.sh"), "--check"], capture_output=True, text=True)
    print(r.stdout[-2500:])
    if len(sys.argv) > 1:
        project_report(sys.argv[1])


if __name__ == "__main__":
    main()
