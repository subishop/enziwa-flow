"""Pack the page's animation frames into sprite sheets (15 Nov 2026).

Why: from Kampala each file from GitHub takes about a second to start, and the page used about 450 single frames,
so the spray, bottle and notes arrived a minute or more late. 12 sheets replace them.

Needs the single frames (from the render pipeline) in img (bs_, bl_, bd_, bo_, obs_, obl_, obd_, obo_) and
img/k8 (w_ mist, m_ masks). Writes img/sheet-*.webp. Run from the site-flow folder:
    python tools/make_sheets.py
Bottle sheets keep only the strip the bottle occupies (BOX), 10 frames per row; the page's BOTC must match BOX.
Mist is stored at half size in 3 sheets of 50 (10 per row); masks at half size in one sheet (15 per row).
"""
from PIL import Image
import glob, math, os

D = "img"
BOX = (752, 96, 956, 880); CW, CH = 204, 784
for pre in ("bs", "bl", "bd", "bo", "obs", "obl", "obd", "obo"):
    fs = sorted(glob.glob(f"{D}/{pre}_*.webp")); n = len(fs)
    if not n: continue
    cols = 10; rows = math.ceil(n / cols)
    sh = Image.new("RGBA", (cols * CW, rows * CH), (0, 0, 0, 0))
    for k, f in enumerate(fs): sh.paste(Image.open(f).convert("RGBA").crop(BOX), ((k % cols) * CW, (k // cols) * CH))
    sh.save(f"{D}/sheet-{pre}.webp", "WEBP", quality=90, alpha_quality=95, method=6); print(pre, n, sh.size)
ws = sorted(glob.glob(f"{D}/k8/w_*.webp"))
for s in range(3):
    sh = Image.new("RGB", (10 * 427, 5 * 240))
    for k, f in enumerate(ws[s * 50:(s + 1) * 50]):
        sh.paste(Image.open(f).convert("RGB").resize((427, 240), Image.LANCZOS), ((k % 10) * 427, (k // 10) * 240))
    sh.save(f"{D}/sheet-k8-w{s}.webp", "WEBP", quality=85, method=6); print("mist", s)
ms = sorted(glob.glob(f"{D}/k8/m_*.webp"))
if ms:
    sh = Image.new("RGBA", (15 * 214, 5 * 240), (0, 0, 0, 0))
    for k, f in enumerate(ms): sh.paste(Image.open(f).convert("RGBA").resize((214, 240), Image.LANCZOS), ((k % 15) * 214, (k // 15) * 240))
    sh.save(f"{D}/sheet-k8-m.webp", "WEBP", lossless=True, method=6); print("masks")
