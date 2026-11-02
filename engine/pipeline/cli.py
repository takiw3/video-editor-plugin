#!/usr/bin/env python3
"""ve: the one command every step of an edit goes through. Setup writes it to $VIDEO_EDITOR_HOME/bin/ve.

    ve new <slug> <clip> [Title] --mode hifi|lofi|showcase      start a project (checks and converts the clip)
    ve probe <clip>                                             what a clip is, in plain words
    ve autocut <project>                                        propose KEEP: pauses, fillers, retakes
    ve cut <project> [--plan]                                   cut the take
    ve words <project>                                          word timings on the cut
    ve cutout <project>  |  ve matte <project>                  the speaker cut out, for things behind the head
    ve mix <project>                                            voice, sound effects, music
    ve build <project> [--stills] [--safe]                      write the composition
    ve transitions <project>                                    pre-render edit.TRANSITIONS
    ve storyboard <project> [--version N] [--list]              the page to review before rendering
    ve serve <project or folder> [--port N]                     review that page locally
    ve render <project> [name]                                  build, render, QA, deliver
    ve qa <project> <render> [--phone]                          the checks on their own
    ve export <project> <render> [--formats 9:16,4:5,1:1,16:9]  other sizes of a finished video
    ve post <project> <render>                                  cover images, captions file, post notes
    ve effects list|show|gallery|try ...                        the effects library
    ve style [--preset NAME] [--accent #hex]                    write or change the style pack
    ve board [--clip <clip>]                                    the style board to approve
    ve refs <out dir> <link or file> ...                        study inspiration videos
    ve fxsandbox <project> <name> --only <ids> --at <times>     test one hand-built effect
    ve flash <video>                                            the photosensitivity check
    ve doctor                                                   what's wrong on this computer, in plain words
    ve hf <args>                                                the pinned HyperFrames CLI (cards and effects use it)
    ve ffmpeg <args>  |  ve ffprobe <args>                      the kit's own video tools
    ve py <script> [args]                                       run a helper script from the plugin or a project
    ve permissions [--apply]                                    let Claude run these steps without asking each time
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
SCRIPTS = {
    "new": "pipeline/new.py", "probe": "pipeline/ingest.py", "autocut": "pipeline/autocut.py", "cut": "pipeline/cut.py",
    "words": "pipeline/words.py", "cutout": "pipeline/cutout.py", "matte": "pipeline/matte.py", "mix": "pipeline/mix.py",
    "build": "pipeline/build.py", "transitions": "pipeline/transitions.py", "storyboard": "pipeline/storyboard.py",
    "serve": "storyboard/serve.py", "render": "pipeline/render.py", "qa": "pipeline/qa.py", "export": "pipeline/export.py",
    "post": "pipeline/postpack.py", "effects": "pipeline/effects.py", "style": "pipeline/presets.py",
    "board": "onboarding/board.py", "refs": "onboarding/refs.py", "fxsandbox": "pipeline/fxsandbox.py",
    "flash": "pipeline/flash.py", "doctor": "pipeline/doctor.py",
}


def home():
    return os.path.expanduser(os.environ.get("VIDEO_EDITOR_HOME", "~/video-editor"))


def run_py(rest):
    """helper scripts only: the ones inside the plugin or the creator's projects, so this can't run anything else"""
    if not rest:
        print("usage: ve py <script> [args]", file=sys.stderr)
        return 2
    script = rest[0]
    if not os.path.isabs(script) and not os.path.exists(script):
        script = os.path.join(KIT, script)
    script = os.path.realpath(script)
    roots = [os.path.realpath(KIT), os.path.realpath(home())]
    if not any(script.startswith(r + os.sep) for r in roots):
        print(f"ve py only runs scripts inside {roots[0]} or {roots[1]}", file=sys.stderr)
        return 4
    return subprocess.call([sys.executable, script] + rest[1:])


def permissions(rest):
    """the allow rules that stop a permission prompt on every step. Prints them; --apply adds them to the user's
    Claude Code settings after they said yes. Nothing else in that file changes."""
    import json
    h = home()
    rules = [f"Bash({h}/bin/ve:*)", f"Read({h}/**)", f"Write({h}/**)", f"Edit({h}/**)"]
    if "--apply" not in rest:
        print("\n".join(rules))
        return 0
    path = os.path.expanduser("~/.claude/settings.json")
    data = json.load(open(path)) if os.path.exists(path) else {}
    allow = data.setdefault("permissions", {}).setdefault("allow", [])
    added = [r for r in rules if r not in allow]
    allow.extend(added)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        import shutil
        shutil.copy(path, path + ".before-video-editor")
    json.dump(data, open(path, "w"), indent=2)
    print(f"Added {len(added)} rules to {path}. To undo, remove the lines that mention {h}.")
    return 0


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "hf":
        sys.path.insert(0, HERE)
        from common import HF
        return subprocess.call(HF + rest)
    if cmd in ("ffmpeg", "ffprobe"):                 # the kit's own, when it fetched one; `ve` put it first on PATH
        return subprocess.call([cmd] + rest)
    if cmd == "py":
        return run_py(rest)
    if cmd == "permissions":
        return permissions(rest)
    if cmd not in SCRIPTS:
        print(f"ve: no step called {cmd!r}. Run `ve help` for the list.", file=sys.stderr)
        return 2
    return subprocess.call([sys.executable, os.path.join(KIT, SCRIPTS[cmd])] + rest)


if __name__ == "__main__":
    sys.exit(main())
