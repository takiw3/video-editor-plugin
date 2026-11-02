# Video Editor for Claude

Drop in a clip you filmed on your phone. Get back a finished video for Reels, TikTok and Shorts, with the pauses gone, captions on, effects on the right words, sound, and your own look. You don't need to know anything about editing.

Everything runs on your computer. Your footage stays there.

## Install

In Claude Code, run these two lines:

```
/plugin marketplace add takiw3/video-editor-plugin
```

```
/plugin install video-editor@takigpt
```

Then type `/video-editor:setup`. Claude gets everything ready, usually in a few minutes depending on your internet. You won't install anything by hand or need an admin password. It downloads about 2 GB.

In Claude Cowork, download `video-editor-plugin.zip` from the [latest release](https://github.com/takiw3/video-editor-plugin/releases/latest), add it from the plugin menu, then ask Claude to set up the video editor.

## Use it

Three steps, and only the first two are once:

1. `/video-editor:setup` gets your computer ready.
2. `/video-editor:style` sets your look. Pick a preset in 30 seconds, point it at your website, or show it videos you like.
3. `/video-editor:edit`, then drag in a clip.

Claude cuts the video and shows you a storyboard: every moment, what's on screen and what you'll hear. Leave a note on anything you want changed. Nothing renders until you say go. Then the finished video lands next to your original clip, with a smaller copy for your phone.

## What's in it

| Command | What it does |
|---|---|
| `/video-editor:edit` | Edit a clip into a finished vertical video |
| `/video-editor:clips` | Pull short clips out of a long video, podcast or webinar |
| `/video-editor:post` | Cover image, feed and YouTube sizes, caption file and post copy |
| `/video-editor:effects` | Browse every effect, or try one on your own footage |
| `/video-editor:style` | Set or change your look |
| `/video-editor:fix` | Something's wrong? It works out what and fixes it |
| `/video-editor:setup` | Get set up, or check things after an update |

**Three edits.** Claude recommends one and you can change it.
- **Studio**: produced, with two framings, full-screen data cards and type behind your head. Best for sit-down videos and numbers.
- **Selfie**: you stay in frame, the real thing lands on top of you or behind you, captions follow your voice word by word. Best for phone clips and tips.
- **Flex**: a different designed effect on every beat. Best when the edit itself is the point.

**225 effects.** Ask for one by name or just describe it ("the old film one", "zoom in hard on that line"). 159 picture effects and 17 voice effects, 40 big designed moments like a receipt printer or a magazine cover, and 9 animated data cards. Every one takes your colours.

**It handles the annoying parts.** iPhone HDR footage that normally comes out grey. Phone clips that drift out of sync. Sideways video. Retakes, pauses and "um"s. Brand colours that wouldn't be readable on screen.

**It checks its work.** Every render gets checked for lip sync, loudness and flashes that can hurt people with photosensitive epilepsy, before you see it.

## What it won't do

It won't post for you, write your script, promise views, copy someone else's video shot for shot, or use a song you don't have the rights to. It'll flag anything private on screen and ask about anyone else on camera.

## What you need

A Mac or Linux computer, about 3 GB of free space, and Claude Code or Claude Cowork. Windows should work through Git Bash but hasn't had the same testing. On an M2 MacBook, a minute of finished video took about 3 minutes to render with no effects, and about 10 with effects and things behind your head, plus the cutout. Close other heavy apps while it renders.

## Removing it

`/plugin uninstall video-editor@takigpt`, then delete the `video-editor` folder in your home folder and `.cache/hyperframes`, where the render browser lives. The `video-editor` folder holds your style and your projects too, so move anything you want to keep first.

## Credits

Built on [Reel Kit](https://github.com/justynberk/reel-kit) by Justyn Berkovits and the effects library from the [Hermes video editor](https://github.com/takiw3/hermes-video-editor-agent), both MIT. Rendering by [HeyGen HyperFrames](https://github.com/heygen-com/hyperframes). Full notices: [NOTICE.md](NOTICE.md).

MIT License.
