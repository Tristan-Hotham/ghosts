"""r/dataisbeautiful collage for Haunted, or Just Old? (2400 x 3000 px).
Every number comes from ../data/results.json and the data files. Run from anywhere: python3 reddit/collage.py
Fonts: FONT_DIR with FrauncesVar.ttf, SourceSerif4-*.ttf and IBMPlexMono-*.ttf (github.com/google/fonts).
"""
import json, os, math
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import shapely
from shapely.geometry import shape, box

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
HIST = os.environ.get("HIST", os.path.dirname(ROOT))
F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts") + "/"
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(F + f)
DISP = fm.FontProperties(fname=F + "FrauncesVar.ttf", weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, LAND, LANDE = "#E9E6EF", "#1D1926", "#5B5569", "#DAD5E2", "#C2BBCD"
GHO, GHO2, BAND = "#0B7A85", "#7FD0D4", "#B3ACBF"

R = json.load(open(os.path.join(ROOT, "data", "results.json")))
S = json.load(open(os.path.join(ROOT, "work", "site.json")))
P = pd.DataFrame(S["P"], columns=["lat", "lon", "name", "kind", "place", "listed", "year", "g", "sent", "url", "gm", "prec", "ysrc"])
K = math.cos(math.radians(54.5))
land = shapely.union_all([shape(f["geometry"]) for f in json.load(open(os.path.join(HIST, "_data3", "ne", "geojson", "ne_10m_land.geojson")))["features"]]).intersection(box(-10.8, 49.8, 2.0, 59.0))
LANDP = [p for p in shapely.get_parts(land) if p.area > 0.002 and not (p.representative_point().x > 0.9 and p.representative_point().y < 51.2)]
pc = lambda v: f"{v * 100:.0f}%"

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
# soft mist bands
for i, a in enumerate(np.linspace(0.0, 0.05, 6)):
    fig.add_artist(plt.Rectangle((0, 0.30 + i * 0.09), 1, 0.05, transform=fig.transFigure, color="white", alpha=a, lw=0))

# title
fig.text(0.045, 0.972, "Is a haunted place", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(0.045, 0.925, "just an old place?", fontproperties=DISP, fontsize=50, color=GHO, va="top", style="italic")
fig.text(0.045, 0.874, f"{R['n_places']} reportedly haunted places in Britain and Ireland from Wikipedia, set against the "
         f"{R['n_listed_all']:,} Grade I,\nGrade II* and Category A listed buildings in Wikidata. The answer: no. It is a particular kind of old place.",
         family=SER, fontsize=14.5, color=FG, va="top", linespacing=1.4)

# hero map
ax = fig.add_axes([0.015, 0.29, 0.58, 0.5])
for p in LANDP:
    x, y = p.exterior.xy
    ax.fill(np.array(x) * K, y, color=LAND, ec=LANDE, lw=0.7, zorder=1)
X, Y = P.lon * K, P.lat
for s, a in [(900, 0.035), (420, 0.06), (160, 0.10)]:
    ax.scatter(X, Y, s=s, c=GHO2, alpha=a, lw=0, zorder=2)
GRP = {"castle": "castle", "inn": "inn", "church": "church", "house": "house"}
MK = {"castle": ("s", "Castles and towers"), "house": ("o", "Houses, halls, palaces"), "inn": ("D", "Inns, pubs, hotels"), "church": ("^", "Churches and abbeys")}
for k, (m, lab) in MK.items():
    q = P[P.kind == k]
    ax.scatter(q.lon * K, q.lat, s=34 if k != "inn" else 26, marker=m, c=FG, edgecolors="white", lw=0.6, zorder=4, label=f"{lab}  {len(q)}")
q = P[~P.kind.isin(MK)]
ax.scatter(q.lon * K, q.lat, s=24, marker="o", facecolor="white", edgecolors=GHO, lw=1.2, zorder=3, label=f"Other places  {len(q)}")
ax.set_xlim(-10.7 * K, 1.9 * K); ax.set_ylim(49.85, 58.95); ax.set_aspect(1); ax.axis("off")
h, l = ax.get_legend_handles_labels()
fig.legend(h, l, loc="lower left", bbox_to_anchor=(0.035, 0.288), frameon=False, prop={"family": MONO, "size": 10}, labelcolor=FG, handletextpad=0.3, labelspacing=0.45)
for nm, lab, dx, dy in [("Edinburgh Castle", "Edinburgh", 1.4, 0.5), ("Tower of London", "London", 1.0, -0.8)]:
    r = P[P.name == nm].iloc[0]
    ax.annotate(lab, (r.lon * K, r.lat), (r.lon * K + dx * K, r.lat + dy), family=SER, fontsize=12, style="italic", color=FG,
                arrowprops=dict(arrowstyle="-", color=FG, lw=0.6), zorder=6, va="center")

# right column: big numbers
m = R["mix"]
notes = [
    (f"{m['castle']['ratio']:.0f}×", f"Castles are {pc(m['castle']['share_haunted'])} of haunted buildings\nbut {m['castle']['share_listed']*100:.1f}% of listed ones. Inns: {pc(m['inn']['share_haunted'])}\nagainst {m['inn']['share_listed']*100:.1f}%, {m['inn']['ratio']:.1f} times as common."),
    (f"{m['church']['ratio']:.2f}×", f"Churches are {pc(m['church']['share_listed'])} of listed buildings\nand the oldest of all. Only {m['church']['haunted']} of the\n{R['n_haunted_gb_buildings']} haunted buildings are churches."),
    (f"{R['age_percentile']['median']*100:.0f}th", f"percentile of its kind: where the median\nhaunted building's date falls among listed\nbuildings of the same kind. Barely older\nthan typical (95% range {R['age_percentile']['lo']*100:.0f} to {R['age_percentile']['hi']*100:.0f})."),
    (f"{R['scot_vs_eng_ratio']:.1f}×", f"haunted places per listed building,\nScotland against England. {pc(R['castle_share_scotland'])} of\nScotland's haunted buildings are castles\nor tower houses; England: {pc(R['castle_share_england'])}."),
]
tx = fig.add_axes([0.615, 0.31, 0.37, 0.49]); tx.axis("off")
for (big, small), y in zip(notes, [1.0, 0.765, 0.535, 0.235]):  # four blocks
    tx.text(0, y, big, fontproperties=DISP, fontsize=40, color=GHO, va="top", transform=tx.transAxes)
    tx.text(0, y - 0.088, small, family=SER, fontsize=12.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)

# bottom row: three small multiples
fig.text(0.045, 0.262, "WHAT KIND OF PLACE", family=MONO, fontsize=11, color=MUT)
fig.text(0.375, 0.262, "HOW OLD, WITHIN ITS KIND", family=MONO, fontsize=11, color=MUT)
fig.text(0.705, 0.262, "WHO HAUNTS WHERE", family=MONO, fontsize=11, color=MUT)
a = fig.add_axes([0.115, 0.115, 0.22, 0.125], facecolor=BG)
ks = ["castle", "inn", "house", "church"]; lab = {"castle": "Castle", "inn": "Inn", "house": "House", "church": "Church"}
y = np.arange(len(ks))[::-1]
a.barh(y + 0.2, [m[k]["share_haunted"] * 100 for k in ks], 0.38, color=GHO, label="haunted")
a.barh(y - 0.2, [m[k]["share_listed"] * 100 for k in ks], 0.38, color=BAND, label="listed")
for yy, k in zip(y, ks):
    a.text(max(m[k]["share_haunted"], m[k]["share_listed"]) * 100 + 1.5, yy, f"{m[k]['share_haunted']*100:.0f} v {m[k]['share_listed']*100:.0f}", va="center", family=MONO, fontsize=10, color=FG)
a.set_yticks(y); a.set_yticklabels([lab[k] for k in ks], family=SER, fontsize=12.5, color=FG); a.set_xlim(0, 58); a.set_xticks([])
for s in a.spines.values(): s.set_visible(False)
a.tick_params(length=0)
a.text(0, -1.0, "teal: % of haunted; grey: % of listed", family=MONO, fontsize=9.5, color=MUT)

b = fig.add_axes([0.47, 0.115, 0.2, 0.125], facecolor=BG)
st = pd.DataFrame(S["STRIP"], columns=["name", "kind", "year", "pct"])
rows = [("Castle", st[st.kind == "castle"]), ("House", st[st.kind == "house"]), ("Other", st[~st.kind.isin(["castle", "house"])])]
rng = np.random.default_rng(5)
for i, (lb, q) in enumerate(rows):
    yy = 2 - i
    b.scatter(q.pct * 100, yy + rng.uniform(-0.25, 0.25, len(q)), s=22, c=GHO, alpha=0.75, lw=0, zorder=3)
    b.plot([q.pct.median() * 100] * 2, [yy - 0.38, yy + 0.38], color=FG, lw=2.2, zorder=4)
    b.text(-4, yy, f"{lb} ({len(q)})", ha="right", va="center", family=SER, fontsize=12, color=FG)
b.axvline(50, color=MUT, ls="--", lw=1)
b.set_xlim(0, 100); b.set_ylim(-0.6, 2.6); b.set_yticks([]); b.set_xticks([0, 50, 100]); b.set_xticklabels(["older", "middle", "newer"], family=MONO, fontsize=9.5, color=MUT)
for s in ("top", "right", "left"): b.spines[s].set_visible(False)
b.spines["bottom"].set_color(MUT); b.tick_params(length=0)

c = fig.add_axes([0.81, 0.11, 0.16, 0.125], facecolor=BG)
figs = [("white_lady", "White Lady"), ("grey_lady", "Grey Lady"), ("green_lady", "Green Lady"), ("monk", "Monk"), ("nun", "Nun"), ("poltergeist", "Poltergeist")]
cols = [("castle", "Cas."), ("house", "Hse"), ("inn", "Inn"), ("church", "Chu.")]
M = np.array([[R["cast_by_kind"][k][g] for k, _ in cols] for g, _ in figs])
cmap = matplotlib.colors.LinearSegmentedColormap.from_list("g", ["#F4F2F7", GHO2, GHO, "#06474E"])
c.imshow(M, cmap=cmap, vmin=0, vmax=M.max(), aspect="auto")
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        if M[i, j]:
            c.text(j, i, str(M[i, j]), ha="center", va="center", family=MONO, fontsize=10, color="white" if M[i, j] >= 4 else FG)
c.set_xticks(range(len(cols))); c.set_xticklabels([l for _, l in cols], family=MONO, fontsize=9.5, color=FG)
c.set_yticks(range(len(figs))); c.set_yticklabels([l for _, l in figs], family=SER, fontsize=11.5, color=FG)
c.xaxis.tick_top(); c.tick_params(length=0)
for s in c.spines.values(): s.set_visible(False)
c.set_xticks(np.arange(-.5, len(cols)), minor=True); c.set_yticks(np.arange(-.5, len(figs)), minor=True)
c.grid(which="minor", color=BG, lw=2); c.tick_params(which="minor", length=0)
fig.text(0.705, 0.088, f"No inn has a coloured lady; {R['green_scot_castle']} of\n{R['cast']['green_lady']} Green Ladies are in Scottish castles.", family=MONO, fontsize=9.5, color=MUT, va="top", linespacing=1.35)
fig.text(0.045, 0.088, f"{R['n_haunted_gb_buildings']} haunted buildings and {R['n_listed_buildings']:,} listed\nbuildings, Great Britain.", family=MONO, fontsize=9.5, color=MUT, va="top", linespacing=1.35)
fig.text(0.375, 0.088, f"One dot per dated haunted building ({R['age_percentile']['n']}):\nshare of its kind that is older. Bar: median.", family=MONO, fontsize=9.5, color=MUT, va="top", linespacing=1.35)

fig.add_artist(plt.Line2D([0.045, 0.955], [0.047, 0.047], transform=fig.transFigure, color=LANDE, lw=1))
fig.text(0.045, 0.041,
         "Data: haunted places from English Wikipedia categories and lists of reportedly haunted locations (CC BY-SA 4.0), a record of stories written down, not of ghosts.\n"
         "Listed buildings and dates: Wikidata (CC0). Places and regions: OS Open Names (contains OS data © Crown copyright 2026, OGL v3). Pubs: OpenStreetMap (ODbL).\n"
         "Irish sites: Sites and Monuments Record, National Monuments Service (CC BY 4.0). Land: Natural Earth. Analysis and chart: Tristan Hotham, with Python and matplotlib.",
         family=MONO, fontsize=8.2, color=MUT, linespacing=1.35, va="top")
fig.savefig(os.path.join(HERE, "haunted_or_just_old.png"), facecolor=BG, dpi=200)
print("ok")
