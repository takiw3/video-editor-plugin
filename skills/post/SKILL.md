---
name: post
description: Gets a finished video ready to post - cover image, other sizes (feed, YouTube), caption file, and post copy in the creator's voice. Use on /video-editor:post, or when someone asks for a thumbnail, cover, caption, hashtags, a square or 4:5 version, or says the video is ready to post.
---

# Ready to post

Commands run through `VE` = `~/video-editor/bin/ve`. How to write the copy: `${CLAUDE_PLUGIN_ROOT}/engine/kit/POSTING.md`.

1. `VE post <project> renders/<name>.mp4` writes `<name>-post/` next to the render: `cover.jpg`, `cover-4x5.jpg`,
   `captions.srt`, `transcript.txt`. Look at the cover. If the frame is mid-blink or the hook isn't on it, pick a better
   moment with `--cover <seconds>`.
2. Other sizes, only the ones they'll use: `VE export <project> renders/<name>.mp4 --formats 4:5,1:1,16:9`. Look at a
   frame of each: a crop can cut off a hook or a CTA near the edge. If it does, say so and offer a re-edit for that size.
3. Write `post.md` in that folder from `transcript.txt`, following POSTING.md, in their voice (`style/STYLE.md`, and
   past posts if they share them): three caption options, the first comment, the keyword reply if the video has a
   comment CTA.
4. Tell them where it all is and offer to open the folder. Posting stays with them: this plugin doesn't post, even when a
   social tool is connected, unless they ask for that in so many words and confirm the account.

Never promise reach. Nobody can tell them how a video will perform, and that includes you.
