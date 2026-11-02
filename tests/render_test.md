# Real-footage checks before a release

1. Clean setup with no tools on PATH: `VIDEO_EDITOR_HOME=/tmp/ve sh engine/setup/setup.sh` ends in READY.
2. `python tests/test_engine.py` with the kit's Python and ffmpeg on PATH.
3. `ve new` on a real HLG iPhone clip: colours look natural next to a straight SDR frame.
4. A project using FXLIB, TRANSITIONS, AUDIO_FX, BROLL, a cutout and a caption preset: `ve render` ends in QA PASS.
5. `tests/smoke_library.py <project> <out dir>` and `tests/smoke_handbuilt.py <project> <out dir>` on a real project with a cut, words and a mix: one page per effect, a snapshot of each, checked by eye.
