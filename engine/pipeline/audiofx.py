#!/usr/bin/env python3
"""Audio effects from the library, applied to the voice before the mix.

    AUDIO_FX = [
        dict(effect="reverb", at=12.0, end=14.5, params=dict(size=0.8, wet=0.5)),   # a moment: dream sequence, big word
        dict(effect="low-pass", at=30.0, end=33.0),                                  # "like it's on the phone"
        dict(effect="compressor", params=dict(threshold=-20)),                       # no window: the whole voice
    ]

The library's 17 effects keep their ids, parameters and ranges (effects-library/audio/<id>/effect.json). They run here
as ffmpeg filters rather than in the render browser, so a moment can start and stop exactly on a word with a short
crossfade at each end, and lip sync can't move. The voice's length never changes.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FADE = 0.02


def _f(v):
    return f"{float(v):.4f}"


def filter_for(effect, p):
    """library effect + parameters -> an ffmpeg filter chain"""
    db = lambda x: 10 ** (float(x) / 20)  # noqa: E731
    if effect == "bell-eq":
        return f"equalizer=f={_f(p['frequency'])}:t=q:w=1:g={_f(p['gain'])}"
    if effect == "bitcrusher":
        return f"acrusher=bits={_f(p['bits'])}:samples={_f(p['samples'])}:mix=1:mode=lin"
    if effect == "chorus":
        return f"chorus=0.6:{_f(1 - p['mix'] * 0.3)}:{_f(7 + p['depth'])}:{_f(p['mix'])}:{_f(p['speed'])}:{_f(p['depth'] / 2)}"
    if effect == "compressor":
        return f"acompressor=threshold={_f(db(p['threshold']))}:ratio={_f(p['ratio'])}:attack=20:release=250:knee=2.83:makeup={_f(db(p['makeup']))}"
    if effect == "echo-delay":
        return f"aecho=1:{_f(p['mix'])}:{_f(p['time'])}|{_f(p['time'] * 2)}|{_f(p['time'] * 3)}:{_f(p['feedback'])}|{_f(p['feedback'] ** 2)}|{_f(p['feedback'] ** 3)}"
    if effect == "gain":
        return f"volume={_f(p['gain'])}dB"
    if effect == "high-pass":
        return f"highpass=f={_f(p['frequency'])}:poles=2"
    if effect == "low-pass":
        return f"lowpass=f={_f(p['frequency'])}:poles=2"
    if effect == "high-shelf":
        return f"treble=g={_f(p['gain'])}:f={_f(p['frequency'])}"
    if effect == "low-shelf":
        return f"bass=g={_f(p['gain'])}:f={_f(p['frequency'])}"
    if effect == "limiter":
        return f"alimiter=limit={_f(db(p['limit']))}:attack=5:release=50:level=false"
    if effect == "true-peak-limiter":
        return f"alimiter=limit={_f(db(p['ceiling']))}:attack=3:release=80:level=false"
    if effect == "noise-gate":
        return f"agate=threshold={_f(db(p['threshold']))}:range={_f(db(p['range']))}:ratio=10:attack=1:release=100:knee=2.83"
    if effect == "phaser":
        return f"aphaser=in_gain=0.4:out_gain=0.74:delay=3:decay={_f(p['decay'])}:speed={_f(p['speed'])}:type=t"
    if effect == "pitch-shift":
        r = 2 ** (float(p["semitones"]) / 12)
        tempo = []
        left = 1 / r
        while left < 0.5:
            tempo.append("atempo=0.5")
            left /= 0.5
        while left > 2:
            tempo.append("atempo=2")
            left /= 2
        tempo.append(f"atempo={left:.5f}")
        return f"asetrate=48000*{r:.5f},aresample=48000," + ",".join(tempo)
    if effect == "reverb":
        size, wet = float(p["size"]), float(p["wet"])
        delays = "|".join(f"{d * (0.5 + size):.1f}" for d in (31, 47, 71, 97, 131))
        decays = "|".join(f"{(0.5 * wet + 0.2) * (0.86 ** k):.3f}" for k in range(5))
        return f"aecho=0.8:{0.7 + wet * 0.2:.3f}:{delays}:{decays}"
    if effect == "saturation-drive":
        drive = max(1.0, 10 ** (-float(p["threshold"]) / 20))
        return f"volume={drive:.3f},asoftclip=type=tanh,volume={_f(p['output'])}dB"
    raise SystemExit(f"AUDIO_FX: {effect} isn't a library audio effect")


def params_for(entry):
    import fxlib
    spec = fxlib.spec_of(entry["effect"])
    if spec.get("kind") != "audio":
        raise SystemExit(f"AUDIO_FX: {entry['effect']} is a picture effect. Put it in FXLIB.")
    out = {}
    given = entry.get("params") or {}
    for P in spec["parameters"]:
        v = float(given.get(P["key"], P["default"]))
        if not P["min"] <= v <= P["max"]:
            raise SystemExit(f"AUDIO_FX: {entry['effect']} {P['key']}={v} is outside {P['min']} to {P['max']}")
        out[P["key"]] = v
    bad = set(given) - set(out)
    if bad:
        raise SystemExit(f"AUDIO_FX: {entry['effect']} has no setting called {sorted(bad)}. It has {sorted(out)}")
    return out


def apply(voice, entries, total, dest):
    """voice wav + AUDIO_FX -> dest wav, same length. Windowed effects crossfade in and out over FADE seconds."""
    whole = [e for e in entries if e.get("at") is None]
    moments = [e for e in entries if e.get("at") is not None]
    chain = ",".join(filter_for(e["effect"], params_for(e)) for e in whole)
    graph = [f"[0:a]{chain or 'anull'},aresample=48000,aformat=channel_layouts=stereo,asetpts=N/SR/TB[b0]"]
    last = "b0"
    for k, e in enumerate(moments):
        a, b = float(e["at"]), float(e.get("end", total))
        wet = filter_for(e["effect"], params_for(e))
        env = (f"volume=enable='1':eval=frame:volume='if(lt(t,{a}),0,if(lt(t,{a + FADE}),(t-{a})/{FADE},"
               f"if(lt(t,{b}),1,if(lt(t,{b + FADE}),1-(t-{b})/{FADE},0))))'")
        inv = env.replace("volume='", "volume='1-(").rstrip("'") + ")'"
        graph.append(f"[{last}]asplit=2[d{k}][w{k}]")
        graph.append(f"[w{k}]{wet},aresample=48000,aformat=channel_layouts=stereo,asetpts=N/SR/TB,{env}[wo{k}]")
        graph.append(f"[d{k}]{inv}[do{k}]")
        graph.append(f"[do{k}][wo{k}]amix=inputs=2:normalize=0:duration=first[b{k + 1}]")
        last = f"b{k + 1}"
    graph.append(f"[{last}]apad=whole_dur={total:.4f},atrim=0:{total:.4f}[out]")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", voice, "-filter_complex", ";".join(graph), "-map", "[out]",
                        "-ar", "48000", "-c:a", "pcm_s16le", dest], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"AUDIO_FX failed: {r.stderr.strip()[-500:]}")
    return dest
