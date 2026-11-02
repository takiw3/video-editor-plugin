# Changelog

Your style, your projects and your finished videos live in `~/video-editor/`, outside the plugin, so an update never touches them.

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
