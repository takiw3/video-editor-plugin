---
name: effects
description: Shows the video effects library and tries an effect on the person's own footage. Use on /video-editor:effects, or when someone asks what effects there are, wants to see effects, wants a look, transition, zoom, glitch, caption style or sound effect, or asks what something would look like on their video.
---

# Effects

225 effects, all usable by name or by describing what you want. Commands run through `VE` = `~/video-editor/bin/ve`.

## Browse

`VE effects gallery` writes a page with a picture of every effect, a search box and a "top picks" filter:
`~/video-editor/gallery/index.html`.

- Artifact tool available: publish it with every file in `gallery/files.json`, title "Effects library".
- Otherwise: run `VE serve ~/video-editor/gallery` in the background and give them the address.

In text: `VE effects list` (add `--featured`, `--find zoom`, `--group "Move the camera"`). A question about one effect:
`VE effects show <name>`. Keep the answer short: what it does and the kind of moment it suits, never a dump of the list.

## Try one

When they're working on a video, show it on their own footage before committing:
`VE effects try <project> <name> --at <seconds> [--duration 1.5] [--param k=v] [--text "..."]` prints a still. Show it.
Picked moments beat random ones: use a line it suits.

## Picking for someone

They describe a feeling, you pick a name, and you say which and why: "the old-film one" -> `film-look`.
Read `${CLAUDE_PLUGIN_ROOT}/engine/kit/EFFECTS.md` for how each kind goes into an edit and for what doesn't work together.
Effects serve the words. If they want effects on every line of a calm explainer, say it'll hurt, and offer the flex mode
if showing off is the point. The flash check runs on every render, so strobes won't ship even when asked for: say why.
