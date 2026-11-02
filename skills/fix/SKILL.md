---
name: fix
description: Works out what's wrong when the video editor fails or a video comes out wrong, and fixes it. Use on /video-editor:fix, or when someone says it's broken, stuck, won't render, there's no sound, the captions are off, or the colours look washed out.
---

# Fix it

The person sees a problem, not a cause. Find the cause, fix it, tell them in one line what it was.

1. Run `VE doctor` (`~/video-editor/bin/ve`), adding the project folder when a video is involved: `VE doctor <project>`. If
   `ve` doesn't exist, setup never finished: run the `setup` skill.
2. Match what they describe:

| They see | Likely cause | Do this |
|---|---|---|
| Washed out, grey colours | HDR clip that skipped the working copy | `VE probe <clip>`; if HDR, start a new project from the clip, which converts it |
| Voice and lips drift | variable frame rate, or a project cut before an edit | `VE probe`, then `VE cut` and `VE words` again |
| Captions wrong words | names misheard | add the name to `PROMPT` and `FIXES` in edit.py, `VE words`, rebuild |
| Captions in the wrong place | `CAPTION_Y` | look at a still, set it just under the chin |
| Render fails: "browser" | the render browser | run setup again; it tests and repairs the browser |
| Render fails: out of memory, killed | too much at once | close other apps, render again; say so plainly |
| Flash check fails | a glitch or flash effect too fast | soften or remove the effect at the time it names, render again |
| QA "out of sync" under graphics | a false alarm when graphics cover the face | check that frame by eye |
| Effect refused | a setting out of range, or it needs a `src` or `text` | `VE effects show <name>` and follow it |
| Files vanish mid-job on a Mac | iCloud moved them off the disk | keep projects in `~/video-editor`, which isn't synced |

3. Fix what you can and rerun the step. Don't change what the video says or looks like to get past an error.
4. Still stuck after two honest tries: say what failed, what you tried and what you'd need. Point out what still works.
