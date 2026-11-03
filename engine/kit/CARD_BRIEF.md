# Card brief (every card agent reads this, then the creator's STYLE.md, then its own prompt)

You are building one full-screen motion-graphic card for a 1080x1920, 30fps vertical video. The card hard-cuts in
over the speaker while their voice keeps playing; the main edit lays live captions over it. It must look like it
came from the same hand as every other card in the video, and like the creator, not like this kit.

KIT is this repo. PROJECT is the video's folder (your prompt gives both). Every tool below goes through the `ve` command your prompt gives the path of (it brings its own ffmpeg, Node and HyperFrames).
- `PROJECT/style/STYLE.md`: the creator's style in words, with a Hi-fi section that says how their cards should
  feel (read it first). `PROJECT/style/brand.css`: their tokens and fonts.
- `KIT/kit/TOKENS.md`: every token and what it means. `KIT/kit/card.css`: type voices and devices built on them.
- `KIT/cards/LIBRARY.md`: the card patterns, plus the creator's own in `HOME/cards/LIBRARY.md` (on the same name
  theirs wins); start from the closest one when your prompt names it.
- `KIT/kit/template.html`: a working skeleton with `q()`, `tok()`, `draw()` and `count()`.

Start: `ve card PROJECT <id> --from <library card> --frames N --ground light|dark` makes `PROJECT/cards/<id>/` with
the library card, the style pack, card.css, GSAP and hyperframes.json, `data-duration` and the ground already set, and
lists the card's element ids. Then change the data, labels and beat times in its `index.html`. No library card fits:
leave out `--from` and it starts from the template. You only need `TOKENS.md` or `card.css` when the card needs a
token or device its starting card doesn't use.
Never edit KIT, the style pack, or other cards.

## Style rules (hard)
- Every colour and font is a token. No hex, rgb or font names in your card: CSS uses `var(--...)`, JS reads `tok()`.
- Three voices, never swapped: `.display` speaks (titles, big figures, emphasis), `.text` informs (labels),
  `.mono` measures (every number, unit, axis, year, kicker).
- Grounds: `.ground-light` or `.ground-dark` on `#root`, whichever your prompt names.
- Fixed meaning: accent = emphasis, the thing to look at; negative = losses, down; positive = gains, up; ink or
  light = people and plain facts. Use `--c-accent-light`, `--c-neg-light`, `--c-pos-light` on a light ground.
- Hairlines 1.5-3px, corners `var(--radius)`. NO gradients, glows, blur as decoration, drop shadows, glassmorphism,
  emoji, clip art or decorative icons. Simple hairline diagrams are fine.
- Real artifacts first: screenshots of the source, scans of real objects, what the creator sends. A generated
  image only when your prompt hands you one; never make your own.
- No em dashes in on-screen text; use the real minus "−" for negatives.
- Data to scale: areas, lengths and splits are true to the numbers.

## Layout (hard)
- Content in x 70-1010, y 250-1150. y 1170-1430 is the caption band: ground only. Nothing to read below y 1470.
- Phone-readable: key numbers >= 96px, labels >= 30px, footnotes 24px (texture, not essential).
- It reads in the order they say it, top to bottom and left to right: "7 BILLION / AI TOKENS", never "7 / AI TOKENS /
  BILLION". Nothing says the same thing twice: no kicker that repeats the headline.
- The hero (the figure or the line) spans at least 70% of the content width. The idea sits in the middle of y 250-1150,
  not stacked at the top over empty ground.

## Motion
- The creator's `STYLE.md` sets the pace (calm, normal or punchy). Within it:
- Hard cut in: frame 0 already shows the ground and the frame of the idea (axes, outlines, kicker).
- Every key beat lands on its spoken word from your prompt (card seconds, ±0.05s, snapped with `q()`), 2-3 frames
  early so the visual lands as the word does.
- Entrances 0.25-0.5s, `expo.out` / `power3.out`. Lines draw with stroke-dashoffset, bars grow with scale +
  transformOrigin, numbers roll with `count()` (fixed decimals so widths never jitter).
- One slow camera push across the card (`#cam` 1 to 1.02-1.03, ease none). No bounce; a stamp or pop may use
  `back.out(1.4)` at most. Hold the final state to the last frame.

## HyperFrames rules
- Root: `id="root"`, `data-composition-id="main"`, `data-start="0"`, `data-duration` = frames/30 exactly,
  `data-fps="30"`, `data-width="1080"`, `data-height="1920"`. One paused GSAP timeline at `window.__timelines["main"]`.
- Deterministic: no Math.random (seed it), no Date.now, no events. Drive anything computed from one clock tween's
  onUpdate so any seek lands on the right state.
- Never pair a CSS transform with a GSAP tween on the same property; `fromTo` that starts later needs
  `immediateRender:false`; hidden initial states via `gsap.set` outside the timeline.
- No apostrophes in ids, no `<br>` in text.

## Commands
- Look: `ve card PROJECT <id> --look <t1,t2,...>` (your beat seconds) lints, takes a still at each, writes
  `still.jpg` (the final frame) and `sheet.jpg` (every still in a row), and says whether anything sits in the caption
  band. Read both images like a senior motion designer and fix what's off; one or two rounds, not more.
- Render: `ve card PROJECT <id> --render` renders `<id>.mp4` and checks 1080x1920, 30fps and your exact frame count.
- Anything else in the card folder: `ve hf ...` (the pinned HyperFrames CLI).

## Two phases
1. **Storyboard**: build the card, then save `still.jpg` (the final state, 1080x1920) and report its beats. Stop
   there unless your prompt says to render; the creator comments on the storyboard first.
2. **Render** (after their notes): apply them, render the mp4, verify, report.

## Report (short)
The mp4 or still path, exact frame count, every visible event with its card time (for sound design), and anything
you were unsure about. Don't restate the brief.
