#!/usr/bin/env python3
"""The whole effects library in one place, for people and for the agent.

    ve effects list [--featured] [--group G] [--find WORD]    every effect, what it's for, how to use it
    ve effects show <name>                                    one effect: settings, ranges, how to call it
    ve effects gallery [--out DIR]                            a page of every effect with a picture, to browse
    ve effects try <project> <name> --at T [--duration D] [--param k=v] [--text "..."]   one frame of it on their footage

Four kinds, all named the same way in a request:
  hand-built  fx/ and the creator's HOME/fx/: big designed moments keyed to words. Goes in edit.FX.
  cards       cards/ and HOME/cards/: full-screen animated data cards. Goes in edit.CARDS.
  library     effects-library/: the verified looks, camera moves, overlays, text, layouts. Goes in edit.FXLIB;
              transitions go in edit.TRANSITIONS.
  audio       effects-library/audio: voice effects. Goes in edit.AUDIO_FX.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HOME, KIT, PY  # noqa: E402

GROUPS = {          # plain names for what a thing is for, in the order the gallery shows them
    "moments": "Big designed moments",
    "cards": "Full-screen data cards",
    "text-and-title": "Animate words",
    "transitions": "Between two shots",
    "camera-and-motion": "Move the camera",
    "looks-and-grades": "Colour and mood",
    "image-effects": "Texture and stylise",
    "overlays-and-generators": "Add on top",
    "creator-composites": "Layouts and split screens",
    "keying-and-subject": "Green screen and subject",
    "audio": "Voice and sound",
}


def table_rows(path):
    """the rows of a LIBRARY.md: a `name` first column, then layer, what it does, when to reach for it"""
    if not os.path.exists(path):
        return []
    rows = []
    for line in open(path, encoding="utf-8"):
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        name = re.match(r"`([\w-]+)`", cells[0])
        if name:
            rows.append((name.group(1), cells))
    return rows


def handbuilt(root, kind):
    out = []
    lib = os.path.join(root, "LIBRARY.md")
    for name, cells in table_rows(lib):
        folder = os.path.join(root, name)
        if not os.path.isdir(folder):
            continue
        what = cells[2] if kind == "moments" and len(cells) > 2 else cells[1]
        when = cells[3] if kind == "moments" and len(cells) > 3 else (cells[2] if len(cells) > 2 else "")
        out.append(dict(id=name, group=kind, kind="hand-built" if kind == "moments" else "card", what=what, when=when,
                        featured=False, picture=os.path.join(folder, "preview.jpg"), use="edit.FX" if kind == "moments" else "edit.CARDS"))
    return out


def library_entries():
    import fxlib
    feat = {e["effect_id"]: e["use_for"] for e in json.load(open(os.path.join(fxlib.LIB, "featured.json")))["effects"]}
    out = []
    for eid, spec in fxlib.fx.library().items():
        if fxlib.fx.status_of(spec) not in ("verified", "limited"):
            continue
        fam = spec["family"]
        use = {"audio": "edit.AUDIO_FX", "transitions": "edit.TRANSITIONS"}.get(fam, "edit.FXLIB")
        out.append(dict(id=eid, group=fam, kind="audio" if fam == "audio" else "library", what=spec["description"],
                        when=feat.get(eid, ""), featured=eid in feat, picture=os.path.join(spec["_dir"], "reference.jpg"),
                        use=use, params=spec.get("parameters", []), flash=spec.get("photosensitivity")))
    return out


def everything():
    items = handbuilt(os.path.join(KIT, "fx"), "moments") + handbuilt(os.path.join(HOME, "fx"), "moments")
    items += handbuilt(os.path.join(KIT, "cards"), "cards") + handbuilt(os.path.join(HOME, "cards"), "cards")
    seen, merged = set(), []
    for it in reversed(items):                                       # the creator's version of a name wins
        if it["id"] not in seen:
            seen.add(it["id"])
            merged.append(it)
    merged.reverse()
    return merged + library_entries()


def cmd_list(a):
    items = everything()
    if "--featured" in a:
        items = [i for i in items if i["featured"] or i["kind"] in ("hand-built", "card")]
    if "--group" in a:
        g = a[a.index("--group") + 1]
        items = [i for i in items if i["group"] == g or GROUPS.get(i["group"], "").lower() == g.lower()]
    if "--find" in a:
        w = a[a.index("--find") + 1].lower()
        items = [i for i in items if w in (i["id"] + " " + i["what"] + " " + i["when"]).lower()]
    for g, label in GROUPS.items():
        rows = [i for i in items if i["group"] == g]
        if rows:
            print(f"\n## {label} ({len(rows)})")
            for i in rows:
                star = " *" if i["featured"] else ""
                print(f"{i['id']}{star}: {(i['when'] or i['what'])[:130]}")
    print(f"\n{len(items)} effects. * = reviewed at full size on real talking-head footage.")


def cmd_show(a):
    name = a[0]
    items = {i["id"]: i for i in everything()}
    if name not in items:
        import difflib
        close = difflib.get_close_matches(name, items, n=3, cutoff=0.4) or [k for k in items if name.lower() in k][:3]
        sys.exit(f"No effect called {name!r}. Closest: {', '.join(close) or 'none'}")
    i = items[name]
    print(f"{i['id']}  ({GROUPS[i['group']]})\n{i['what']}")
    if i["when"]:
        print(f"Use it for: {i['when']}")
    print(f"Goes in {i['use']}")
    for P in i.get("params", []):
        print(f"  {P['key']}: {P['min']} to {P['max']}, default {P['default']} {P.get('unit', '')}  ({P.get('label', '')})")
    if i["kind"] == "hand-built":
        print(f"Folder to start from: {os.path.dirname(i['picture'])} (contract: kit/FX_BRIEF.md)")
    print(f"Picture: {i['picture']}")


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Effects library</title><style>
:root{{--bg:#fafaf7;--fg:#141414;--mut:#6c6c66;--line:#dddcd5;--card:#fff;--ac:#d9480f}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#111;--fg:#f4f4ef;--mut:#a0a09a;--line:#2b2b2b;--card:#1a1a1a;--ac:#ff7a3d}}}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 -apple-system,Segoe UI,Roboto,sans-serif;padding:24px 16px 80px}}
h1{{font-size:26px;margin:0 0 4px}} .sub{{color:var(--mut);margin:0 0 16px;max-width:60ch}}
.bar{{position:sticky;top:0;background:var(--bg);padding:10px 0;display:flex;gap:8px;flex-wrap:wrap;z-index:2}}
input{{flex:1 1 220px;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);font:inherit}}
button{{padding:8px 11px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);font:inherit;cursor:pointer}}
button.on{{background:var(--fg);color:var(--bg);border-color:var(--fg)}}
h2{{font-size:18px;margin:26px 0 10px}} .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px}}
.c{{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;display:flex;flex-direction:column}}
.c img{{width:100%;aspect-ratio:4/5;object-fit:cover;object-position:50% 30%;display:block;background:#222}}
.c div{{padding:9px 10px}} .n{{font:600 13px ui-monospace,Menlo,monospace;word-break:break-word}} .w{{color:var(--mut);font-size:13px;margin-top:3px}}
.s{{color:var(--ac);font-size:12px;font-weight:600}} .none{{display:none}}
</style></head><body><h1>Effects library</h1>
<p class="sub">{count} effects. Tell Claude the name ("put film-grain on the whole video, whip-pan on the first cut") or describe what you want. Pictures show each effect on sample footage, and your own colours replace the placeholder ones.</p>
<div class="bar"><input id="q" type="search" placeholder="Search: zoom, glitch, cinematic, list..." aria-label="Search effects"><button id="f">Top picks only</button></div>
{body}
<script>
var q=document.getElementById('q'),f=document.getElementById('f'),on=false;
function go(){{var w=q.value.toLowerCase();document.querySelectorAll('.c').forEach(function(c){{
var m=(!w||c.dataset.t.indexOf(w)>=0)&&(!on||c.dataset.s==='1');c.classList.toggle('none',!m);}});
document.querySelectorAll('section').forEach(function(s){{s.classList.toggle('none',!s.querySelector('.c:not(.none)'));}});}}
q.oninput=go;f.onclick=function(){{on=!on;f.classList.toggle('on',on);go();}};
</script></body></html>"""


def cmd_gallery(a):
    out = a[a.index("--out") + 1] if "--out" in a else os.path.join(HOME, "gallery")
    pics = os.path.join(out, "img")
    os.makedirs(pics, exist_ok=True)
    items = everything()
    from PIL import Image
    files, body = ["index.html"], []
    for g, label in GROUPS.items():
        rows = [i for i in items if i["group"] == g]
        if not rows:
            continue
        cards = []
        for i in rows:
            name = f"{i['id']}.jpg"
            dest = os.path.join(pics, name)
            src = i["picture"]
            if os.path.exists(src) and (not os.path.exists(dest) or os.path.getmtime(src) > os.path.getmtime(dest)):
                im = Image.open(src).convert("RGB")
                im.thumbnail((480, 480))
                im.save(dest, quality=78)
            has = os.path.exists(dest)
            if has:
                files.append(f"img/{name}")
            text = html.escape((i["when"] or i["what"])[:150])
            search = html.escape((i["id"] + " " + i["what"] + " " + i["when"]).lower()).replace('"', "")
            star = '<span class="s">Top pick</span>' if i["featured"] else ""
            img = f'<img loading="lazy" src="img/{name}" alt="{html.escape(i["id"])}">' if has else ""
            cards.append(f'<article class="c" data-t="{search}" data-s="{1 if i["featured"] else 0}">{img}<div><span class="n">{html.escape(i["id"])}</span> {star}<p class="w" style="margin:3px 0 0">{text}</p></div></article>')
        body.append(f'<section><h2>{label} ({len(rows)})</h2><div class="grid">{"".join(cards)}</div></section>')
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(PAGE.format(count=len(items), body="\n".join(body)))
    json.dump(files, open(os.path.join(out, "files.json"), "w"))
    print(os.path.join(out, "index.html"))


def cmd_try(a):
    project = os.path.abspath(os.path.expanduser(a[0]))
    name = a[1]
    at = float(a[a.index("--at") + 1]) if "--at" in a else 1.0
    dur = float(a[a.index("--duration") + 1]) if "--duration" in a else 1.0
    params = {}
    for k, v in enumerate(a):
        if v == "--param":
            key, val = a[k + 1].split("=")
            params[key] = float(val)
    text = a[a.index("--text") + 1] if "--text" in a else None
    import fxlib
    spec = fxlib.spec_of(name)
    sb = os.path.join(project, "work", "try", name)
    pub, ppub = os.path.join(sb, "public"), os.path.join(project, "public")
    shutil.rmtree(sb, ignore_errors=True)
    os.makedirs(pub)
    for f in ("words.json", "timeline.json"):
        shutil.copy(os.path.join(project, f), os.path.join(sb, f))
    for d in ("fx", "assets", "audio", "style", "cards"):
        if os.path.exists(os.path.join(project, d)):
            os.symlink(os.path.join(project, d), os.path.join(sb, d))
    for f in os.listdir(ppub):
        if f not in ("index.html", ".hyperframes", "assets", "fx-instances.json") and not os.path.lexists(os.path.join(pub, f)):
            os.symlink(os.path.join(ppub, f), os.path.join(pub, f))
    entry = dict(effect=name, at=at, duration=dur, params=params)
    if text:
        entry["text"] = text
    edit = open(os.path.join(project, "edit.py"), encoding="utf-8").read()
    if spec.get("target") == "scene-pair":
        edit += f"\nTRANSITIONS = [{entry!r}]\n"
    else:
        edit += f"\nFXLIB = list(globals().get('FXLIB', [])) + [{entry!r}]\n"
    open(os.path.join(sb, "edit.py"), "w", encoding="utf-8").write(edit)
    if spec.get("target") == "scene-pair":
        subprocess.run([PY, os.path.join(KIT, "pipeline", "transitions.py"), sb], check=True)
    subprocess.run([PY, os.path.join(KIT, "pipeline", "build.py"), sb, "--stills"], check=True, stdout=subprocess.DEVNULL)
    from storyboard import snapshot
    names = snapshot(sb, [at + min(dur, 2) / 2], os.path.join(sb, "shots"))
    print(os.path.join(sb, "shots", names[0]))


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    cmd, rest = a[0], a[1:]
    {"list": cmd_list, "show": cmd_show, "gallery": cmd_gallery, "try": cmd_try}.get(cmd, lambda _: sys.exit(__doc__))(rest)


if __name__ == "__main__":
    main()
