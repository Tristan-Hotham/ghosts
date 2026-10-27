"""Step 7. Render ../header.png (1200x630 social card) with Playwright Chromium.
Uses the fonts installed on the system (Fraunces, Source Serif 4, IBM Plex Mono); falls back to serif fonts.
Land outline: Natural Earth 10 m land (public domain), read from HIST/_data3/ne/geojson.
Run: python3 code/07_header.py
"""
import json, math, os
import numpy as np, shapely
from shapely.geometry import shape, box
from playwright.sync_api import sync_playwright
from common import ROOT, NE, DATA

S = json.load(open(os.path.join(ROOT, "work", "site.json")))
R = json.load(open(os.path.join(DATA, "results.json")))
proj = lambda lat, lon: (lon * math.cos(math.radians(54.5)), -lat)
land = shapely.union_all([shape(f["geometry"]) for f in json.load(open(os.path.join(NE, "ne_10m_land.geojson")))["features"]]).intersection(box(-10.8, 49.8, 2.0, 59.0))
x0, y0 = proj(59.0, -10.8); x1, y1 = proj(49.8, 2.0)
H, PAD = 600, 14
sc = (H - 2 * PAD) / (y1 - y0)
P = lambda p: ((p[0] - x0) * sc + PAD, (p[1] - y0) * sc + PAD)
W = (x1 - x0) * sc + 2 * PAD
path = ""
for pg_ in shapely.get_parts(land):
    if pg_.geom_type != "Polygon" or pg_.area < 0.004:
        continue
    c = pg_.representative_point()
    if c.x > 0.9 and c.y < 51.2:  # France
        continue
    pts = [P(proj(la, lo)) for lo, la in np.array(pg_.simplify(0.01).exterior.coords)]
    path += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"
COL = {"castle": "#5A4BA8", "inn": "#B8741A", "church": "#2C78A8", "house": "#B0367A"}
dots = ""
for r in S["P"]:
    x, y = P(proj(r[0], r[1]))
    c = COL.get(r[3], "#3F8A4E" if r[3] in ("theatre", "gaol", "military", "civic", "other_building") else None)
    if c:
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="#0B7A85" fill-opacity=".10"/><circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="{c}" stroke="#F7F5FA" stroke-width="1"/>'
    else:
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="#F7F5FA" stroke="#5B5569" stroke-width="1.5"/>'
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;width:1200px;height:630px;background:#ECE9F0;color:#1D1926;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:70px;top:62px;font:400 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#5B5569;display:flex;gap:12px;align-items:center}}
.k b{{background:#1D1926;color:#ECE9F0;padding:7px 9px;font-weight:400}}
h1{{position:absolute;left:64px;top:104px;margin:0;font:900 112px/.9 Fraunces,Georgia,serif;letter-spacing:-.02em}}
h1 em{{font-style:italic;font-weight:600;color:#0B7A85;display:block}}
p{{position:absolute;left:70px;top:330px;width:640px;margin:0;font-size:26px;line-height:1.36}}
.f{{position:absolute;left:70px;bottom:40px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#5B5569}}
svg{{position:absolute;right:30px;top:15px}}
</style></head><body>
<div class="k"><b>Data study</b><span>Folklore × buildings</span></div>
<h1>Haunted,<em>or just old?</em></h1>
<p>{R['n_places']} reportedly haunted places against {R['n_listed_all']:,} top-listed buildings. Castles are {R['mix']['castle']['ratio']:.0f} times as common among the haunted; churches almost absent.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{W:.0f}" height="{H}" viewBox="0 0 {W:.0f} {H}"><path d="{path}" fill="#DDD8E5" stroke="#B8B1C5" stroke-width="1"/>{dots}</svg>
</body></html>"""
tmp = os.path.join(ROOT, "work", "header.html")
open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")
