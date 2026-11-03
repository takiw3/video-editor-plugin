# Effects: what goes where

Four fields in edit.py. Name the effect and the moment; the build works out the rest. `ve effects show <name>` gives any effect's
settings and ranges. A value outside a range is refused, because it was never tested.

## FXLIB: the verified library
```python
FXLIB = [
    dict(effect="film-grain", params=dict(amount=0.15)),             # no window: the whole video
    dict(effect="vignette", params=dict(amount=0.3)),
    dict(effect="digital-glitch", at=5.55, duration=0.35),           # a moment
    dict(effect="crash-zoom", at=12.0, duration=0.6),                # camera: moves footage and behind-head graphics together
    dict(effect="confetti-burst", at=40.0, duration=1.8),            # overlay: under the captions
    dict(effect="word-pop", text="Three things", at=2, duration=2, y=300, size=120),   # text: makes its own element
    dict(effect="lower-third", at=3.0, duration=3, text="Sam Lee|Founder"),
    dict(effect="split-screen-stack", src="media/screen.mp4", at=8, duration=4),       # layouts: src is the second layer
    dict(effect="spotlight-focus", at=19, duration=2),               # aims at FACE
]
```
Any move or frame also works on their own clip or photo: `dict(effect="ken-burns-pan", src="media/photo.jpg", at=8, duration=3)` plays full frame, and adding `x`, `y`, `w`, `h`
places it (`photo-card`, `slow-push`). `blur-fill-reframe` with `src` fits a landscape screen recording into the frame over a blurred copy of itself.

Colours follow the creator's accent automatically (`progress-bar`, `lower-third`, `light-leak-glow`, confetti and more), and an explicit
value wins. Text effects take `x`, `y`, `w`, `size`, `align`, `color`. Media goes in `public/media/`.

## TRANSITIONS: on picture cuts
```python
TRANSITIONS = [dict(effect="whip-pan", at=8.3), dict(effect="zoom-through", at=25.6, duration=0.5)]
```
`at` is a picture cut or reframe from `timeline.json`. Each is pre-rendered as its own short clip (`ve transitions`, a few seconds each, cached)
and hard-cut over the footage, under the captions. The voice runs underneath, so lip sync can't move. One style per video, unless it's a flex edit.
They cover graphics behind the head for their length.

## AUDIO_FX: on the voice
```python
AUDIO_FX = [dict(effect="reverb", at=12.0, end=14.5, params=dict(size=0.8, wet=0.5)), dict(effect="low-pass", at=30, end=33)]
```
Runs before the mix. The voice's length never changes. No window means the whole voice. These are moments, so use them on a word, never for clean-up: the
cut already cleans the voice (noise, EQ, compression, level). `pitch-shift` on someone's real voice for more than a joke beat changes how they
sound. Ask first.

## FX: hand-built moments
`fx/LIBRARY.md`, contract `kit/FX_BRIEF.md`. Designed moments keyed to words: receipt printer, keycaps, magazine cover, projected film. Add
`dict(id=, layer=, at=, end=)` to `FX` (`like="<folder>"` when the id isn't the folder name): the build copies the library folder into
`<project>/fx/<id>/` the first time, and you change the constants there. Works in any mode, and a flex edit lives on them.
`full=True` on an entry that fills the frame (a chat takeover, a phone mockup, a studio reveal) counts it as full screen
in the storyboard's density line.

**Starter pack.** The twenty effects from the "20 Video Effects Created by Claude" reel work with no setup beyond a window on their word:
`orbit`, `chat-takeover`, `frame-escape`, `snap-zoom`, `checklist-pop`, `headline-storm`, `zoom-portal`, `growth-curve`, `studio-reveal`,
`broll-overlay`, `paper-cutout`, `dolly-zoom`, `magazine-cover`, `liquid-glass`, `zoom-through`, `green-screen`, `frame-break`, `digital-zoom`,
`phone-mockup`, `checklist`. The `behind` ones need the cutout and a `CUT_WINDOWS` entry over the window. `examples/effects/edit.py` uses all twenty.

## What doesn't combine
- **A look on the footage reaches what's behind the head**, because it's the same layer. A black-and-white moment turns a coloured title grey. Time looks
  to beats with nothing behind, or do it on purpose.
- **Whole-video looks: one grade, plus at most grain and a vignette.** The pack's `grade` is already a grade. Set it to "none" when a library look carries the video.
- **Text effects split their element into spans.** Give them their own (`text=`), never a caption or a hook box.
- **Camera effects** stack with `CAMERA`, since they sit on a wrapper around it. Two big moves on the same beat look like a mistake, though.
- **Some effects distort a face** (`wave-warp`, `self-displace`, `kuwahara-paint`, `ascii-art`): short moments only, never on a line that needs trust.
- **Made for wide video**: `letterbox-bars` leaves a slot across a vertical video, so don't use it for more than a joke. `chroma-softening`, `blur`, `unsharp-sharpen` and `tilt-shift` are subtle at their defaults: raise them or skip them.
- **Green screen keys** need real green or blue footage and something behind (`BEHIND` backdrop). A blue shirt on a blue key disappears.
- **Flash**: every render is measured against WCAG 2.3.1. A fail blocks delivery. `flash-through-white`, `digital-glitch`, `glitch-cut`, `camera-shake`, `whip-pan`,
  `zoom-through`, `push-slide` are safe at their defaults but add up if stacked close together. Don't chain them.

## Where they came from, and what's verified
The library (159 picture, 17 audio) is the set from the Hermes video editor: each one rendered at its default, minimum and maximum, twice, seeked alone, with no network and
a flash reading, on HyperFrames 0.8.183, plus a full-size smoke test on a real talking-head page in this plugin. Top picks were reviewed at 1080x1920 on real footage. Hand-built
effects and cards come from the kit this engine started from. All of them were smoke-tested on 0.8.183, and they ship with sample words and placeholders, so review each one on its own video's stills.
Audio effects keep the library's ids and ranges but run through ffmpeg here, so a moment starts and stops on a word; they're tested separately at default, minimum and maximum for length and sound (`tests/`), by measurement, not by ear.
