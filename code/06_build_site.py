"""Step 6. Build ../index.html from page_template.html, and ../README.md from README_template.md.

Every number in the text is a placeholder like {{mix.castle.ratio|f1}}, filled from ../data/results.json.
Map points and chart data are embedded in the page as `const D = ...`.
Formats: int, pct0, pct1, f1, f2, x1 (ratio with a times sign written as "times"), p, words, Words, raw.
Run: python3 code/06_build_site.py
"""
import json, os, re
import pandas as pd
from common import ROOT, DATA

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(DATA, "results.json")))
H = pd.read_csv(os.path.join(DATA, "haunted_places.csv"), keep_default_na=False, na_values=[""])
CAST = ["grey_lady", "white_lady", "green_lady", "other_lady", "monk", "nun", "headless", "drummer", "dog", "soldier", "child", "poltergeist", "coach", "royal"]


def place_str(r):
    if r.country in ("Ireland", "Northern Ireland"):
        return r.country
    p = r.county if isinstance(r.county, str) else (r.district if isinstance(r.district, str) else "")
    return ", ".join(x for x in [p, r.country] if x)


pts = []
for _, r in H[H.lat.notna()].iterrows():
    g = ",".join(c for c in CAST if r["g_" + c] == 1)
    pts.append([round(r.lat, 5), round(r.lon, 5), r["name"], r.kind, place_str(r), r.listed if isinstance(r.listed, str) else "",
                int(r.year) if pd.notna(r.year) else None, g, r.ghost_sentence if isinstance(r.ghost_sentence, str) else "",
                r.wikipedia_url if isinstance(r.wikipedia_url, str) else "", r.geo_method, r.geo_precision if isinstance(r.geo_precision, str) else "",
                r.year_source if isinstance(r.year_source, str) else ""])
site = dict(P=pts, MIX=R["mix"], REG=R["regions"], CK=R["cast_by_kind"], CC=R["cast_by_country"], CL=R["cast_labels"], AGE=R["age"],
            YB=R["year_bins"], YH=R["year_hist"], CAS=R["castles_by_country"], CITY=R["cities"], GBR=R["gb_per_1000"],
            KL=R["kind_labels"], INN=R["inns_near_listed"])
# percentile strip: recomputed here from the data files exactly as in 05_analyse.py
L = pd.read_csv(os.path.join(DATA, "listed_baseline.csv.gz"))
LD = L[(L.is_building == 1) & L.year.notna() & (L.year > 0)]
HD = H[(H.is_building == 1) & H.year.notna()]
strip = []
for _, r in HD.iterrows():
    l = LD[LD.kind == r.kind].year.values
    if len(l) < 30:
        continue
    strip.append([r["name"], r.kind, int(r.year), round(float(((l < r.year).sum() + 0.5 * (l == r.year).sum()) / len(l)), 4)])
site["STRIP"] = strip
assert len(strip) == R["age_percentile"]["n"]


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f0": return f"{v:.0f}"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "yr": return f"{int(round(v))}"
    if f == "p": return "below 0.001" if v < 0.001 else f"{v:.3f}"
    if f == "per100": return f"{v * 100:.0f}"
    if f == "words":
        w = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split()
        return w[int(v)] if int(v) < len(w) else f"{int(v):,}"
    if f == "Words": return fmt(v, "words").capitalize()
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


def fill(t):
    return re.sub(r"\{\{(.+?)\}\}", sub, t)


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
    json.dump(site, open(os.path.join(ROOT, "work", "site.json"), "w"), ensure_ascii=False)
    t = fill(open(os.path.join(HERE, "page_template.html")).read())
    data = json.dumps(site, separators=(",", ":"), ensure_ascii=False).replace("–", "-").replace("—", "-").replace("</", "<\\/")
    t = t.replace("/*DATA*/", "const D = " + data + ";")
    open(os.path.join(ROOT, "index.html"), "w").write(t)
    print("index.html", len(t.encode()) // 1024, "KB")
    open(os.path.join(ROOT, "README.md"), "w").write(fill(open(os.path.join(HERE, "README_template.md")).read()))
    print("README.md written")
