#!/usr/bin/env python3
"""Builds dist/video-editor-plugin.zip: the plugin, ready to upload to Claude Cowork or add to Claude Code from a folder.
Run: python3 scripts/package.py
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP = [".claude-plugin", "agents", "skills", "engine", "README.md", "LICENSE", "NOTICE.md", "CHANGELOG.md"]
SKIP = {"__pycache__", ".DS_Store", "fonts", "board"}


def main():
    out = os.path.join(ROOT, "dist", "video-editor-plugin.zip")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for t in TOP:
            p = os.path.join(ROOT, t)
            if os.path.isfile(p):
                z.write(p, t)
                n += 1
                continue
            for root, dirs, files in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP)
                for f in sorted(files):
                    if f not in SKIP and not f.endswith(".pyc"):
                        full = os.path.join(root, f)
                        z.write(full, os.path.relpath(full, ROOT))
                        n += 1
    print(f"{out}  {n} files, {os.path.getsize(out) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
