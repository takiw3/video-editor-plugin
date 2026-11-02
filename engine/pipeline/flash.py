#!/usr/bin/env python3
"""Flash check: WCAG 2.3.1 general and red flash on a finished video. Fast glitches and white flashes can hurt people
with photosensitive epilepsy, so this runs on every render and a fail stops delivery.
Run: ve flash <video>
"""
import contextlib
import io
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check(path):
    """-> {verdict: pass|warn|fail, text: one plain line, report: the full analysis}"""
    import fxlib
    with contextlib.redirect_stdout(io.StringIO()):
        r = fxlib.fx.flash_analysis(Path(path))
    worst = max((r["general"], r["red"]), key=lambda x: x["flashes"])
    at = worst.get("at", 0)
    if r["result"] == "fail":
        text = (f"{worst['flashes']:g} flashes a second near {at:.1f}s, over the safe limit of 3. Find the effect at that "
                "moment, soften or remove it, and render again.")
    elif r["result"] == "warn":
        text = f"under the limit, but busy near {at:.1f}s ({worst['flashes']:g} flashes a second). Worth a look."
    else:
        text = "nothing close to the limit."
    return {"verdict": r["result"], "text": text, "report": r}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    f = check(os.path.expanduser(sys.argv[1]))
    print(f"flashes: {f['verdict']}: {f['text']}")
    sys.exit(1 if f["verdict"] == "fail" else 0)


if __name__ == "__main__":
    main()
