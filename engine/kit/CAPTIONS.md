# Caption styles

Set `captions.preset` in the style pack, or `CAPTION_STYLE` in one video's edit.py. All are word-timed from the transcript, in any mode, as long as `CAPS` is empty.
`CAPTION_Y` puts them just under the chin (seeded by `ve new`, never below y 1470 where the app's buttons sit).

| Preset | What it looks like | Use it for |
|---|---|---|
| `karaoke-box` | A dark box; words light up as they're spoken | The safe default, works over any background |
| `phrase-box` | A dark box; short phrases land whole | Calm, educated, editorial feel |
| `bold-outline` | Heavy caps with a thick outline, the live word in the accent colour | Fast tips, hooks, high-energy videos |
| `one-word` | One huge word at a time, popping in | Short punchy videos, under 30 seconds |
| `active-pill` | Plain words, the live word in an accent pill | Tech, explainers, modern brands |
| `plain-shadow` | Clean white text, soft shadow, no box | Minimal looks, when the picture should breathe |

Hand-written `CAPS` (studio mode) are the other option: 2 to 4 word phrases with `*word*` for the accent, `big` for numbers, `thesis` for the display face, `strike` for what's being negated.

Rules: keep a line under the preset's length so it doesn't run off the frame, and fix every misheard name (`FIXES`, `PROMPT`): a wrong name in a caption is the
fastest way to look careless. Check a caption against the transcript on the storyboard.
