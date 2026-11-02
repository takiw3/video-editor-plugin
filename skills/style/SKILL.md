---
name: style
description: Builds the creator's video style (fonts, colours, captions, pace) from a brand guide, a website, videos they like or a couple of quick questions, and shows it to approve. Use on /video-editor:style, the first time someone uses the editor, or when they say change my style, my brand, my colours, my captions.
---

# Your style

Every video this plugin makes wears the creator's look. It lives in `~/video-editor/style/`, outside the plugin, so
updates never touch it. Full reference: `${CLAUDE_PLUGIN_ROOT}/engine/onboarding/ONBOARDING.md` and
`${CLAUDE_PLUGIN_ROOT}/engine/kit/STYLE_PACK.md`. Commands run through `VE` = `~/video-editor/bin/ve`. If it doesn't exist,
run the `setup` skill first.

Plain words, one question at a time, no design jargon. Most people should be done in two minutes.

## Start

Style already exists: show their board and ask what they'd like to change, then steps 3 and 4 on the current pack.
Start over only if they ask.

Otherwise ask one question, with a question tool if you have one:

"How do you want to set your look?"
1. **Pick a look for me** (fastest, 30 seconds): ask what they do and who they talk to, then recommend one preset with a
   reason. Then ask for their brand colour, if they have one.
2. **Use my brand**: a website, brand guide, PDF or logo.
3. **Copy the feel of videos I like**: 2 or 3 links or files.

## 1. Pick a look

`VE style --list` shows the presets: default, bold, soft, editorial, minimal, tech. Then write the pack:

`VE style --preset <name> --accent "#hex" --name "<name>" --handle "@handle"`

## 2. Brand or videos

Follow `ONBOARDING.md` steps 1 and 2. A brand file or website sets colours and fonts; videos set pace, captions and
motion. For links: `VE refs ~/video-editor/style/refs <link or file> ...`, read `summary.md`, then look at every contact
sheet it lists. Instagram often needs a login: ask for the saved file when a link fails. Studied videos are evidence and
never content: take the style and leave the identity (no logos, handles, names or signature graphics of the people they
point to). Then write `style.json` and `STYLE.md` (ONBOARDING step 4) and run `VE style`. Fix every WARNING it prints.

Always pick a `captions.preset` (`${CLAUDE_PLUGIN_ROOT}/engine/kit/CAPTIONS.md`).

## 3. Show the board

`VE board` (add `--clip <file>` when they've given you a clip, so they see themselves) -> `~/video-editor/style/board/index.html`.

- Artifact tool available: publish it with every file in `board/files.json`.
- Otherwise: run `VE serve ~/video-editor/style/board` in the background and give them the address.

## 4. Approve

Ask "Does this look like you?" Apply changes to `style.json` and `STYLE.md`, run `VE style` and `VE board`, show it again.
When they say yes: "Saved. Every video from now on uses it." Then ask for their first clip. Old projects keep the
style they were made with.
