#!/usr/bin/env python3
"""Setup: gets this computer ready to edit video. Safe to run again any time; it picks up where it stopped.

Run:  sh setup/setup.sh [--check] [--matte] [--accurate]
  --check     report only, change nothing
  --matte     also install PyTorch for smoother cutouts (about 1 GB)
  --accurate  use the bigger transcription model (Whisper medium, 1.5 GB instead of 0.5 GB)

Prints STEP lines a person can follow, one STATUS line per piece, and ends with READY or NOT READY. A MISSING line
ends with the exact fix for this computer. Standard library only, so it runs before anything else is installed.
Everything it installs goes in $VIDEO_EDITOR_HOME (default ~/video-editor: .venv/, vendor/, tools/, models/, cache/, bin/),
never inside the plugin folder and never system-wide, except the render browser, which the render engine keeps in
~/.cache/hyperframes. No admin password, no Homebrew.
"""
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.request

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser(os.environ.get("VIDEO_EDITOR_HOME", "~/video-editor"))
WIN = os.name == "nt"
VENV = os.path.join(HOME, ".venv")                     # everything setup makes lives in HOME: the skill folder may be read-only
VENV_PY = os.path.join(VENV, "Scripts", "python.exe") if WIN else os.path.join(VENV, "bin", "python")
HF_VERSION = "0.8.183"                                  # the version every effect in the library was verified on
HF = ["npx.cmd" if WIN else "npx", "-y", f"hyperframes@{HF_VERSION}"]
GSAP_VERSION = "3.15.0"
GSAP_URL = f"https://cdn.jsdelivr.net/npm/gsap@{GSAP_VERSION}/dist/gsap.min.js"
GSAP_PATH = os.path.join(HOME, "vendor", "gsap.min.js")
CHECK = "--check" in sys.argv
OS = "macos" if sys.platform == "darwin" else "windows" if WIN else "linux"
ARCH = "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "amd64"
TOOLS = os.path.join(HOME, "tools")                    # ffmpeg, Node and Python that setup fetched itself
BIN = os.path.join(TOOLS, "bin")                       # first on PATH for setup and the pipeline (common.py)
os.environ["PATH"] = BIN + os.pathsep + os.environ.get("PATH", "")
# downloads stay in the one folder too, so deleting it really removes everything
os.environ.update(HF_HOME=os.path.join(HOME, "models"), npm_config_cache=os.path.join(HOME, "cache", "npm"),
                  XDG_CACHE_HOME=os.path.join(HOME, "cache"), PLAYWRIGHT_BROWSERS_PATH=os.path.join(HOME, "browsers"),
                  HYPERFRAMES_NO_TELEMETRY="1", DO_NOT_TRACK="1", HYPERFRAMES_NO_UPDATE_CHECK="1", HYPERFRAMES_SKIP_SKILLS="1")
MARKER = os.path.join(HOME, ".setup-version")          # the kit release that last reached READY on this computer
AGAIN = f"check your internet connection, then run setup again: sh {os.path.join(KIT, 'setup', 'setup.sh')}"
FIX = {
    "ffmpeg": {"macos": AGAIN, "linux": AGAIN,
               "windows": "winget install --id Gyan.FFmpeg -e   (then reopen the terminal)"},
    "node": {"macos": AGAIN, "linux": AGAIN,
             "windows": "winget install --id OpenJS.NodeJS.LTS -e   (then reopen the terminal)"},
    "python": {"macos": f"sh {os.path.join(KIT, 'setup', 'setup.sh')}   (it fetches one)",
               "linux": f"sh {os.path.join(KIT, 'setup', 'setup.sh')}   (it fetches one)",
               "windows": "winget install --id Python.Python.3.12 -e"},
}

# Static builds fetched when the computer has no ffmpeg (or one without the VP9 encoder the cutout needs) or no
# Node 22+. Pinned with their checksums, so every computer gets the same tools.
FFMPEG_BASE = "https://ffmpeg.martin-riedl.de/download"
FFMPEG = {   # (os, arch): (build folder, ffmpeg.zip sha256, ffprobe.zip sha256), ffmpeg 9.0.2
    ("macos", "arm64"): ("macos/arm64/1789931890_9.0.2",
                         "c8ed4c4e6978a03c485edbfe4e0a5dc2380f8a30bba5150531b31b094492d924",
                         "fcbe839537485eaee7a7a8bc5cbc0f90d53617e80943e8a5b2e31cb851197ea6"),
    ("macos", "amd64"): ("macos/amd64/1789931006_9.0.2",
                         "7c6b4125b191cbf773832dc51f424cf2b6bb7da43007d1e066f95909e47cacd4",
                         "2322438ed2f6319a691291b247d09c69dcaa3a982460d1f269a7e1af335cfdfd"),
    ("linux", "arm64"): ("linux/arm64/1789931697_9.0.2",
                         "93a76ae90db5474eecdf951a729857c64f3de23567228d6a7d5e6e8e3cd1021b",
                         "bcbe80fb741c180083327afaf5434812e006b33cacde2016b9aeaf6936128330"),
    ("linux", "amd64"): ("linux/amd64/1789931100_9.0.2",
                         "fa8ecf4abbd290d98f7d188b8649cc6b391ae209a98452be955a15aab1909d7f",
                         "3f428c49070be3d24ec338602b76d412e401ffcb8a5641ef0e729181a232fc32"),
}
NODE_VERSION = "v22.23.3"
NODE = {     # (os, arch): (nodejs.org platform, tar.gz sha256)
    ("macos", "arm64"): ("darwin-arm64", "23b25245dcfb9af7262f8ff142e9e2e0af025368117329e7a7458a51e5922f53"),
    ("macos", "amd64"): ("darwin-x64", "8a677b0219178efd6eb0e475457c4afb452b521a92f6e67845a73bd85727f2a8"),
    ("linux", "arm64"): ("linux-arm64", "5ced2d48d1d7198739b7f86804de0171aefb6823b684b12341d3321afc3cb0b2"),
    ("linux", "amd64"): ("linux-x64", "1084aa36196bba4c3a5e69a1ee388a6e4ff729dad09445fbcd434b28fe3c24af"),
}
ok = True
SANDBOX = os.environ.get("CODEX_SANDBOX")   # Codex marks its sandboxed commands; the render browser can't start in it
FULL_ACCESS = ("give this session full access (Codex: Full access in the permissions menu, or start it with "
               "`codex --sandbox danger-full-access`), then run setup again")


def status(name, good, detail="", fix=""):
    global ok
    ok = ok and good
    line = f"STATUS {name:<10} {'OK     ' if good else 'MISSING'} {detail}"
    if not good and fix:
        line += f"\n           fix: {fix}"
    print(line, flush=True)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def version_of(cmd):
    try:
        out = run(cmd)
        return (out.stdout + out.stderr).strip()
    except OSError:
        return ""


def download(url, dest, sha=None):
    """url -> dest, checked against sha256 when given. curl first: a fetched Python may not find the system's
    certificates, and curl always does. True when the file is there and matches."""
    tmp = dest + ".part"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        if shutil.which("curl"):
            subprocess.run(["curl", "-fsSL", "--retry", "2", "-o", tmp, url], check=True)
        else:
            urllib.request.urlretrieve(url, tmp)
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"download failed: {url} ({e})", flush=True)
        return False
    if sha and hashlib.sha256(open(tmp, "rb").read()).hexdigest() != sha:
        os.remove(tmp)
        print(f"download didn't match its checksum: {url}", flush=True)
        return False
    os.replace(tmp, dest)
    return True


def link(target, name):
    """BIN/name -> target, replacing an older link"""
    os.makedirs(BIN, exist_ok=True)
    p = os.path.join(BIN, name)
    if os.path.lexists(p):
        os.remove(p)
    os.symlink(target, p)


def fetch_ffmpeg():
    """a static ffmpeg + ffprobe (with libvpx-vp9) into TOOLS/ffmpeg, linked from BIN"""
    import zipfile
    build = FFMPEG.get((OS, ARCH))
    if not build:
        return False
    print("  fetching ffmpeg 9.0.2 (about 80 MB, once) ...", flush=True)
    folder = os.path.join(TOOLS, "ffmpeg")
    for name, sha in (("ffmpeg", build[1]), ("ffprobe", build[2])):
        z = os.path.join(folder, f"{name}.zip")
        if not download(f"{FFMPEG_BASE}/{build[0]}/{name}.zip", z, sha):
            return False
        with zipfile.ZipFile(z) as zf:
            member = next(m for m in zf.namelist() if os.path.basename(m) == name)
            with zf.open(member) as src, open(os.path.join(folder, name), "wb") as out:
                shutil.copyfileobj(src, out)
        os.remove(z)
        os.chmod(os.path.join(folder, name), 0o755)
        link(os.path.join(folder, name), name)
    return True


def fetch_node():
    """Node 22 from nodejs.org into TOOLS/node, with node, npm and npx linked from BIN"""
    import tarfile
    build = NODE.get((OS, ARCH))
    if not build:
        return False
    print(f"  fetching Node {NODE_VERSION} (about 50 MB, once) ...", flush=True)
    name = f"node-{NODE_VERSION}-{build[0]}"
    tgz = os.path.join(TOOLS, f"{name}.tar.gz")
    if not download(f"https://nodejs.org/dist/{NODE_VERSION}/{name}.tar.gz", tgz, build[1]):
        return False
    with tarfile.open(tgz) as tf:
        if hasattr(tarfile, "data_filter"):
            tf.extractall(TOOLS, filter="data")
        else:
            tf.extractall(TOOLS)
    os.remove(tgz)
    dest = os.path.join(TOOLS, "node")
    shutil.rmtree(dest, ignore_errors=True)
    os.rename(os.path.join(TOOLS, name), dest)
    for b in ("node", "npm", "npx"):
        link(os.path.join(dest, "bin", b), b)
    return True


def node_major():
    m = re.match(r"v(\d+)", version_of(["node", "--version"]) if shutil.which("node") else "")
    return int(m.group(1)) if m else 0


FRAME = """<!doctype html><html><head><meta charset="utf-8"><title>render test</title></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1.000" data-fps="30" data-width="1080" data-height="1920"
 style="width:1080px;height:1920px;background:#222"></div>
<script src="vendor/gsap.min.js"></script>
<script>window.__timelines = window.__timelines || {}; window.__timelines["main"] = gsap.timeline({ paused: true }).to({}, { duration: 1 });</script>
</body></html>"""


BROWSER_FILE = os.path.join(HOME, "vendor", "browser-path.txt")     # a browser setup picked; the pipeline uses it
PLAYWRIGHT = "playwright@1.56.1"


def frame_test(browser=None):
    """one frame of a one-second composition with the render browser; returns (ok, output)"""
    import glob
    import tempfile
    d = tempfile.mkdtemp(prefix="video-editor-render-test-")
    os.makedirs(os.path.join(d, "vendor"))
    shutil.copy(GSAP_PATH, os.path.join(d, "vendor", "gsap.min.js"))
    shutil.copy(os.path.join(KIT, "kit", "hyperframes.json"), d)
    with open(os.path.join(d, "index.html"), "w") as fh:
        fh.write(FRAME)
    env = dict(os.environ, **({"HYPERFRAMES_BROWSER_PATH": browser} if browser else {}))
    r = subprocess.run(HF + ["snapshot", "--at", "0.5", "--no-end", "--describe", "false"], cwd=d,
                       capture_output=True, text=True, env=env)
    m = re.search(r"snapshots saved to (.+)", r.stdout + r.stderr)          # the CLI says where; it moved between releases
    good = r.returncode == 0 and bool(m and glob.glob(os.path.join(m.group(1).strip(), "frame-*.png")))
    shutil.rmtree(d, ignore_errors=True)
    return good, r.stdout + r.stderr


def linux_browser():
    """Linux on ARM (Claude Cowork's VM, Raspberry Pi, ARM servers) has no headless Chrome build, and Ubuntu's
    chromium-browser is a snap wrapper that won't start in a VM or container: install Playwright's Chromium into
    HOME/browsers instead and remember it. Returns the path that renders, or None."""
    dest = os.path.join(HOME, "browsers")
    env = dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=dest)
    print("installing a render browser that works on this Linux (Chromium, about 200 MB, once) ...", flush=True)
    root = hasattr(os, "geteuid") and os.geteuid() == 0
    cmd = ["npx", "-y", PLAYWRIGHT, "install"] + (["--with-deps"] if root else []) + ["chromium"]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode and not root:
        print("note: if it still can't start, its system libraries are missing: "
              f"sudo npx -y {PLAYWRIGHT} install-deps chromium", flush=True)
    import glob
    found = sorted(glob.glob(os.path.join(dest, "chromium_headless_shell-*", "*", "headless_shell"))) + \
        sorted(glob.glob(os.path.join(dest, "chromium-*", "*", "chrome")))
    for b in found:
        if frame_test(b)[0]:
            os.makedirs(os.path.dirname(BROWSER_FILE), exist_ok=True)
            with open(BROWSER_FILE, "w") as fh:
                fh.write(b)
            return b
    return None


def render_test():
    """launch the render browser for real: one frame of a one-second composition. READY has to mean it can render"""
    saved = open(BROWSER_FILE).read().strip() if os.path.exists(BROWSER_FILE) else None
    good, out = frame_test(saved if saved and os.path.exists(saved) else None)
    if not good and OS == "linux" and not SANDBOX and not CHECK:
        b = linux_browser()
        if b:
            good, out = True, ""
            print(f"render browser: {b}", flush=True)
    if good:
        status("render", True, "the render browser launched and drew a frame")
    elif SANDBOX or "MachPortRendezvousServer" in out:
        status("render", False, "BLOCKED: this agent's sandbox stops the render browser from starting", FULL_ACCESS)
    else:
        status("render", False, "the test frame failed:\n" + out[-1200:],
               f"{' '.join(HF)} browser ensure, or point HYPERFRAMES_BROWSER_PATH at any Chrome or Chromium")


def find_python():
    """this Python if it is 3.10+, else the newest python3.1x on PATH (or Homebrew's), else None"""
    if sys.version_info >= (3, 10):
        return sys.executable
    names = ["python3.13", "python3.12", "python3.11", "python3.10"] + (["py"] if WIN else [])
    extra = ["/opt/homebrew/bin/python3", "/usr/local/bin/python3"]
    for c in [shutil.which(n) for n in names] + [p for p in extra if os.path.exists(p)]:
        if not c:
            continue
        m = re.search(r"Python 3\.(\d+)", version_of([c, "--version"]))
        if m and int(m.group(1)) >= 10:
            return c
    return None



STEPS = 8
_n = 0


def step(text):
    global _n
    _n += 1
    print(f"STEP {_n}/{STEPS}  {text}", flush=True)


def preflight():
    """the things that make a setup fail 15 minutes in: say them first, in plain words"""
    target = HOME if os.path.exists(HOME) else os.path.dirname(HOME.rstrip(os.sep)) or os.sep
    free = shutil.disk_usage(target).free / 1e9 if os.path.exists(target) else 99
    status("disk", free >= 4, f"{free:.0f} GB free (needs about 3 GB, plus room for your videos)",
           f"free up some space on this computer, then run setup again")
    if "Mobile Documents" in HOME or "/Library/CloudStorage/" in HOME:
        print("note: this folder syncs to the cloud, which can pull files away mid-render. A folder that doesn't sync "
              "is safer: set VIDEO_EDITOR_HOME to one.", flush=True)
    if CHECK:
        return
    try:
        urllib.request.urlopen("https://registry.npmjs.org/-/ping", timeout=15)
        status("internet", True, "reachable")
    except Exception:
        if shutil.which("curl") and subprocess.run(["curl", "-fsS", "-m", "15", "-o", os.devnull, "https://registry.npmjs.org/-/ping"],
                                                   capture_output=True).returncode == 0:
            status("internet", True, "reachable")
        else:
            status("internet", False, "can't reach the download servers", "connect to the internet (and turn off any VPN that blocks downloads), then run setup again")


def write_ve():
    """HOME/bin/ve: the one command every step goes through, so nothing depends on PATH or on where the plugin lives"""
    os.makedirs(os.path.join(HOME, "bin"), exist_ok=True)
    cli = os.path.join(KIT, "pipeline", "cli.py")
    path = os.path.join(HOME, "bin", "ve")
    with open(path, "w") as fh:
        fh.write("#!/bin/sh\n"
                 "# written by setup: runs a Video Editor step with its own Python, ffmpeg and Node\n"
                 f'export VIDEO_EDITOR_HOME="{HOME}"\n'
                 f'export PATH="{BIN}:$PATH"\n'
                 f'exec "{VENV_PY}" "{cli}" "$@"\n')
    os.chmod(path, 0o755)
    return path


def fetch_shader():
    """the WebGL transition runtime (shader transitions), from npm at the pinned version"""
    dest = os.path.join(HOME, "vendor", "hyper-shader.js")
    if os.path.exists(dest):
        return True
    import glob
    import tarfile
    import tempfile
    d = tempfile.mkdtemp(prefix="video-editor-shader-")
    npm = "npm.cmd" if WIN else "npm"
    r = run([npm, "pack", f"@hyperframes/shader-transitions@{HF_VERSION}", "--silent"], cwd=d)
    packs = glob.glob(os.path.join(d, "*.tgz"))
    if r.returncode or not packs:
        print((r.stdout + r.stderr)[-500:], flush=True)
        shutil.rmtree(d, ignore_errors=True)
        return False
    with tarfile.open(packs[0]) as tf:
        member = next((m for m in tf.getmembers() if m.name.endswith("dist/index.global.js")), None)
        if member is None:
            shutil.rmtree(d, ignore_errors=True)
            return False
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with tf.extractfile(member) as src, open(dest, "wb") as out:
            shutil.copyfileobj(src, out)
    shutil.rmtree(d, ignore_errors=True)
    return True


def main():
    ver = open(os.path.join(KIT, "VERSION")).read().strip() if os.path.exists(os.path.join(KIT, "VERSION")) else "unknown"
    print(f"Video Editor {ver} setup on {OS} ({platform.machine()})\nInstalling into {HOME}", flush=True)
    if SANDBOX:
        net = " with the network off" if os.environ.get("CODEX_SANDBOX_NETWORK_DISABLED") else ""
        print(f"note: running inside Codex's sandbox ({SANDBOX}){net}. Rendering launches a headless browser, which "
              f"this sandbox blocks: {FULL_ACCESS}", flush=True)
    os.makedirs(HOME, exist_ok=True)
    step("Checking this computer")
    preflight()
    if not ok:
        print("NOT READY: apply the fixes above, then run setup again", flush=True)
        sys.exit(1)
    base = find_python()
    status("python", bool(base), (version_of([base, "--version"]) + f" ({base})") if base else platform.python_version(),
           FIX["python"][OS])

    step("Video tools (ffmpeg)")
    # also catches a broken install: an ffmpeg that is on PATH but can't start reports no encoders, so it gets replaced
    def vp9():
        return "libvpx-vp9" in version_of(["ffmpeg", "-hide_banner", "-encoders"])
    have = bool(shutil.which("ffmpeg") and shutil.which("ffprobe")) and vp9()
    if not have and not CHECK and fetch_ffmpeg():
        have = bool(shutil.which("ffmpeg")) and vp9()
    detail = version_of(["ffmpeg", "-version"]).split("\n")[0][:60] if have else ""
    status("ffmpeg", have, detail + (f" ({shutil.which('ffmpeg')})" if have else ""), FIX["ffmpeg"][OS])

    step("Render tools (Node)")
    if node_major() < 22 and not CHECK:
        fetch_node()
    v = version_of(["node", "--version"]) if shutil.which("node") else ""
    status("node", node_major() >= 22, v + ("" if node_major() >= 22 else " (needs 22+)") +
           (f" ({shutil.which('node')})" if node_major() >= 22 else ""), FIX["node"][OS])

    step("Python packages")
    reqs = os.path.join(KIT, "setup", "requirements.txt")
    if not os.path.exists(VENV_PY) and not CHECK and base:
        subprocess.run([base, "-m", "venv", VENV], check=True)
    if os.path.exists(VENV_PY) and not CHECK:
        run([VENV_PY, "-m", "pip", "install", "-q", "--upgrade", "pip"])
        r = run([VENV_PY, "-m", "pip", "install", "-q", "-r", reqs])
        if r.returncode:
            print(r.stderr[-1500:], flush=True)
    probe = run([VENV_PY, "-c", "import numpy, scipy, PIL, faster_whisper, cv2; cv2.CascadeClassifier"]) if os.path.exists(VENV_PY) else None
    status("packages", bool(probe and probe.returncode == 0), "numpy, scipy, pillow, faster-whisper, opencv, yt-dlp",
           f"sh {os.path.join(KIT, 'setup', 'setup.sh')}")

    step("Animation libraries")
    if not os.path.exists(GSAP_PATH) and not CHECK:
        download(GSAP_URL, GSAP_PATH)
    good = os.path.exists(GSAP_PATH) and f"GSAP {GSAP_VERSION}" in open(GSAP_PATH, errors="ignore").read(400)
    status("gsap", good, GSAP_VERSION, f"download {GSAP_URL} to {GSAP_PATH}")
    if shutil.which("npm" if not WIN else "npm.cmd") and not CHECK:
        fetch_shader()
    status("shaders", os.path.exists(os.path.join(HOME, "vendor", "hyper-shader.js")),
           "the shader transitions", "check your internet connection, then run setup again")

    step("Render engine and its browser")
    if shutil.which("npx" if not WIN else "npx.cmd"):
        hv = version_of(HF + ["--version"])
        status("engine", HF_VERSION in hv, f"hyperframes {HF_VERSION}",
               FULL_ACCESS if SANDBOX else "check your internet connection, then run setup again")
        if not CHECK:
            r = run(HF + ["browser", "ensure"])
            if r.returncode:
                print((r.stdout + r.stderr)[-800:], flush=True)
        chrome = run(HF + ["browser", "path"])
        found = chrome.returncode == 0 and bool(chrome.stdout.strip())
        if OS != "linux" or found:                  # on Linux the render step installs a browser that works
            status("browser", found, "found" if found else "", FULL_ACCESS if SANDBOX else f"{' '.join(HF)} browser ensure")
        if os.path.exists(GSAP_PATH) and (found or OS == "linux"):
            render_test()
    else:
        status("engine", False, "needs Node first", FIX["node"][OS])

    step("Speech model, for captions (about 500 MB)")
    model = "medium" if "--accurate" in sys.argv or os.path.exists(os.path.join(HOME, ".model-medium")) else "small"
    if "--accurate" in sys.argv and not CHECK:
        open(os.path.join(HOME, ".model-medium"), "w").close()
    if os.path.exists(VENV_PY):
        check = f"from faster_whisper.utils import download_model; download_model('{model}', local_files_only=True)"
        have = run([VENV_PY, "-c", check])
        if have.returncode and not CHECK:
            subprocess.run([VENV_PY, "-c", f"from faster_whisper.utils import download_model; download_model('{model}')"],
                           stderr=subprocess.DEVNULL)
            have = run([VENV_PY, "-c", check])
        status("speech", have.returncode == 0, f"Whisper {model}", "check your internet connection, then run setup again")

    # optional: smoother cutouts
    if "--matte" in sys.argv and os.path.exists(VENV_PY):
        if not CHECK:
            cmd = [VENV_PY, "-m", "pip", "install", "-q", "torch"]
            if OS == "linux" and not shutil.which("nvidia-smi"):
                cmd += ["--index-url", "https://download.pytorch.org/whl/cpu"]
            print("  installing PyTorch (about 1 GB) ...", flush=True)
            subprocess.run(cmd)
        t = run([VENV_PY, "-c", "import torch; print(torch.__version__)"])
        status("matte", t.returncode == 0, t.stdout.strip(), f"sh {os.path.join(KIT, 'setup', 'setup.sh')} --matte")

    step("Finishing up")
    ve = write_ve() if os.path.exists(VENV_PY) and not CHECK else os.path.join(HOME, "bin", "ve")
    status("ve", os.path.exists(ve), ve, f"sh {os.path.join(KIT, 'setup', 'setup.sh')}")
    pack = os.path.join(HOME, "style", "style.json")
    print(f"STATUS style      {'OK     ' if os.path.exists(pack) else 'NONE YET'} "
          f"{pack if os.path.exists(pack) else 'next step: /video-editor:style'}", flush=True)
    if ok and not CHECK:
        with open(MARKER, "w") as fh:
            fh.write(ver + "\n")
    print("READY" if ok else "NOT READY: apply the fixes above, then run setup again", flush=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
