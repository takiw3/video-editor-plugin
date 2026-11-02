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


class Post(unittest.TestCase):
    def test_srt(self):
        w = [dict(text=t, start=i * .5, end=i * .5 + .4) for i, t in enumerate("Hello there. This is a test of the captions file.".split())]
        s = postpack.srt(w)
        self.assertIn("00:00:00,000 --> 00:00:00,900\nHello there.", s)


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
