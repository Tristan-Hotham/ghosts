"""Shared paths and helpers for the Ghosts project.

Shared inputs are read in place from the folder one level above this repository (set HIST to override).
"""
import os, re, json, gzip, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HIST = os.environ.get("HIST", os.path.dirname(ROOT))
D10 = os.path.join(HIST, "_data10")
D8 = os.path.join(HIST, "_data8")
OSNAMES = os.path.join(HIST, "osnames_gb.tsv")
NE = os.path.join(HIST, "_data3", "ne", "geojson")
OLDEST = os.path.join(HIST, "oldest-buildings", "data", "buildings.csv")
WORK = os.path.join(ROOT, "work")
DATA = os.path.join(ROOT, "data")
os.makedirs(WORK, exist_ok=True)
os.makedirs(DATA, exist_ok=True)


def load_wiki():
    return json.load(gzip.open(os.path.join(D10, "wikipedia_batch10.json.gz")))


def load_bundle():
    return json.load(gzip.open(os.path.join(D10, "wd_osm_bundle10.json.gz")))


def tsv_rows(text):
    lines = text.split("\n")
    head = [h.lstrip("?") for h in lines[0].split("\t")]
    out = []
    for l in lines[1:]:
        if not l.strip():
            continue
        f = l.split("\t")
        f += [""] * (len(head) - len(f))
        out.append(dict(zip(head, f)))
    return out


def qid(s):
    m = re.search(r"(Q\d+)", s or "")
    return m.group(1) if m else ""


def lit(s):
    s = s or ""
    m = re.match(r'^"(.*)"(@\w+)?$', s)
    return m.group(1) if m else s


def wkt(s):
    m = re.search(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)", s or "")
    return (float(m.group(2)), float(m.group(1))) if m else (None, None)


def year(s):
    m = re.match(r"^(-?)(\d{1,4})-", s or "")
    if not m:
        return None
    y = int(m.group(2))
    return -y if m.group(1) else y


def hav(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
