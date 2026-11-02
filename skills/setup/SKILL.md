---
name: setup
description: Sets up the video editor on this computer, or checks it after an update. Use on /video-editor:setup, when someone first installs the plugin, says "set it up" or "get started", or when another video-editor skill finds setup hasn't run.
---

# Set up the video editor

The person is probably not technical. They should never have to install anything, read a log or type a command.
Do the work, narrate it in plain words, and stay with it until it prints READY.

## Run it

Say what's about to happen, in this shape: "I'm getting your video editor ready. This takes a few minutes the first time,
depending on your internet, and downloads about 2 GB. It goes in one folder, `video-editor` in your home folder. Nothing
needs your password."

Run this with the longest timeout your tool allows, and wait for it:

```
sh "${CLAUDE_PLUGIN_ROOT}/engine/setup/setup.sh"
```

If it times out or gets cut off, run it again: it picks up where it stopped, so nothing is lost. Do not end your turn until
it has printed READY or you've reached something only the person can fix. If your output shows `STEP n/8` lines, pass them on
in a few plain words, not the raw line. Keep updates short.

## When it stops

- Prints `READY`: go to "After it's ready".
- A `MISSING` line comes with its fix. Do the fix yourself, then run setup again. It picks up where it stopped. Only ask
  the person to act when it needs their hands:
  - **Mac popup about command line developer tools**: "Click Install on the popup and wait for it to finish, then tell me."
  - **No internet**: "I can't reach the download servers. Check your wifi or turn off your VPN, then tell me."
  - **Not enough disk space**: say how much is free and that about 3 GB is needed, plus room for videos.
- Fails the same way twice: run `ve doctor` (below), and tell them what's wrong in one sentence, what you tried, and what
  you need. No stack traces.
- **Windows**: setup needs Git Bash (`sh`). If `sh` isn't found, say the Windows path hasn't been tested as much as Mac
  and Linux, install Git for Windows with `winget install --id Git.Git -e`, and carry on.
- **No terminal here at all** (a chat app with no computer access): say this needs Claude Code or Claude Cowork,
  because it edits video on their computer. Then stop.
- **Claude Cowork or a host limited to granted folders**: `export VIDEO_EDITOR_HOME=<granted folder>/video-editor` in
  every command, so their style and videos stay on their computer between sessions.

## After it's ready

From here on, every step runs through one command, `VE` = `~/video-editor/bin/ve` (or `$VIDEO_EDITOR_HOME/bin/ve`).

1. Offer to stop the approval popups. Ask, using a question tool if you have one: "Each step would normally ask your
   permission. Want me to let the video editor's own tools run without asking? It only covers the `video-editor` folder,
   and you can undo it any time." On yes, run `VE permissions --apply`. It backs up their settings first and takes
   effect in the next session. On no, carry on: never ask again this session. If it isn't Claude Code, skip this.
2. Then say the next step, once, in one line:
   - No style yet (`~/video-editor/style/style.json` missing): "You're ready. Next we set up your look, which takes a
     couple of minutes." Start the `style` skill's flow right away unless they want to stop.
   - Style exists: "All set. Drag in a clip and I'll edit it."

## What it installs

ffmpeg, Node, a Python environment, the render engine and a speech model for captions, all inside `~/video-editor/`, plus the
render browser in `~/.cache/hyperframes`. Nothing needs an admin password and nothing is system-wide. Deleting those two
folders removes it all (their projects live in the first, so warn them first). `--accurate` swaps in a bigger speech model (1.5 GB) for hard names and
accents. `--matte` adds smoother cutouts (about 1 GB).
