---
name: clips
description: Pulls short vertical clips out of a long video - a podcast, webinar, interview, Zoom call or YouTube video - picks the moments that stand alone, and edits the ones the person chooses. Use on /video-editor:clips, or when someone has a long video and wants shorts or reels from it.
---

# Long video to short clips

Commands run through `VE` = `~/video-editor/bin/ve`. If it doesn't exist, run the `setup` skill first.

1. **Get the file.** A local file they own or have rights to. `VE probe <file>` says what it is. Other people on camera (a
   guest, a client): ask once whether they're OK with being in the clips.
2. **Transcribe once.** `VE new <slug>-source <file> "<Title>" --mode lofi`, then `VE autocut <project>` transcribes the whole
   thing into `work/autocut_words.json` (it won't change anything without `--write`). Long files take a few minutes:
   say so and run it in the background.
3. **Find the moments.** Read the transcript and pick 3 to 7 passages of about 20 to 60 seconds that hold one complete idea:
   the opening line works with no setup, it says something specific, and it ends on a point. For each give the
   timecodes, the opening line verbatim, why it stands alone, and what context it loses.
4. **The honesty check.** A clip must not change what the person meant. A joke, a hypothetical or a "people say X, but"
   cut down to X is out. Name any you dropped for this.
5. **Show the list as candidates** and let them choose. Don't start editing until they do.
6. **Edit each one.** Each is its own project: follow the `edit` skill with `KEEP` limited to that passage. Horizontal
   sources crop around the face automatically (`FRAMES`, seeded by `VE new`). Check the crop on a still, since two people
   on camera need a shot change when the speaker changes. Their style carries over, so the storyboard is the only stop.
7. Batch: approve one storyboard, then offer to apply the same treatment to the rest.
