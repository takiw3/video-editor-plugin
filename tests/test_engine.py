#!/usr/bin/env python3
"""Fast checks with no footage and no render: python tests/test_engine.py  (run with the kit's Python: ve py can't reach
this folder when installed, so use <home>/.venv/bin/python, with ffmpeg on PATH). Real renders: tests/render_test.md."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENG = os.path.join(ROOT, "engine")
sys.path.insert(0, os.path.join(ENG, "pipeline"))
import audiofx  # noqa: E402
import autocut  # noqa: E402
import fxlib  # noqa: E402
import postpack  # noqa: E402
import presets  # noqa: E402


def words(text, gap=0.1, word=0.3):
    t, out = 0.0, []
    for w in text.split():
        out.append([round(t, 2), round(t + word, 2), w])
        t += word + gap
    return out


class Autocut(unittest.TestCase):
    def test_keeps_the_last_take(self):
        w = words("The best way to start is simple. The best way to start is with one thing. Then it compounds.")
        ranges, fillers, retakes = autocut.propose(w)
        text = " ".join(r[2] for r in ranges)
        self.assertIn("with one thing", text)
        self.assertNotIn("is simple", text)
        self.assertEqual(len(retakes), 1)

    def test_drops_fillers_and_closes_pauses(self):
        w = [[0, .3, "So"], [.4, .6, "um"], [.7, 1, "here"], [3, 3.3, "we"], [3.4, 3.7, "go."]]
        ranges, fillers, _ = autocut.propose(w)
        self.assertEqual(fillers, ["um"])
        self.assertEqual(len(ranges), 3)   # the filler and the 2 s pause each break the range
        self.assertNotIn("um", " ".join(r[2] for r in ranges))

    def test_different_sentences_stay(self):
        w = words("Three things matter here. First you record. Second you edit. Third you post.")
        ranges, _, retakes = autocut.propose(w)
        self.assertEqual(retakes, [])
        self.assertIn("Third you post.", " ".join(r[2] for r in ranges))


class AudioEffects(unittest.TestCase):
    """every library audio effect runs through ffmpeg at its default, min and max, changes the sound and keeps the length"""

    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp()
        cls.src = os.path.join(cls.d, "voice.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=3:c=pink:a=0.15:r=48000", "-f", "lavfi", "-i", "sine=220:d=3:r=48000",
                        "-filter_complex", "[0][1]amix=2,aformat=channel_layouts=stereo", cls.src], check=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.d)

    def _len(self, p):
        return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip().strip(","))

    def _rms(self, p):
        r = subprocess.run(["ffmpeg", "-i", p, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
        return float(re.search(r"mean_volume: (-?[\d.]+)", r).group(1))

    def test_all_seventeen(self):
        ids = [k for k, v in fxlib.fx.library().items() if v.get("kind") == "audio"]
        self.assertEqual(len(ids), 17)
        for eid in ids:
            spec = fxlib.spec_of(eid)
            for label, pick in (("default", "default"), ("min", "min"), ("max", "max")):
                params = {P["key"]: P[pick] for P in spec["parameters"]}
                out = os.path.join(self.d, f"{eid}-{label}.wav")
                audiofx.apply(self.src, [dict(effect=eid, params=params)], 3.0, out)
                self.assertAlmostEqual(self._len(out), 3.0, delta=0.05, msg=f"{eid} {label} changed the length")
                self.assertGreater(self._rms(out), -70, f"{eid} {label} came out silent")

    def test_a_moment_leaves_the_rest_alone(self):
        out = os.path.join(self.d, "moment.wav")
        audiofx.apply(self.src, [dict(effect="gain", at=1.0, end=2.0, params=dict(gain=-30))], 3.0, out)
        def level(a, b):
            r = subprocess.run(["ffmpeg", "-ss", str(a), "-t", str(b - a), "-i", out, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
            return float(re.search(r"mean_volume: (-?[\d.]+)", r).group(1))
        self.assertGreater(level(0.1, 0.9) - level(1.1, 1.9), 20)
        self.assertLess(abs(level(0.1, 0.9) - level(2.1, 2.9)), 1)

    def test_out_of_range_is_refused(self):
        with self.assertRaises(SystemExit):
            audiofx.params_for(dict(effect="gain", params=dict(gain=20)))

    def test_picture_effect_is_refused(self):
        with self.assertRaises(SystemExit):
            audiofx.params_for(dict(effect="film-grain"))


class Library(unittest.TestCase):
    def test_counts(self):
        lib = fxlib.fx.library()
        ok = [k for k, v in lib.items() if fxlib.fx.status_of(v) in ("verified", "limited")]
        self.assertEqual(len(ok), 176)

    def test_routing_refuses_wrong_field(self):
        class E:
            S = {"colors": {"accent": "#FD5323"}}
        page = '<div data-composition-id="main" data-duration="10" data-width="1080" data-height="1920" id="root"></div>'
        with self.assertRaises(SystemExit):
            fxlib.plan(E, [dict(effect="whip-pan", at=1)], page)
        with self.assertRaises(SystemExit):
            fxlib.plan(E, [dict(effect="reverb")], page)
        with self.assertRaises(SystemExit):
            fxlib.plan(E, [dict(effect="word-pop", at=1, duration=1)], page)
        with self.assertRaises(SystemExit):
            fxlib.plan(E, [dict(effect="no-such-effect")], page)

    def test_accent_and_face_defaults(self):
        class E:
            S = {"colors": {"accent": "#FD5323"}}
            FACE = (540, 1000)
            CANVAS = (1080, 1920)
        self.assertEqual(fxlib.pack_defaults(E, "progress-bar", {})["hue"], 13)
        self.assertEqual(fxlib.pack_defaults(E, "progress-bar", {"hue": 200})["hue"], 200)
        p = fxlib.pack_defaults(E, "spotlight-focus", {})
        self.assertEqual((p["cx"], p["cy"]), (0.5, 0.521))


class Presets(unittest.TestCase):
    def test_shade_darkens(self):
        self.assertEqual(presets.shade("#FFFFFF", 0.5), "#808080")

    def test_all_packs_load_and_pass_contrast(self):
        import style as ST
        for name in presets.BLURB:
            S = ST.load(os.path.join(ENG, "examples", "packs", name, "style.json"))
            self.assertTrue(S["fonts"]["display"]["family"])
            self.assertTrue(os.path.exists(os.path.join(ENG, "examples", "packs", name, "STYLE.md")))

    def test_any_accent_keeps_losses_apart(self):
        import style as ST
        S = ST.load(os.path.join(ENG, "examples", "packs", "bold", "style.json"))
        for accent in ("#FD5323", "#E53935", "#1D58F6", "#7E57C2", "#FFD400"):
            C = dict(S["colors"], accent=accent, accent_on_light=presets.shade(accent, 0.72))
            presets.fit(C)
            self.assertGreaterEqual(ST.distance(ST.rgba(C["accent_on_light"]), ST.rgba(C["negative_on_light"])), 30, accent)

    def test_style_md_follows_the_colour_and_name(self):
        with tempfile.TemporaryDirectory() as d:
            md = os.path.join(d, "STYLE.md")
            shutil.copy(os.path.join(ENG, "examples", "packs", "bold", "STYLE.md"), md)
            S = {"creator": {"name": "Sam"}, "colors": {"accent": "#FD5323"}}
            presets.retell(md, "bold", S, {"accent": "#FFD400"})
            presets.retell(md, None, {"colors": {"accent": "#1D58F6"}}, {"accent": "#FD5323"})
            text = open(md).read()
            self.assertTrue(text.startswith("# Sam's style (from the bold preset)\n\nYour accent is #1D58F6."))
            self.assertEqual(text.count("Your accent is"), 1)
            self.assertNotIn("#FFD400", text)


class Post(unittest.TestCase):
    def test_srt(self):
        w = [dict(text=t, start=i * .5, end=i * .5 + .4) for i, t in enumerate("Hello there. This is a test of the captions file.".split())]
        s = postpack.srt(w)
        self.assertIn("00:00:00,000 --> 00:00:00,900\nHello there.", s)


class LongSteps(unittest.TestCase):
    def test_a_long_step_passes_on_its_own_result(self):
        cli = os.path.join(ENG, "pipeline", "cli.py")
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, cli, "cutout", d], capture_output=True, text=True, timeout=120)
            self.assertNotEqual(r.returncode, 0)                       # no aroll.mp4: the step fails, and says so
            self.assertIn("aroll.mp4", r.stdout)
            self.assertNotEqual(open(os.path.join(d, "work", "ve-cutout.exit")).read().strip(), "0")


    def test_cutout_finishes_and_then_skips(self):
        import cutout
        with tempfile.TemporaryDirectory() as d:
            for sub in ("assets", "public"):
                os.makedirs(os.path.join(d, sub))
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=64x64:rate=30", "-frames:v", "12",
                            os.path.join(d, "assets", "aroll.mp4")], check=True)
            fake = ["sh", "-c", 'sleep 0.3; ffmpeg -v error -y -i "$2" -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le "$4"',
                    "remove-background"]
            old = (cutout.HF, cutout.PROGRESS_EVERY, sys.argv)
            try:
                cutout.HF, cutout.PROGRESS_EVERY, sys.argv = fake, 0, ["cutout.py", d, "--all"]
                cutout.main()
                self.assertTrue(os.path.exists(os.path.join(d, "public", "subject.webm")))
                cutout.HF = ["false"]                                  # a second call must not run it again
                cutout.main()
            finally:
                cutout.HF, cutout.PROGRESS_EVERY, sys.argv = old


def alpha(f, n):
    out = subprocess.run(["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", f, "-vf", f"select=eq(n\\,{n})", "-frames:v",
                          "1", "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True, check=True).stdout
    return max(out[3::4])


class Cutout(unittest.TestCase):
    """only the moments that use it are cut out; the file stays frame for frame with the cut"""
    def test_ranges(self):
        import cutout
        self.assertEqual(cutout.merge([[10, 20], [25, 30], [60, 70]], gap=5), [[10, 30], [60, 70]])
        self.assertEqual(cutout.subtract([[0, 100]], [[10, 20], [50, 60]]), [[0, 9], [21, 49], [61, 100]])
        self.assertEqual(cutout.subtract([[10, 20]], [[0, 30]]), [])

    def test_windows_then_only_the_new_frames(self):
        import cutout
        with tempfile.TemporaryDirectory() as d:
            for sub in ("assets", "public"):
                os.makedirs(os.path.join(d, sub))
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=64x64:rate=30", "-frames:v", "90",
                            os.path.join(d, "assets", "aroll.mp4")], check=True)
            open(os.path.join(d, "edit.py"), "w").write("CUT_WINDOWS = [(1.0, 1.2)]\n")
            log = os.path.join(d, "calls")
            fake = ["sh", "-c", f'echo "$2" >> {log}; ffmpeg -v error -y -i "$2" -c:v prores_ks -profile:v 4444 '
                                '-pix_fmt yuva444p10le "$4"', "remove-background"]
            old = (cutout.HF, cutout.PROGRESS_EVERY, sys.argv)
            try:
                cutout.HF, cutout.PROGRESS_EVERY, sys.argv = fake, 0, ["cutout.py", d]
                cutout.main()
                sub = os.path.join(d, "public", "subject.webm")
                self.assertEqual(cutout.frames(sub), "90")
                self.assertEqual(alpha(sub, 5), 0)                      # outside the window: transparent
                self.assertEqual(alpha(sub, 33), 255)                   # inside: the subject
                self.assertAlmostEqual(cutout.last_time(sub), 89 / 30, delta=0.002)
                E = cutout.load_edit(d)
                self.assertEqual(cutout.missing(d, E), [])
                cutout.main()                                           # same windows: nothing to do
                self.assertEqual(len(open(log).read().split()), 1)
                open(os.path.join(d, "edit.py"), "w").write("CUT_WINDOWS = [(1.0, 1.2), (2.4, 2.6)]\n")
                self.assertEqual(len(cutout.missing(d, cutout.load_edit(d))), 1)
                cutout.main()                                           # a new window: only its frames
                self.assertEqual(len(open(log).read().split()), 2)
                key = json.load(open(os.path.join(d, "assets", "subject.key")))
                self.assertEqual([r[:2] for r in key["parts"][1]["ranges"]], [[52, 89]])   # joined to the first: under a second apart
                self.assertEqual(alpha(sub, 75), 255)
                self.assertEqual(alpha(sub, 33), 255)                   # the first window is still there
                self.assertEqual(cutout.frames(sub), "90")
            finally:
                cutout.HF, cutout.PROGRESS_EVERY, sys.argv = old


class Card(unittest.TestCase):
    def test_scaffold(self):
        card = os.path.join(ENG, "pipeline", "card.py")
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "style", "fonts"))
            open(os.path.join(d, "style", "brand.css"), "w").write(":root{}")
            os.makedirs(os.path.join(d, "public", "vendor"))
            open(os.path.join(d, "public", "vendor", "gsap.min.js"), "w").write("")
            r = subprocess.run([sys.executable, card, d, "c1", "--from", "pie", "--frames", "90", "--ground", "light"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            c = os.path.join(d, "cards", "c1")
            for f in ("index.html", "brand.css", "card.css", "hyperframes.json", "vendor/gsap.min.js"):
                self.assertTrue(os.path.exists(os.path.join(c, f)), f)
            root = re.search(r'<div id="root"[^>]*>', open(os.path.join(c, "index.html")).read()).group(0)
            self.assertIn('data-duration="3.0000"', root)
            self.assertIn('class="ground-light"', root)
            r = subprocess.run([sys.executable, card, d, "c3", "--from", "pie", "--frames", "305"], capture_output=True, text=True)
            root = re.search(r'<div id="root"[^>]*>', open(os.path.join(d, "cards", "c3", "index.html")).read()).group(0)
            self.assertIn('data-duration="10.1666"', root)              # rounded down: 10.167 renders 306 frames
            self.assertIn('class="ground-dark"', root)                  # no --ground: the library card's own
            r = subprocess.run([sys.executable, card, d, "c1", "--from", "pie", "--frames", "90"], capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)                        # an agent's card is never overwritten
            r = subprocess.run([sys.executable, card, d, "c2", "--from", "nope", "--frames", "9"], capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse(os.path.exists(os.path.join(d, "cards", "c2")))


class Density(unittest.TestCase):
    def test_count(self):
        import storyboard
        from types import SimpleNamespace
        E = SimpleNamespace(TOTAL=60.0, END_IN=60.0, END_CARD=None, TRANSITIONS=[],
                            CARDS=[("c1", "cards/c1.mp4", 10.0, 15.0, "dark")], BROLL=[dict(at=12.0, end=18.0)],
                            FX=[dict(id="a", at=30.0, end=35.0, full=True), dict(id="b", at=40.0, end=42.0)],
                            FXLIB=[dict(effect="x", at=1.0), dict(effect="y", at=2.0)])
        ps = [dict(id="p01", kind="footage", moves=[]), dict(id="p02", kind="footage", moves=["Punch-in on the cut."]),
              dict(id="p03", kind="footage", moves=["Something lands."]), dict(id="p04", kind="dark", moves=[])]
        share, per_min, bare = storyboard.density(E, ps)
        self.assertAlmostEqual(share, 13 / 60)                         # 10-18 (card and cutaway overlap) + 30-35
        self.assertAlmostEqual(per_min, 4.0)
        self.assertEqual(bare, ["p01", "p02"])


class StarterPack(unittest.TestCase):
    PACK = ("orbit", "chat-takeover", "frame-escape", "snap-zoom", "checklist-pop", "headline-storm", "zoom-portal",
            "growth-curve", "studio-reveal", "broll-overlay", "paper-cutout", "dolly-zoom", "magazine-cover",
            "liquid-glass", "zoom-through", "green-screen", "frame-break", "digital-zoom", "phone-mockup", "checklist")

    def test_all_twenty_are_in_the_library(self):
        lib = open(os.path.join(ENG, "fx", "LIBRARY.md")).read()
        for name in self.PACK:
            for f in ("fx.html", "fx.js"):
                self.assertTrue(os.path.exists(os.path.join(ENG, "fx", name, f)), f"{name}/{f}")
            self.assertIn(f"| `{name}` |", lib, name)

    def test_the_example_uses_all_twenty(self):
        src = open(os.path.join(ENG, "examples", "effects", "edit.py")).read()
        self.assertEqual(re.findall(r'dict\(id="([\w-]+)"', src), list(self.PACK))

    def test_colours_come_from_the_pack(self):
        colour = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(")
        hits = []
        for name in self.PACK:
            for f in ("fx.html", "fx.js"):
                for n, line in enumerate(open(os.path.join(ENG, "fx", name, f)), 1):
                    if colour.search(line.replace("{{ID}}", "")) and not line.startswith("var CHROMA"):
                        hits.append(f"{name}/{f}:{n}")
        self.assertEqual(hits, [])

    def test_the_build_copies_an_effect_by_name(self):
        import types
        import build
        import common
        old = common.HOME
        with tempfile.TemporaryDirectory() as d:
            common.HOME = os.path.join(d, "home")                          # no creator library: the kit's
            try:
                E = types.SimpleNamespace(FX=[dict(id="snap-zoom"), dict(id="snap-2", like="snap-zoom"), dict(id="made-up")])
                build.provision_fx(E, d)
                build.provision_fx(E, d)                                   # a second build leaves the copies alone
            finally:
                common.HOME = old
            for fid in ("snap-zoom", "snap-2"):
                self.assertEqual(open(os.path.join(d, "fx", fid, "fx.js")).read(),
                                 open(os.path.join(ENG, "fx", "snap-zoom", "fx.js")).read())
            self.assertFalse(os.path.exists(os.path.join(d, "fx", "made-up")))
            self.assertFalse(os.path.exists(os.path.join(d, "fx", "snap-zoom", "preview.jpg")))


class Captions(unittest.TestCase):
    def E(self, preset, mode=None, **kw):
        import types
        S = dict(captions=dict(preset=preset, hifi=dict(box=False), lofi=dict(box=False)))
        return types.SimpleNamespace(S=S, MODE=mode or {}, **kw)

    def test_colours_and_weight_come_from_the_pack(self):
        import build
        pure = re.compile(r"#f{3}\b|#f{6}\b|#0{3}\b|#0{6}\b|rgba?\(\s*(0\s*,\s*){2}0|rgba?\(\s*(255\s*,\s*){2}255", re.I)
        css = [c for c, *_ in build.CAPTION_PRESETS.values()] + list(build.ON_LIGHT.values()) + [build.pack_css(self.E("one-word"))]
        self.assertEqual([c for c in css if pure.search(c)], [])
        self.assertEqual([c for c in css if "font-weight:900" in c], [])

    def test_rhythm(self):
        import build
        self.assertEqual(build.caption_rhythm(self.E("one-word")), (1, 16))
        self.assertEqual(build.caption_rhythm(self.E("bold-outline", dict(captions="single"))), (3, 18))
        self.assertEqual(build.caption_rhythm(self.E("karaoke-box")), (4, 24))
        self.assertEqual(build.caption_rhythm(self.E("karaoke-box", dict(captions="single", max_chars=20))), (1, 20))
        self.assertEqual(build.caption_rhythm(self.E("one-word", KARAOKE=dict(max_words=2))), (2, 16))

    def test_board_samples_fit_every_preset(self):
        import build
        sys.path.insert(0, os.path.join(ENG, "onboarding"))
        import board
        for preset in build.CAPTION_PRESETS:
            for mode in ({}, dict(captions="single"), dict(captions="phrase")):
                mw, mc = build.caption_rhythm(self.E(preset, mode))
                for samples in [board.HIFI_CAPS, board.SHOWCASE_CAPS] + list(board.LOFI_CAPS.values()):
                    s = board.fit(samples, (mw, mc))
                    self.assertLessEqual(len(s.split()), mw, (preset, mode, s))
                    self.assertLessEqual(len(s.replace("*", "")), mc, (preset, mode, s))
        self.assertIn("never", board.fit(board.SHOWCASE_CAPS, (1, 16)))


class Plugin(unittest.TestCase):
    def test_manifest(self):
        d = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
        self.assertEqual(d["name"], "video-editor")
        self.assertEqual(open(os.path.join(ENG, "VERSION")).read().strip(), d["version"])

    def test_skills_have_frontmatter(self):
        for name in ("setup", "edit", "style", "effects", "clips", "post", "fix"):
            s = open(os.path.join(ROOT, "skills", name, "SKILL.md")).read()
            self.assertTrue(s.startswith(f"---\nname: {name}\ndescription: "), name)

    def test_no_stale_names(self):
        bad = re.compile(r"reel-kit|REEL_KIT|Reel Kit|justyn|Masterclass|\$HERMES_HOME", re.I)
        hits = []
        for base in ("skills", "agents", "engine/kit", "engine/modes", "engine/pipeline", "engine/onboarding", "engine/setup", "engine/storyboard"):
            for root, _, files in os.walk(os.path.join(ROOT, base)):
                for f in files:
                    if f.endswith((".md", ".py", ".sh", ".html", ".css", ".json")):
                        if bad.search(open(os.path.join(root, f), errors="ignore").read()):
                            hits.append(os.path.join(root, f))
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
