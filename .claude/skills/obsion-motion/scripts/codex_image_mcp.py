#!/usr/bin/env python3
"""codex_image_mcp.py — MCP server (stdio, stdlib only) that generates images with the Codex CLI built-in image_gen
(ChatGPT login, no API key). Part of the OBSION Motion skill: whole frames, MODULAR RIG PARTS and DEPTH PLATES, all from one
canonical reference + style bible so the set stays consistent.

Register (user scope):
  claude mcp add --scope user codex-image -- python3 <path-to-skill>/scripts/codex_image_mcp.py

Tools
  image_generate   one image → out_path (sync; ~1–3 min)
  image_parts      many images as a background job: rig parts of one character/object, or depth plates, or any list
  image_job        status/result of a background job
  image_check      size + real alpha check (opaque border %, halo) of PNGs — run before using a part in a rig

Rules baked in: one piece per call; the same canonical refs on every call (never chain
regenerations); style bible text verbatim on every call; transparent parts get real alpha (checked, not trusted).
"""
import json, os, re, shutil, subprocess, sys, threading, time, glob, uuid, struct, zlib

CODEX = shutil.which("codex") or os.path.expanduser("~/.local/bin/codex")
PY_PIL = os.environ.get("CODEX_IMAGE_PY") or sys.executable  # any Python with Pillow (pip install pillow)
PREAMBLE = ("Use your built-in image_gen tool (not a CLI, script or API call) to generate ONE image, then copy the generated "
            "PNG file into this workspace as {name} . Do not write any code or edit other files.")
ALPHA = ("Background: fully transparent (real alpha channel, PNG) everywhere outside the subject, clean anti-aliased edges, "
         "no ground, no cast shadow, no frame, no checkerboard pattern.")
PART = ("This is ONE separate part of a cut-out puppet for 2D/2.5D rig animation: draw ONLY the part named below, isolated, "
        "in a neutral straight pose, at the same scale and from the same camera angle as the reference character; extend the "
        "joint end with ~15% extra overlap (rounded joint cap) so it can rotate ±35° without a gap; no other body parts.")
PLATE = ("This is ONE depth plate for a 2.5D multiplane camera: draw ONLY the layer described, wide (edge-to-edge horizontally, "
         "with 25% extra margin of continuous scenery on every side so the camera can move), everything nearer than this layer "
         "left out (transparent), consistent light direction with the reference.")
JOBS = {}

def log(*a): print(*a, file=sys.stderr, flush=True)

def generate(prompt, out_path, refs=None, size=None, transparent=False, style_bible=None, kind="image", timeout=900):
    out_path = os.path.abspath(os.path.expanduser(out_path)); d = os.path.dirname(out_path); os.makedirs(d, exist_ok=True)
    name = os.path.basename(out_path) if out_path.lower().endswith(".png") else os.path.basename(out_path) + ".png"
    sb = ""
    if style_bible:
        sb = open(os.path.expanduser(style_bible)).read().strip() if os.path.exists(os.path.expanduser(style_bible)) else style_bible
    parts = [PREAMBLE.format(name=name)]
    if refs: parts.append("Reference images are attached: match their character design, art style, palette, line and light exactly.")
    if sb: parts.append("STYLE BIBLE (follow verbatim):\n" + sb)
    if kind == "part": parts.append(PART)
    if kind == "plate": parts.append(PLATE)
    if transparent: parts.append(ALPHA)
    if size: parts.append(f"Image size: {size}.")
    parts.append("ASSET:\n" + prompt)
    full = "\n\n".join(parts)
    cmd = [CODEX, "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", d, "-c", 'model_reasoning_effort="low"']
    for r in refs or []: cmd += ["-i", os.path.abspath(os.path.expanduser(r))]
    cmd += ["--", "-"]
    logp = out_path + ".codex.log"; t0 = time.time()
    with open(logp, "wb") as lf:
        p = subprocess.run(cmd, input=full.encode(), stdout=lf, stderr=subprocess.STDOUT, timeout=timeout)
    text = open(logp, encoding="utf-8", errors="replace").read()
    target = os.path.join(d, name)
    if not (os.path.exists(target) and os.path.getmtime(target) >= t0 - 1):
        sid = (re.search(r"session id:\s*([0-9a-f-]{8,})", text) or [None, None])[1]
        c = [x for x in re.findall(r"(/[^\s'\"`]*generated_images/[^\s'\"`]+?\.(?:png|webp|jpg))", text) if os.path.exists(x)]
        if not c and sid:
            c = sorted(glob.glob(os.path.join(os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex")), "generated_images", sid, "*")), key=os.path.getmtime)
        if not c:
            raise RuntimeError(f"codex exit {p.returncode}, no image; log {logp}: " + " | ".join(text.strip().splitlines()[-6:]))
        shutil.copy(c[-1], target)
    if target != out_path: shutil.move(target, out_path)
    res = {"path": out_path, "seconds": round(time.time() - t0, 1), "log": logp}
    if transparent: res["check"] = check([out_path])[0]
    return res

def check(paths):
    code = r'''
import sys, json
from PIL import Image
out=[]
for p in sys.argv[1:]:
    im=Image.open(p); r={"path":p,"size":im.size,"mode":im.mode}
    if im.mode in ("RGBA","LA") or "transparency" in im.info:
        rgba=im.convert("RGBA"); a=rgba.getchannel("A"); w,h=a.size; n=w*h
        hist=a.histogram(); r["alpha"]=True; r["transparent_pct"]=round(sum(hist[:8])/n*100,1)
        ring=[a.getpixel((x,0)) for x in range(w)]+[a.getpixel((x,h-1)) for x in range(w)]+[a.getpixel((0,y)) for y in range(h)]+[a.getpixel((w-1,y)) for y in range(h)]
        r["opaque_border_pct"]=round(sum(1 for v in ring if v>200)/len(ring)*100,1)
        r["semi_transparent_pct"]=round(sum(hist[1:255])/n*100,1)
        r["ok"]=r["transparent_pct"]>5 and r["opaque_border_pct"]<5 and r["semi_transparent_pct"]<=8
    else:
        r["alpha"]=False; r["ok"]=False
    out.append(r)
print(json.dumps(out))'''
    py = PY_PIL if os.path.exists(PY_PIL) else sys.executable
    r = subprocess.run([py, "-c", code, *[os.path.expanduser(x) for x in paths]], capture_output=True, text=True)
    try: return json.loads(r.stdout)
    except Exception: return [{"error": r.stderr[-400:]}]

def run_job(jid, items, common):
    J = JOBS[jid]
    for it in items:
        if J.get("cancel"): break
        k = dict(common); k.update(it); name = k.pop("name", None) or f"item{len(J['done'])}"
        out = k.pop("out_path", None) or os.path.join(common["out_dir"], name + ".png"); k.pop("out_dir", None)
        J["current"] = name
        try:
            J["done"].append({"name": name, **generate(k.pop("prompt"), out, **{x: k[x] for x in ("refs", "size", "transparent", "style_bible", "kind") if x in k})})
        except Exception as e:
            J["failed"].append({"name": name, "error": str(e)[:600]})
    J["current"] = None; J["status"] = "finished"; J["finished_at"] = time.time()
    try: json.dump(J, open(os.path.join(common["out_dir"], f"job-{jid}.json"), "w"), indent=1, default=str)
    except Exception: pass

TOOLS = [
 {"name": "image_generate", "description": "Generate ONE image with Codex built-in image_gen (ChatGPT login) and save it to out_path (PNG). Blocks ~1–3 min. Pass the same canonical refs + style_bible on every call for a consistent set. kind='part' for one rig part, 'plate' for one depth layer.",
  "inputSchema": {"type": "object", "required": ["prompt", "out_path"], "properties": {
    "prompt": {"type": "string"}, "out_path": {"type": "string"}, "refs": {"type": "array", "items": {"type": "string"}},
    "size": {"type": "string", "description": "e.g. 1536x1024, 1024x1024, 1024x1536"}, "transparent": {"type": "boolean"},
    "style_bible": {"type": "string", "description": "path to style_bible.txt or the text itself"},
    "kind": {"type": "string", "enum": ["image", "part", "plate"]}}}},
 {"name": "image_parts", "description": "Background job: generate many images one by one (one Codex call each, sequential to save RAM). Use for modular rig parts of one character/object (head, torso, upper_arm_l, forearm_l, hand_l, thigh_l, shin_l, foot_l, … each transparent, kind='part') or depth plates (sky, far, mid, near, foreground debris; kind='plate'). Returns job_id; poll image_job.",
  "inputSchema": {"type": "object", "required": ["items", "out_dir"], "properties": {
    "items": {"type": "array", "items": {"type": "object", "required": ["name", "prompt"], "properties": {"name": {"type": "string"}, "prompt": {"type": "string"}, "transparent": {"type": "boolean"}, "kind": {"type": "string"}, "size": {"type": "string"}}}},
    "out_dir": {"type": "string"}, "refs": {"type": "array", "items": {"type": "string"}}, "style_bible": {"type": "string"},
    "transparent": {"type": "boolean"}, "kind": {"type": "string", "enum": ["image", "part", "plate"]}, "size": {"type": "string"}}}},
 {"name": "image_job", "description": "Status of an image_parts job (done/failed/current). cancel=true stops after the current item.",
  "inputSchema": {"type": "object", "required": ["job_id"], "properties": {"job_id": {"type": "string"}, "cancel": {"type": "boolean"}}}},
 {"name": "image_check", "description": "Check PNGs: size, real alpha, transparent %, opaque border % (must be <5 for a cut-out), edge colour (halo).",
  "inputSchema": {"type": "object", "required": ["paths"], "properties": {"paths": {"type": "array", "items": {"type": "string"}}}}},
]

def call(name, a):
    if name == "image_generate":
        return generate(a["prompt"], a["out_path"], a.get("refs"), a.get("size"), a.get("transparent", False), a.get("style_bible"), a.get("kind", "image"))
    if name == "image_parts":
        jid = uuid.uuid4().hex[:8]; common = {k: a[k] for k in ("out_dir", "refs", "style_bible", "transparent", "kind", "size") if k in a}
        common["out_dir"] = os.path.abspath(os.path.expanduser(a["out_dir"])); os.makedirs(common["out_dir"], exist_ok=True)
        JOBS[jid] = {"job_id": jid, "status": "running", "total": len(a["items"]), "done": [], "failed": [], "current": None, "started_at": time.time()}
        threading.Thread(target=run_job, args=(jid, a["items"], common), daemon=True).start()
        return {"job_id": jid, "total": len(a["items"]), "note": "poll image_job; each item ~1–3 min"}
    if name == "image_job":
        J = JOBS.get(a["job_id"])
        if not J: return {"error": "unknown job_id (server restarted?) — look for job-<id>.json in out_dir"}
        if a.get("cancel"): J["cancel"] = True
        return {k: J[k] for k in ("job_id", "status", "total", "current", "done", "failed")}
    if name == "image_check":
        return check(a["paths"])
    raise ValueError("unknown tool " + name)

def send(m): sys.stdout.write(json.dumps(m) + "\n"); sys.stdout.flush()

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try: m = json.loads(line)
        except Exception: continue
        mid, meth = m.get("id"), m.get("method")
        if mid is None: continue  # notification
        try:
            if meth == "initialize":
                send({"jsonrpc": "2.0", "id": mid, "result": {"protocolVersion": m.get("params", {}).get("protocolVersion", "2025-06-18"),
                      "capabilities": {"tools": {}}, "serverInfo": {"name": "codex-image", "version": "1.0.0"}}})
            elif meth == "tools/list":
                send({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
            elif meth == "tools/call":
                p = m["params"]; r = call(p["name"], p.get("arguments", {}))
                send({"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": json.dumps(r, ensure_ascii=False, indent=1)}]}})
            elif meth == "ping":
                send({"jsonrpc": "2.0", "id": mid, "result": {}})
            else:
                send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "method not found"}})
        except Exception as e:
            if meth == "tools/call":
                send({"jsonrpc": "2.0", "id": mid, "result": {"isError": True, "content": [{"type": "text", "text": str(e)[:2000]}]}})
            else:
                send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32000, "message": str(e)[:500]}})

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--test":  # direct CLI test: --test OUT.png "prompt" [ref...]
        print(json.dumps(generate(sys.argv[3], sys.argv[2], sys.argv[4:] or None, "1024x1024", True, kind="part"), indent=1)); sys.exit()
    main()
