# Tiny render server for a RunPod pod: installs Blender, takes a zipped bundle, renders, serves the frames.
import os, json, threading, subprocess, zipfile, io, glob, http.server, urllib.request, tarfile, traceback
TOKEN = os.environ.get("JOBTOKEN", "")
BL = "https://download.blender.org/release/Blender5.2/blender-5.2.3-linux-x64.tar.xz"
ST = {"blender": "installing", "render": "idle", "error": None}
J = "/job"; os.makedirs(J + "/out", exist_ok=True)
def log(m):
    with open(J + "/log.txt", "a") as f: f.write(m + "\n")
def setup():
    try:
        subprocess.run("apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq xz-utils libx11-6 libxi6 libxxf86vm1 libxfixes3 libxrender1 libgl1 libegl1 libxkbcommon0 libsm6 libice6 >> /job/log.txt 2>&1", shell=True)
        urllib.request.urlretrieve(BL, "/tmp/b.tar.xz"); log("downloaded")
        subprocess.run("mkdir -p /opt/blender && tar -xJf /tmp/b.tar.xz -C /opt/blender --strip-components=1", shell=True, check=True)
        r = subprocess.run(["/opt/blender/blender", "-b", "--version"], capture_output=True, text=True); log(r.stdout[-300:] + r.stderr[-300:])
        ST["blender"] = "ready"
    except Exception: ST["blender"] = "failed"; ST["error"] = traceback.format_exc(); log(ST["error"])
def render():
    try:
        ST["render"] = "running"; src = J + "/src"
        for a, b in json.load(open(src + "/ranges.json")):
            cmd = ["/opt/blender/blender", "-b", src + "/bottle-v6-shot.blend", "--python", src + "/front_hole.py", "--python", src + "/land_seq.py",
                   "--python", src + "/clear_bg.py", "--python", src + "/hq.py", "-a", "--", "0", J + "/out/f_", str(a), str(b)]
            with open(J + "/blender.log", "a") as f: p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
            log("range %s-%s exit %s" % (a, b, p.returncode))
        ST["render"] = "done"
    except Exception: ST["render"] = "failed"; ST["error"] = traceback.format_exc(); log(ST["error"])
class H(http.server.BaseHTTPRequestHandler):
    def ok(self):
        if self.headers.get("X-Token") != TOKEN: self.send_response(403); self.end_headers(); return False
        return True
    def send(self, body, ct="application/json"):
        self.send_response(200); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path == "/ping": return self.send(b"pong", "text/plain")
        if not self.ok(): return
        if self.path == "/status":
            outs = sorted(os.path.basename(p) for p in glob.glob(J + "/out/*.png"))
            tail = open(J + "/blender.log").read()[-1500:] if os.path.exists(J + "/blender.log") else ""
            return self.send(json.dumps(dict(ST, frames=outs, tail=tail, log=open(J + "/log.txt").read()[-1500:] if os.path.exists(J + "/log.txt") else "")).encode())
        if self.path.startswith("/file/"):
            p = J + "/out/" + os.path.basename(self.path[6:])
            if os.path.exists(p): return self.send(open(p, "rb").read(), "application/octet-stream")
        self.send_response(404); self.end_headers()
    def do_POST(self):
        if not self.ok(): return
        if self.path == "/bundle" and ST["blender"] == "ready" and ST["render"] in ("idle", "failed", "done"):
            data = self.rfile.read(int(self.headers["Content-Length"]))
            zipfile.ZipFile(io.BytesIO(data)).extractall(J + "/src")
            threading.Thread(target=render, daemon=True).start(); return self.send(b'{"started":true}')
        self.send_response(409); self.end_headers()
    def log_message(self, *a): pass
threading.Thread(target=setup, daemon=True).start()
http.server.ThreadingHTTPServer(("0.0.0.0", 8000), H).serve_forever()
