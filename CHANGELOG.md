# Changelog

Your style, your projects and your finished videos live in `~/video-editor/`, outside the plugin, so an update never touches them.

## 1.3.0
Faster edits, and fuller ones.
- The cutout (you, cut out so type can sit behind your head) only does the moments that use it, and runs while the
  cards are built instead of holding up the storyboard. On a 66-second video: 3.6 minutes instead of 17. Move a
  moment later and only its new frames are done. The rest of the file is see-through, so every effect lines up as before.
- The cut is about twice as fast and a little sharper: one compression step instead of two.
- The checks after a render run all at once.
- Cards start from one command that sets up the folder, so the card builders spend their time on the card. They
  render while you look at the storyboard, so "go" goes straight to the final render.
- Every edit is held to a fuller bar: a designed moment on every beat, about a third of the video full screen (cards,
  your clips, effects that fill the frame), and 3 to 4 effects a minute from the starter pack. The storyboard counts it.
- Claude asks once for screen recordings of what you talk about and screenshots public pages itself.
- Send a reel you like and the edit borrows its pacing: how long shots last, how often the picture changes, how
  much is full screen. It never copies its words or look.

## 1.2.1
Fixes from setting up a real brand's style.
- The style board shows your caption preset the way your videos get it: its size, outline and rhythm. Before, its
  sample captions ignored the preset, and with `one-word` the showcase caption ran off both sides of the frame.
- Captions take your brand's light and dark, never pure white or black, so brands that ban them stay on-brand.
- `bold-outline` and `one-word` use your caption font's own weight, the one setup downloads, instead of a 900 most
  fonts weren't downloaded in.
- No more Pillow warning while setup builds the board.

## 1.2.0
The starter pack: the twenty effects from the "20 Video Effects Created by Claude" reel now come built in, so a new
edit can look good from the first try.
- Nineteen new hand-built effects: orbit, chat takeover, frame escape, snap zoom, checklist pop, headline storm, zoom
  portal, growth curve, studio reveal, b-roll overlay, paper cutout, dolly zoom, liquid glass, zoom through cut, green
  screen, frame break, digital zoom, phone mockup and checklist. With the magazine cover that was already there, that's
  all twenty. 244 effects in all.
- Ask for any hand-built effect by name and the build copies it into the project by itself. No more copying folders.
  `like="<name>"` uses one twice in a video.
- Effects that need words (headlines, the chat prompt, the checklist) take them from what you said, so the defaults work.
- A worked example, `engine/examples/effects/edit.py`, uses all twenty on one video.
- The README opens with a step-by-step quick start.

## 1.1.0
Fixes from editing real videos end to end in studio and flex. After updating, Claude runs setup once more by itself.
- The long steps (cutout, render, the first transcription) keep running if Claude's session ends partway, and asking
  again waits for the running one instead of starting over. Before, a cutout could die with the session and the edit
  stopped short of the storyboard.
- A finished cutout isn't redone for the same cut.
- Your style file now carries your name and your colour, not the preset's.
- Any brand colour keeps "losses" clearly apart from it.
- Captions over a light card turn dark, the way the rest of the card's type does, and end where the card ends.
- Words behind the head drop a trailing comma.
- The lip-sync check no longer fails on the last second of a clip.
- Card builders check their card reads in the order it's said and the main number fills the width.

## 1.0.0
First release.
- One clip in, one finished vertical video out, with a storyboard to approve first.
- Three edits: studio, selfie, flex.
- 225 effects usable by name in any edit: 159 picture and 17 audio effects from the verified library, 40 hand-built moments, 9 data cards.
- All 27 transitions work on real cuts of a single take.
- Handles iPhone HDR, variable frame rate and rotated clips by itself.
- First pass at the cut: pauses, fillers, retakes.
- Six caption styles and six style presets, with any brand colour adjusted to stay readable.
- Other sizes (4:5, 1:1, 16:9), covers, caption files and post copy.
- Long video to short clips.
- A flash check on every render.
