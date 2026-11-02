"""Starter pack edit: all twenty effects from the "20 Video Effects Created by Claude" reel on one 47-second video.

The video: the creator names twenty effects one after another and each plays on its own name. Every effect is listed
by its library name, so the build copies it into the project by itself (kit/FX_BRIEF.md); nothing here was set by hand
except the magazine cover's words and layout. Copy the field shapes and the timing pattern (each effect from the word
that names it to the next one), never the content. Every time is on the OUTPUT timeline in seconds, except KEEP.
"""
TITLE = "Twenty Effects"
STYLE = "showcase"                    # hifi (modes/HIFI.md), lofi (modes/LOFI.md) or showcase (modes/SHOWCASE.md)
KIT_VERSION = "1.2.0"
SRC = "~/Videos/twenty-effects/take.mov"
ORIGINAL = SRC

# ---- cut (source seconds): keep ranges from silencedetect, last clean take of every line
KEEP = [(0.0, 47.15)]   # natural pacing: each effect needs its ~2 s of screen time
# 9:16 crops of the source (w, h, x, y): seeded from its size, then measure on a frame of THIS shoot (face, eyes, chin)
FRAMES = {"WIDE": (1080, 1920, 0, 0), "CLOSE": (864, 1536, 108, 192)}
SHOTS = [(0.000, "WIDE")]           # add CLOSE/WIDE changes; hide them under cards where you can
HOLD = 0.5                         # picture after the last word: hi-fi 0.6 (1.3 with an end card), lo-fi 0.04
FIXES = {}                         # transcription mishearings -> the real word
PROMPT = ""                         # names, products and numbers in the script, to help transcription

# ---- after words.py: captions (start, text, kind[, end]); kinds "", "big", "thesis", "strike"; *word* = accent
CAPS = []
HOOK = None                         # dict(eyebrow=, h1=, h2=, off=, shot_end=[, tag=])
BEHIND = []                         # moments behind the speaker's head
CUT_WINDOWS = [(9.18, 11.28), (16.00, 18.18), (20.34, 24.88), (26.58, 34.48), (38.54, 40.14)]   # the behind-layer effects
BW = []                             # black-and-white beats, at most two
CAMERA = dict(settles=[], open=(1.0, 0.01), zooms=[])
CARDS = []                          # (id, "cards/<id>.mp4", start, end, "light"|"dark", "what it shows")
END_CARD = None                     # opt-in only
TYPE = lambda t, db, n: dict(at=t, name="typing", db=db, max_len=n, align="start")   # noqa: E731  typing runs from its start
SOUND = dict(music=None, sfx=[       # one event, one sound; times are when each one hits
    (5.52, "whoosh-soft", -20), (5.62, "pop", -18), (5.74, "pop", -19), (5.86, "pop", -19),                 # orbit
    (6.86, "whoosh-soft", -19), TYPE(7.37, -24, 1.3), (8.82, "whoosh-soft", -20),                         # chat takeover
    (9.20, "whoosh-soft", -19), (9.52, "stamp", -17), (10.96, "whoosh-soft", -21),                        # frame escape
    (11.38, "impact-low", -15), (11.93, "whoosh", -17), (11.93, "impact-low", -16),                       # snap zoom
    (13.81, "pop", -17), (13.89, "tick", -16), (14.64, "pop", -17), (14.72, "tick", -16),                 # checklist pop
    (16.19, "stamp", -19), (16.46, "stamp", -19), (16.73, "stamp", -19), (17.00, "stamp", -19), (17.27, "stamp", -19),
    (18.66, "whoosh-soft", -19), (19.65, "whoosh-deep", -16),                                             # zoom portal
    (20.36, "switch-off", -20), (20.94, "riser", -21), (22.04, "ding", -20),                              # growth curve
    (22.56, "switch-off", -18), (23.14, "click", -16), (23.34, "click", -17), (23.59, "ding", -21),       # studio reveal
    (24.90, "whoosh-soft", -20), (25.10, "click", -19),                                                   # b-roll overlay
    (26.62, "stamp", -17), (26.70, "pop", -19), (26.85, "pop", -20),                                      # paper cutout
    (29.30, "riser-long", -22),                                                                           # dolly zoom
    (31.70, "whoosh-soft", -20), (31.75, "clicks-run", -22, 0.4), (32.52, "stamp", -17),                  # magazine cover
    (34.56, "whoosh-soft", -21), (35.30, "whoosh-soft", -23),                                             # liquid glass
    (36.95, "whoosh-long", -18), (37.24, "impact-low", -15),                                              # zoom through
    (38.62, "whoosh", -18), (39.95, "whoosh-soft", -20),                                                  # green screen
    (40.54, "impact-low", -14), (40.76, "boom-low", -16),                                                 # frame break
    (41.90, "click", -20), (41.94, "shutter", -17), (42.32, "shutter", -17),                              # digital zoom
    (43.60, "whoosh-soft", -19), (45.10, "whoosh-soft", -20),                                             # phone mockup
    (45.46, "whoosh-soft", -20), (45.79, "clicks-run", -21, 1.46),                                        # checklist
])
CARD_SFX = []
NEEDS = []                          # (beat id, what the creator should send: a screenshot, a clip, a logo)
GENERATED = []                      # (beat id, what a connected generator made, which model); empty without one

# ---- the library (kit/EFFECTS.md): any mode can use these
FACE = (494, 1082)                         # (x, y) of the face on the 1080x1920 frame; seeded automatically, check it on a still
CAPTION_Y = 1385                    # top of the captions: just under the chin; None uses the pack's
HEAD_TOP = 689                     # where the hair starts on the WIDE shot: big words behind the head sit so the head breaks them
FXLIB = []                          # dict(effect=, at=, duration=, params=) looks, camera, overlays, text, layouts
TRANSITIONS = []                    # dict(effect=, at=<a picture cut>) on real cuts; run `ve transitions` before the render
AUDIO_FX = []                       # dict(effect=, at=, end=, params=) on the voice
BROLL = []                          # dict(src="media/x.mp4", at=, end=) full-screen cutaways, captions stay on top
CAPTION_STYLE = None                # a preset from kit/CAPTIONS.md; None uses the pack's
LANGUAGE = None                     # "en", "es", ...; None detects it

# ---- showcase (modes/SHOWCASE.md): the lo-fi type system + one hand-built motion graphic per beat
KARAOKE = dict(huge=[], hide=[(6.84, 9.18), (43.56, 45.44), (45.44, 47.65)])   # the chat, the phone, the checklist
BOXES = [dict(text="20 Video Effects\nCreated by Claude", at=0.0, end=5.50, note="Hook box from frame 0.")]
OVERLAYS = []
FX = [                              # each effect from the word that names it to the next one (every library effect, by name)
    dict(id="orbit", layer="top", at=5.50, end=6.84, frames=[5.9, 6.5]),
    dict(id="chat-takeover", layer="cam", at=6.84, end=9.18, frames=[7.6, 8.6]),
    dict(id="frame-escape", layer="behind", at=9.18, end=11.28, frames=[9.8, 10.7]),
    dict(id="snap-zoom", layer="top", at=11.28, end=13.62, frames=[11.6, 12.9]),
    dict(id="checklist-pop", layer="top", at=13.62, end=16.00, frames=[14.4, 15.4]),
    dict(id="headline-storm", layer="behind", at=16.00, end=18.18, frames=[16.8, 17.7]),
    dict(id="zoom-portal", layer="cam", at=18.18, end=20.34, frames=[18.9, 19.9]),
    dict(id="growth-curve", layer="behind", at=20.34, end=22.54, frames=[21.2, 22.1]),
    dict(id="studio-reveal", layer="behind", at=22.54, end=24.88, frames=[23.4, 24.3]),
    dict(id="broll-overlay", layer="top", at=24.88, end=26.58, frames=[25.4, 26.1]),
    dict(id="paper-cutout", layer="behind", at=26.58, end=29.24, frames=[27.2, 28.5]),
    dict(id="dolly-zoom", layer="behind", at=29.24, end=31.64, frames=[29.6, 31.2]),
    dict(id="magazine-cover", layer="behind", at=31.64, end=34.48, frames=[32.6, 34.0]),
    dict(id="liquid-glass", layer="top", at=34.48, end=36.80, frames=[35.2, 36.1]),
    dict(id="zoom-through", layer="top", at=36.80, end=38.54, frames=[36.9, 37.6]),
    dict(id="green-screen", layer="behind", at=38.54, end=40.14, frames=[39.0, 39.8]),
    dict(id="frame-break", layer="cam", at=40.14, end=41.86, frames=[40.3, 40.8]),
    dict(id="digital-zoom", layer="top", at=41.86, end=43.56, frames=[42.2, 43.0]),
    dict(id="phone-mockup", layer="cam", at=43.56, end=45.44, frames=[44.3, 45.0]),
    dict(id="checklist", layer="top", at=45.44, end="end", frames=[46.2, 47.3]),
]
GRADES = []                         # (start, end, "warm"|"moody"|css filter): looks the script asks for
J_LEADS = None                      # per-join J-cut leads, when one shot must stop early (a lean-in to the phone)
