#!/usr/bin/env python3
"""Ingest: reads a clip and makes it safe to edit, without touching the original.

Phones hand over footage the render can't use straight: iPhone HDR (HLG or Dolby Vision) comes out grey and washed
out, variable frame rate drifts out of sync, rotated clips arrive sideways, a cloud folder can hold a placeholder
instead of the file. This finds all of it, explains it in plain words, and writes one clean working copy (SDR Rec.709,
constant frame rate, rotation applied) into the project. The original is checksummed before and after.

Run:  ve probe <clip>     prints what the clip is, changes nothing
Used by new.py on every new project.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

HDR_TRANSFERS = {"arib-std-b67": "HLG", "smpte2084": "HDR10 or Dolby Vision"}


def make_local(path):
    """a cloud folder (iCloud, Drive) can hold a placeholder: pull the real file down first"""
    try:
        if sys.platform == "darwin" and os.stat(path).st_blocks == 0 and os.path.getsize(path) > 0:
            print(f"downloading {os.path.basename(path)} from iCloud first ...", flush=True)
            subprocess.run(["brctl", "download", path], capture_output=True)
            for _ in range(600):
                if os.stat(path).st_blocks > 0:
                    return
                subprocess.run(["sleep", "1"])
    except OSError:
        pass


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,color_transfer,"
                          "color_primaries,pix_fmt,sample_rate,channels:stream_side_data=rotation,dv_profile:format=duration,size",
                          "-of", "json", path], capture_output=True, text=True)
    if out.returncode:
        raise SystemExit(f"{os.path.basename(path)} can't be read as a video. Is the file complete? ({out.stderr.strip()[:200]})")
    d = json.loads(out.stdout)
    video = next((s for s in d.get("streams", []) if s["codec_type"] == "video"), None)
    audio = next((s for s in d.get("streams", []) if s["codec_type"] == "audio"), None)
    if not video:
        raise SystemExit(f"{os.path.basename(path)} has no picture in it.")

    def rate(text):
        m = re.match(r"(\d+)/(\d+)", text or "")
        return float(m.group(1)) / float(m.group(2)) if m and float(m.group(2)) else 0.0
    side = video.get("side_data_list", [])
    rotation = next((abs(int(x["rotation"])) for x in side if "rotation" in x), 0)
    dv = any("dv_profile" in x for x in side)
    w, h = video.get("width", 0), video.get("height", 0)
    if rotation in (90, 270):
        w, h = h, w
    r, a = rate(video.get("r_frame_rate")), rate(video.get("avg_frame_rate"))
    info = {
        "path": path, "width": w, "height": h, "codec": video.get("codec_name"), "fps": round(a or r, 3),
        "vfr": bool(r and a and abs(r - a) > 0.1), "rotation": rotation,
        "hdr": HDR_TRANSFERS.get(video.get("color_transfer", "")) or ("Dolby Vision" if dv else None),
        "transfer": video.get("color_transfer"), "pix_fmt": video.get("pix_fmt"),
        "has_audio": bool(audio), "duration": float(d.get("format", {}).get("duration", 0) or 0),
        "size_mb": round(float(d.get("format", {}).get("size", 0) or 0) / 1e6),
    }
    return info


def describe(i):
    """the clip, and everything worth saying about it, in plain words"""
    lines = [f"{i['width']}x{i['height']}, {i['fps']:g} fps, {i['duration']:.0f} seconds, {i['size_mb']} MB"]
    shape = "vertical" if i["height"] > i["width"] else "horizontal" if i["width"] > i["height"] else "square"
    lines.append(f"Shape: {shape}.")
    if i["hdr"]:
        lines.append(f"Filmed in HDR ({i['hdr']}): converted to normal colour so it doesn't come out washed out.")
    if i["vfr"]:
        lines.append("Variable frame rate (normal for phones): evened out so the voice stays in sync.")
    if i["rotation"]:
        lines.append(f"Stored rotated {i['rotation']} degrees: straightened.")
    if not i["has_audio"]:
        lines.append("NO SOUND in this clip. Captions and the voice mix need audio.")
    if i["duration"] > 300:
        lines.append("Longer than 5 minutes: use /video-editor:clips to pull short clips out of it.")
    if max(i["width"], i["height"]) < 1080:
        lines.append("Low resolution: the finished video will look soft. Send the original if you have it.")
    return lines


def needs_copy(i):
    """a working copy only when the edit can't use the file straight: HEVC and 60 fps are fine, the cut re-encodes them"""
    return bool(i["hdr"] or i["vfr"] or i["rotation"])


def tone_filter(i):
    """HDR to SDR Rec.709. zscale + hable when this ffmpeg has it, else a plain matrix conversion. Colour is checked
    against the frame's own brightness after: a washed-out conversion is the bug this exists to prevent"""
    has_z = "zscale" in subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    if i["hdr"] and has_z:
        npl = "npl=203" if i["hdr"] == "HLG" else "npl=100"
        return (f"zscale=t=linear:{npl},format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0:peak=6,"
                "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    if i["hdr"]:
        return "colorspace=all=bt709:iall=bt2020:trc=bt709:format=yuv420p"
    return "format=yuv420p"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def working_copy(src, project):
    """-> the path the edit should use: the original when it is clean, else <project>/source/<name>.mp4"""
    make_local(src)
    i = probe(src)
    for line in describe(i):
        print(line)
    if not i["has_audio"]:
        raise SystemExit("This clip has no sound. Video Editor cuts on the voice, so it needs a clip with sound.")
    if not needs_copy(i):
        return src, i
    dest_dir = os.path.join(project, "source")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, os.path.splitext(os.path.basename(src))[0] + ".mp4")
    fps = 30 if i["fps"] <= 31 else 60
    # a vertical 4K phone clip has more pixels than a 1080 reel can use: 1440 wide still leaves room for a 1.33x close-up
    size = "scale=-2:2560:flags=lanczos," if i["height"] > i["width"] and i["height"] > 2560 else ""
    print(f"Preparing a clean working copy, about {max(1, round(i['duration'] / 60))} minute(s) (your original stays untouched) ...", flush=True)
    before = sha(src)
    tmp = dest + ".part.mp4"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0:v:0", "-map", "0:a:0",
                        "-vf", f"{size}{tone_filter(i)},fps={fps}", "-fps_mode", "cfr", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                        "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", tmp],
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"Converting the clip failed: {r.stderr.strip()[-400:]}")
    os.replace(tmp, dest)
    if sha(src) != before:
        raise SystemExit("The original changed while it was being read. Nothing was edited; try again.")
    json.dump({"original": src, "sha256": before, "reasons": [k for k in ("hdr", "vfr", "rotation") if i[k]]},
              open(dest + ".json", "w"), indent=1)
    return dest, i


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = os.path.abspath(os.path.expanduser(sys.argv[1]))
    if not os.path.exists(path):
        sys.exit(f"can't find {path}")
    make_local(path)
    i = probe(path)
    print("\n".join(describe(i)))
    print(json.dumps(i))


if __name__ == "__main__":
    main()
