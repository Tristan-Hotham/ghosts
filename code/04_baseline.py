"""Step 4. The baseline of old notable buildings, pubs and castles, with the same kinds and regions as the haunted places.

* Listed buildings: every Wikidata item designated Grade I, Grade II* (England and Wales) or Category A (Scotland) with
  coordinates (40,410 items; Wikidata CC0, queried 27 Oct 2026). Kind from the Wikidata class label (kinds.LISTED_CLASS),
  or, for generic labels such as "building", from the item's name. Walls, gates, monuments, bridges and the like are kept
  but marked as non-buildings. Inception (P571) is kept where Wikidata has it.
* Pubs: OpenStreetMap amenity=pub in the UK (ODbL).
* Castles: Wikidata UK items of class castle, tower house and similar (from the UK structures bundle), deduplicated.
Region: nearest OS Open Names populated place (Great Britain).
Outputs: data/listed_baseline.csv.gz, work/pubs.json, work/castles.json
"""
import json, os, re, csv
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from pyproj import Transformer
from common import *
from kinds import kind_of, CLASS2KIND, NON_BUILDING, BUILDING_KINDS

B = load_bundle()
os_ = pd.read_csv(OSNAMES, sep="\t", usecols=["name1", "type", "x", "y", "district", "county", "region", "country"], dtype=str)
pp = os_[os_.type == "populatedPlace"].reset_index(drop=True)
tree = cKDTree(np.c_[pp.x.astype(float), pp.y.astype(float)])
tr = Transformer.from_crs(4326, 27700, always_xy=True)


def regionise(lat, lon):
    x, y = tr.transform(np.asarray(lon), np.asarray(lat))
    d, i = tree.query(np.c_[x, y])
    r = pp.iloc[i]
    dist = r.district.where(r.district.notna(), r.county).values
    return r.country.values, r.region.values, r.county.values, dist, d, x, y


DES = {"Q15700818": "Grade I", "Q15700831": "Grade II*", "Q10729054": "Category A"}
rows = {}
for r in tsv_rows(B["wd_listed_top"]):
    q = qid(r["x"])
    la, lo = wkt(r["coord"])
    y = year(r["inception"])
    if q in rows:
        if y is not None and (rows[q]["year"] is None or y < rows[q]["year"]):
            rows[q]["year"] = y
        continue
    rows[q] = dict(wikidata=q, label=lit(r["xLabel"]), grade=DES.get(qid(r["des"]), ""), cls=lit(r["clsLabel"]), lat=la, lon=lo, year=y)
L = pd.DataFrame(rows.values())
L = L[L.lat.notna()].reset_index(drop=True)


def kind_row(lab, cls):
    c = (cls or "").lower()
    l = (lab or "").lower()
    if c in CLASS2KIND:
        return CLASS2KIND[c], 1
    if NON_BUILDING.search(c) or NON_BUILDING.search(l.split(",")[0]) and not re.search(r"\b(house|hall|church|castle|inn|chapel)\b", l):
        return ("road" if re.search(r"bridge|viaduct|tunnel", c + " " + l) else "structure"), 0
    k = kind_of(lab, cls)
    if k in (None, "settlement", "outdoor"):
        k = "other_building"
    if k == "road":
        return "road", 0
    return k, 1


kk = [kind_row(a, b) for a, b in zip(L.label, L.cls)]
L["kind"] = [k for k, _ in kk]
L["is_building"] = [b for _, b in kk]
co, rg, cy, di, dd, x, y = regionise(L.lat.values, L.lon.values)
L["country"], L["region"], L["county"], L["district"] = co, rg, cy, di
L["km_to_os_place"] = np.round(dd / 1000, 2)
L = L[L.km_to_os_place < 30]  # drops a few items with wrong coordinates far offshore
L.to_csv(os.path.join(DATA, "listed_baseline.csv.gz"), index=False, compression="gzip")
print(len(L), "listed items;", L.is_building.sum(), "buildings")
print(L.groupby("country").size().to_string())
print(L[L.is_building == 1].kind.value_counts().to_string())

# pubs
pubs = []
for r in tsv_rows(B["osm_pubs_uk"]):
    la, lo = wkt(r["wkt"])
    if la is None:  # polygons: mean of the vertices
        xy = re.findall(r"([-\d.]+) ([-\d.]+)", r["wkt"])
        if xy:
            lo, la = np.mean([float(a) for a, b in xy]), np.mean([float(b) for a, b in xy])
    if la is not None:
        pubs.append((la, lo))
pubs = np.array(pubs)
co, rg, cy, di, dd, x, y = regionise(pubs[:, 0], pubs[:, 1])
ok = dd < 30000
P = pd.DataFrame(dict(lat=pubs[:, 0], lon=pubs[:, 1], country=co, region=rg, district=di, x=x, y=y, osdist=dd))
gb = P[ok & ~((P.lon < -5.3) & (P.lat < 55.45) & (P.lat > 53.9))]
# share of pubs within 50 m of a Grade I / II* / Category A listed building
lt = cKDTree(np.c_[tr.transform(L.lon.values, L.lat.values)])
d, _ = lt.query(np.c_[gb.x.values, gb.y.values])
gb = gb.assign(near_listed_50=(d <= 50).astype(int))
json.dump(dict(n=int(len(gb)), by_region=gb.groupby("region").size().to_dict(), near_listed_50=float(gb.near_listed_50.mean()),
               by_district=gb.groupby("district").size().to_dict()), open(os.path.join(WORK, "pubs.json"), "w"))
print(len(gb), "GB pubs; within 50 m of a top-listed building:", round(gb.near_listed_50.mean(), 3))

# castles (Wikidata UK structures bundle)
uk = json.load(open(os.path.join(D8, "uk_bundle_wikidata_osm.json")))
CL = {}
CASTLE_CLS = {"castle", "tower house", "ruined castle", "castle ruin", "bastle house", "pele tower", "peel tower", "fortified house", "keep", "shell keep", "concentric castle", "fortified tower", "castle ruins", "palace"}
for r in tsv_rows(uk["wd_structures_tsv"]):
    c = lit(r["clsLabel"]).lower()
    if c not in CASTLE_CLS:
        continue
    q = qid(r["item"]); la, lo = wkt(r["coord"]); yv = year(r["inception"])
    if q in CL:
        if yv is not None and (CL[q]["year"] is None or yv < CL[q]["year"]):
            CL[q]["year"] = yv
        continue
    CL[q] = dict(wikidata=q, label=lit(r["label"]), cls=c, lat=la, lon=lo, year=yv)
C = pd.DataFrame(CL.values()).dropna(subset=["lat"])
co, rg, cy, di, dd, x, y = regionise(C.lat.values, C.lon.values)
C["country"], C["region"], C["district"] = co, rg, di
C = C[dd < 30000]
json.dump(dict(n=int(len(C)), by_region=C.groupby("region").size().to_dict(), years=[int(v) for v in C.year.dropna()],
               qids=C.wikidata.tolist()), open(os.path.join(WORK, "castles.json"), "w"))
print(len(C), "Wikidata castles and tower houses;", C.year.notna().sum(), "dated")
print(C.groupby("region").size().to_string())
