"""Step 5. All the comparisons. Writes data/results.json (every number used anywhere) and the small result tables.

Run: python3 code/05_analyse.py
"""
import json, os, re
import numpy as np, pandas as pd
from scipy import stats
from scipy.spatial import cKDTree
from pyproj import Transformer
from common import *
from kinds import LABEL, BUILDING_KINDS
import importlib
cl = importlib.import_module("03_classify") if False else None

H = pd.read_csv(os.path.join(DATA, "haunted_places.csv"))
L = pd.read_csv(os.path.join(DATA, "listed_baseline.csv.gz"))
PUBS = json.load(open(os.path.join(WORK, "pubs.json")))
CAS = json.load(open(os.path.join(WORK, "castles.json")))
ENT = json.load(open(os.path.join(WORK, "entries.json")))
GB = ["England", "Scotland", "Wales"]
R = {}
rng = np.random.default_rng(20261027)

# ---------- 1. the record ----------
R["n_places"] = int(len(H))
R["n_excluded"] = len(ENT["excluded"])
R["by_country"] = H.country.value_counts().to_dict()
R["n_placed"] = int(H.lat.notna().sum())
R["n_unplaced"] = int(H.lat.isna().sum())
R["geo_methods"] = H.geo_method.value_counts().to_dict()
R["geo_precision"] = H.geo_precision.fillna("not placed").value_counts().to_dict()
src = H.sources.str.split("|")
R["n_from_categories"] = int(src.apply(lambda s: any(x.startswith("cat_") for x in s)).sum())
R["n_from_lists_only"] = int(src.apply(lambda s: not any(x.startswith("cat_") for x in s)).sum())
R["n_wiltshire_list"] = int(src.apply(lambda s: "list_wiltshire" in s).sum())
R["n_with_ghost_text"] = int((H.ghost_text_chars > 0).sum())
R["n_no_ghost_text"] = int((H.ghost_text_chars == 0).sum())
R["n_dated"] = int(H.year.notna().sum())
R["dated_sources"] = {"wikidata": int(H.year_source.fillna("").str.startswith("Wikidata").sum()),
                      "oldest": int(H.year_source.fillna("").str.startswith("Oldest").sum()),
                      "infobox": int(H.year_source.fillna("").str.startswith("Wikipedia").sum())}
R["kinds"] = {k: int(v) for k, v in H.kind.value_counts().items()}
R["kind_labels"] = LABEL
R["n_buildings"] = int(H.is_building.sum())
R["n_not_buildings"] = int((H.is_building == 0).sum())
R["listed_status"] = H.listed.fillna("").replace("", "not top-listed").value_counts().to_dict()

# ---------- 2. what kinds of places: haunted buildings in Great Britain against the listed buildings ----------
HB = H[(H.is_building == 1) & H.country.isin(GB)]
LB = L[L.is_building == 1]
R["n_haunted_gb_buildings"] = int(len(HB))
R["n_listed_buildings"] = int(len(LB))
R["n_listed_all"] = int(len(L))
R["listed_by_country"] = L.groupby("country").size().to_dict()
R["listed_buildings_by_country"] = LB.groupby("country").size().to_dict()
mix = {}
for k in BUILDING_KINDS:
    h = int((HB.kind == k).sum()); l = int((LB.kind == k).sum())
    ph, pl = h / len(HB), l / len(LB)
    bt = stats.binomtest(h, len(HB), pl)
    mix[k] = dict(label=LABEL[k], haunted=h, listed=l, share_haunted=ph, share_listed=pl, ratio=ph / pl if pl else None,
                  p=float(bt.pvalue), per_1000_listed=1000 * h / l if l else None)
R["mix"] = mix
# by country too
mixc = {}
for c in GB:
    hb, lb = HB[HB.country == c], LB[LB.country == c]
    mixc[c] = {k: dict(haunted=int((hb.kind == k).sum()), listed=int((lb.kind == k).sum()),
                       share_haunted=float((hb.kind == k).mean()) if len(hb) else 0, share_listed=float((lb.kind == k).mean())) for k in BUILDING_KINDS}
    mixc[c]["n_haunted"] = int(len(hb)); mixc[c]["n_listed"] = int(len(lb))
R["mix_by_country"] = mixc

# ---------- 3. are haunted buildings top-listed? ----------
tr = Transformer.from_crs(4326, 27700, always_xy=True)
lx, ly = tr.transform(L.lon.values, L.lat.values)
ltree = cKDTree(np.c_[lx, ly])
HBb = HB[HB.geo_precision == "building"].copy()
hx, hy = tr.transform(HBb.lon.values, HBb.lat.values)
d, _ = ltree.query(np.c_[hx, hy])
HBb["near_listed_100"] = ((d <= 100) | (HBb.listed.fillna("") != "")).astype(int)
HBb["near_listed_50"] = ((d <= 50) | (HBb.listed.fillna("") != "")).astype(int)
R["listed_own"] = dict(n=int(len(HB)), is_top_listed=int((HB.listed.fillna("") != "").sum()), share=float((HB.listed.fillna("") != "").mean()))
R["listed_near"] = dict(n=int(len(HBb)), within_100m=int(HBb.near_listed_100.sum()), share_100=float(HBb.near_listed_100.mean()),
                        within_50m=int(HBb.near_listed_50.sum()), share_50=float(HBb.near_listed_50.mean()))
inns = HBb[HBb.kind == "inn"]
R["inns_near_listed"] = dict(n=int(len(inns)), within_50m=int(inns.near_listed_50.sum()), share=float(inns.near_listed_50.mean()),
                             pubs_share=PUBS["near_listed_50"], n_pubs=PUBS["n"],
                             p=float(stats.binomtest(int(inns.near_listed_50.sum()), int(len(inns)), PUBS["near_listed_50"]).pvalue))
R["inns_listed_own"] = dict(n=int((HB.kind == "inn").sum()), top_listed=int(((HB.kind == "inn") & (HB.listed.fillna("") != "")).sum()))

# ---------- 4. how old ----------
LD = LB[LB.year.notna() & (LB.year > 0)]
R["n_listed_dated"] = int(len(LD))
R["n_listed_buildings_dated_share"] = float(len(LD) / len(LB))
HD = H[(H.is_building == 1) & H.year.notna()].copy()
R["n_haunted_buildings_dated"] = int(len(HD))
age = {}
for k in ["castle", "house", "inn", "church"]:
    h = HD[HD.kind == k].year.values; l = LD[LD.kind == k].year.values
    if len(h) < 3:
        continue
    u = stats.mannwhitneyu(h, l)
    age[k] = dict(label=LABEL[k], n_haunted=int(len(h)), n_listed=int(len(l)), median_haunted=float(np.median(h)), median_listed=float(np.median(l)),
                  pre1600_haunted=float((h < 1600).mean()), pre1600_listed=float((l < 1600).mean()), p=float(u.pvalue))
R["age"] = age
# percentile of each dated haunted building within listed buildings of the same kind (0 = older than all, 1 = newer than all)
pct = []
for _, r in HD.iterrows():
    l = LD[LD.kind == r.kind].year.values
    if len(l) < 30:
        continue
    pct.append(((l < r.year).sum() + 0.5 * (l == r.year).sum()) / len(l))
pct = np.array(pct)
boot = [np.median(rng.choice(pct, len(pct))) for _ in range(4000)]
R["age_percentile"] = dict(n=int(len(pct)), median=float(np.median(pct)), lo=float(np.percentile(boot, 2.5)), hi=float(np.percentile(boot, 97.5)),
                           share_older_than_typical=float((pct < 0.5).mean()), p_sign=float(stats.binomtest(int((pct < 0.5).sum()), len(pct), 0.5).pvalue))
# same-source check: haunted buildings dated by Wikidata inception only
HW = HD[HD.year_source.str.startswith("Wikidata")]
pw = []
for _, r in HW.iterrows():
    l = LD[LD.kind == r.kind].year.values
    if len(l) >= 30:
        pw.append(((l < r.year).sum() + 0.5 * (l == r.year).sum()) / len(l))
pw = np.array(pw)
R["age_percentile_wikidata_only"] = dict(n=int(len(pw)), median=float(np.median(pw)), share_older_than_typical=float((pw < 0.5).mean()))
R["median_year_haunted_buildings"] = float(HD.year.median())
R["median_year_listed_buildings"] = float(LD.year.median())
R["haunted_pre1600"] = float((HD.year < 1600).mean())
R["listed_pre1600"] = float((LD.year < 1600).mean())
R["haunted_after1800"] = int((HD.year >= 1800).sum())
newest = HD.sort_values("year", ascending=False).head(6)
R["newest_haunted"] = [dict(name=r["name"], year=int(r.year), kind=r.kind) for _, r in newest.iterrows()]
oldest = HD.sort_values("year").head(6)
R["oldest_haunted"] = [dict(name=r["name"], year=int(r.year), kind=r.kind) for _, r in oldest.iterrows()]
# castles: haunted castles' dates against Wikidata castles
cy = np.array(CAS["years"]); cy = cy[cy > 0]
hc = HD[HD.kind == "castle"].year.values
R["castle_age"] = dict(n_haunted=int(len(hc)), n_wikidata=int(len(cy)), median_haunted=float(np.median(hc)), median_wikidata=float(np.median(cy)),
                       p=float(stats.mannwhitneyu(hc, cy).pvalue))
# year histograms for the page
bins = list(range(1000, 2001, 50))
def hist(v):
    v = np.clip(np.asarray(v, float), 1000, 1999)
    return np.histogram(v, bins=bins)[0].tolist()
R["year_bins"] = bins
R["year_hist"] = {k: dict(haunted=hist(HD[HD.kind == k].year), listed=hist(LD[LD.kind == k].year)) for k in ["castle", "house", "inn", "church"]}
R["year_hist_all"] = dict(haunted=hist(HD.year), listed=hist(LD.year))
R["year_before_1000"] = dict(haunted=int((HD.year < 1000).sum()), listed=int((LD.year < 1000).sum()))

# ---------- 5. where: regional density per listed building ----------
HG = H[H.country.isin(GB) & H.region.notna()]
REG = ["Scotland", "North East", "North West", "Yorkshire and the Humber", "East Midlands", "West Midlands", "Eastern", "London", "South East", "South West", "Wales"]
tot_h, tot_l = len(HG), len(L)
reg = {}
for g in REG:
    h = int((HG.region == g).sum()); l = int((L.region == g).sum())
    hb = int(((HG.region == g) & (HG.is_building == 1)).sum())
    exp = tot_h * l / tot_l
    p = float(stats.poisson.sf(h - 1, exp) if h >= exp else stats.poisson.cdf(h, exp))
    hc = int(((HG.region == g) & (HG.kind == "castle")).sum()); nc = int(CAS["by_region"].get(g, 0))
    hi = int(((HG.region == g) & (HG.kind == "inn")).sum()); npb = int(PUBS["by_region"].get(g, 0))
    reg[g] = dict(haunted=h, haunted_buildings=hb, listed=l, per_1000=1000 * h / l, expected=exp, ratio=h / exp, p_one_sided=min(1.0, 2 * p),
                  haunted_castles=hc, wikidata_castles=nc, castles_per_100=100 * hc / nc if nc else None,
                  haunted_inns=hi, pubs=npb, inns_per_10000_pubs=10000 * hi / npb if npb else None)
R["regions"] = reg
R["gb_per_1000"] = 1000 * tot_h / tot_l
R["n_haunted_gb"] = int(tot_h)
# England, Scotland and Wales
R["countries"] = {c: dict(haunted=int((HG.country == c).sum()), listed=int((L.country == c).sum()),
                          per_1000=1000 * (HG.country == c).sum() / (L.country == c).sum()) for c in GB}
R["scot_vs_eng_ratio"] = R["countries"]["Scotland"]["per_1000"] / R["countries"]["England"]["per_1000"]
# castles: Scotland v England
for c in ["Scotland", "England", "Wales"]:
    hc = int(((HG.country == c) & (HG.kind == "castle")).sum())
    nc = int(sum(v for k, v in CAS["by_region"].items() if (k == c) or (c == "England" and k not in ("Scotland", "Wales"))))
    R.setdefault("castles_by_country", {})[c] = dict(haunted=hc, wikidata=nc, per_100=100 * hc / nc)
R["castle_share_scotland"] = float((HB[HB.country == "Scotland"].kind == "castle").mean())
R["castle_share_england"] = float((HB[HB.country == "England"].kind == "castle").mean())
# cities
cities = {}
for nm, key in [("Edinburgh", "City of Edinburgh"), ("York", "York"), ("Oxford", "Oxford"), ("City of Southampton", "City of Southampton")]:
    h = int((HG.district == key).sum()); l = int((L.district == key).sum())
    cities[nm] = dict(haunted=h, listed=l, per_1000=1000 * h / l if l else None, expected=tot_h * l / tot_l, ratio=h / (tot_h * l / tot_l) if l else None)
hl = int((HG.region == "London").sum()); ll = int((L.region == "London").sum())
cities["London"] = dict(haunted=hl, listed=ll, per_1000=1000 * hl / ll, expected=tot_h * ll / tot_l, ratio=hl / (tot_h * ll / tot_l))
R["cities"] = cities
R["edinburgh_share_of_scotland"] = cities["Edinburgh"]["haunted"] / R["countries"]["Scotland"]["haunted"]
R["york_places"] = HG[HG.district == "York"].name.tolist()
R["oxford_places"] = HG[HG.district == "Oxford"].name.tolist()
R["southampton_places"] = HG[HG.district == "City of Southampton"].name.tolist()
R["ireland"] = dict(republic=int((H.country == "Ireland").sum()), northern=int((H.country == "Northern Ireland").sum()))

# ---------- 6. the cast ----------
CASTK = ["grey_lady", "white_lady", "green_lady", "other_lady", "monk", "nun", "headless", "drummer", "dog", "soldier", "child", "poltergeist", "coach", "royal"]
GL = {"grey_lady": "Grey Lady", "white_lady": "White Lady", "green_lady": "Green Lady", "other_lady": "Brown, black, blue or red lady",
      "monk": "Monk, friar or abbot", "nun": "Nun", "headless": "Headless or beheaded", "drummer": "Drummer or piper", "dog": "Dog or hound", "soldier": "Soldier, knight or airman",
      "child": "Child", "poltergeist": "Poltergeist", "coach": "Phantom coach or horseman", "royal": "King, queen or famous figure"}
GT = H[H.ghost_text_chars > 0]
R["cast_n_texts"] = int(len(GT))
R["cast_labels"] = GL
R["cast"] = {g: int(GT["g_" + g].sum()) for g in CASTK}
R["cast_share"] = {g: float(GT["g_" + g].mean()) for g in CASTK}
R["coloured_lady_any"] = int(GT[["g_grey_lady", "g_white_lady", "g_green_lady", "g_other_lady"]].max(axis=1).sum())
R["n_any_named_type"] = int(GT[["g_" + g for g in CASTK]].max(axis=1).sum())
R["n_false_hits_removed"] = int(len(pd.read_csv(os.path.join(DATA, "ghost_false_hits.csv"))))
KG = {"castle": ["castle"], "house": ["house"], "inn": ["inn"], "church": ["church"], "other": ["theatre", "gaol", "military", "civic", "other_building"], "outside": ["road", "outdoor", "settlement"]}
KGL = {"castle": "Castles", "house": "Houses and palaces", "inn": "Inns and hotels", "church": "Churches and abbeys", "other": "Theatres, gaols, RAF and other buildings", "outside": "Roads, woods, hills and villages"}
mat = {}
for gk, ks in KG.items():
    sub = GT[GT.kind.isin(ks)]
    mat[gk] = dict(label=KGL[gk], n=int(len(sub)), **{g: int(sub["g_" + g].sum()) for g in CASTK})
R["cast_by_kind"] = mat
matc = {}
for c in ["England", "Scotland", "Wales", "Ireland"]:
    sub = GT[GT.country == c]
    matc[c] = dict(n=int(len(sub)), **{g: int(sub["g_" + g].sum()) for g in CASTK})
R["cast_by_country"] = matc
# religious ghosts at religious places
rel = GT.kind == "church"
mn = GT[["g_monk", "g_nun"]].max(axis=1)
R["monk_nun"] = dict(at_church=int(mn[rel].sum()), n_church=int(rel.sum()), elsewhere=int(mn[~rel].sum()), n_elsewhere=int((~rel).sum()),
                     share_church=float(mn[rel].mean()), share_elsewhere=float(mn[~rel].mean()),
                     p=float(stats.fisher_exact([[mn[rel].sum(), rel.sum() - mn[rel].sum()], [mn[~rel].sum(), (~rel).sum() - mn[~rel].sum()]])[1]),
                     places_elsewhere=GT[(~rel) & (mn == 1)].name.tolist())
mil = GT.kind == "military"
R["soldier_military"] = dict(at_military=int(GT[mil].g_soldier.sum()), n_military=int(mil.sum()), elsewhere=int(GT[~mil].g_soldier.sum()))
R["green_lady_places"] = GT[GT.g_green_lady == 1][["name", "country"]].values.tolist()
R["grey_lady_places"] = GT[GT.g_grey_lady == 1][["name", "country"]].values.tolist()
R["white_lady_places"] = GT[GT.g_white_lady == 1][["name", "country"]].values.tolist()
R["drummer_places"] = GT[GT.g_drummer == 1].name.tolist()
R["dog_places"] = GT[GT.g_dog == 1].name.tolist()
R["headless_places"] = GT[GT.g_headless == 1].name.tolist()
R["coach_places"] = GT[GT.g_coach == 1].name.tolist()

json.dump(R, open(os.path.join(DATA, "results.json"), "w"), indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))
pd.DataFrame([dict(kind=k, **{a: b for a, b in v.items()}) for k, v in mix.items()]).to_csv(os.path.join(DATA, "kind_mix.csv"), index=False)
pd.DataFrame([dict(region=k, **v) for k, v in reg.items()]).to_csv(os.path.join(DATA, "regions.csv"), index=False)
pd.DataFrame([dict(group=k, **v) for k, v in mat.items()]).to_csv(os.path.join(DATA, "cast_by_kind.csv"), index=False)
print(json.dumps({k: R[k] for k in ["n_places", "by_country", "n_haunted_gb_buildings", "listed_own", "listed_near", "inns_near_listed", "age_percentile",
                                    "age_percentile_wikidata_only", "countries", "scot_vs_eng_ratio", "castles_by_country", "cities", "cast", "monk_nun", "soldier_military"]}, indent=0, default=str)[:6000])
for k, v in mix.items(): print(k, v["haunted"], v["listed"], round(v["share_haunted"], 3), round(v["share_listed"], 3), round(v["ratio"], 2), round(v["p"], 4))
for k, v in age.items(): print(k, v)
for k, v in reg.items(): print(k, v["haunted"], v["listed"], round(v["per_1000"], 2), round(v["ratio"], 2), round(v["p_one_sided"], 4), v["haunted_castles"], v["wikidata_castles"])
for k, v in mat.items(): print(k, v)

# a few derived counts quoted in the text
R["green_scot_castle"] = int(((GT.g_green_lady == 1) & (GT.country == "Scotland") & (GT.kind == "castle")).sum())
R["headless_england"] = int(((GT.g_headless == 1) & (GT.country == "England")).sum())
R["monknun_england"] = int(((GT[["g_monk", "g_nun"]].max(axis=1) == 1) & (GT.country == "England")).sum())
R["monknun_scotland"] = int(((GT[["g_monk", "g_nun"]].max(axis=1) == 1) & (GT.country == "Scotland")).sum())
R["monknun_total"] = int((GT[["g_monk", "g_nun"]].max(axis=1) == 1).sum())
R["poltergeist_house"] = int(((GT.g_poltergeist == 1) & (GT.kind == "house")).sum())
R["lady_castle"] = int(((GT[["g_grey_lady", "g_white_lady", "g_green_lady", "g_other_lady"]].max(axis=1) == 1) & (GT.kind == "castle")).sum())
R["lady_inn"] = int(((GT[["g_grey_lady", "g_white_lady", "g_green_lady", "g_other_lady"]].max(axis=1) == 1) & (GT.kind == "inn")).sum())
R["n_inn_texts"] = int((GT.kind == "inn").sum())
R["n_castle_texts"] = int((GT.kind == "castle").sum())
R["scotland_share_haunted_gb"] = R["countries"]["Scotland"]["haunted"] / R["n_haunted_gb"]
R["scotland_share_listed"] = R["countries"]["Scotland"]["listed"] / R["n_listed_all"]
R["n_gb_buildings_church"] = R["mix"]["church"]["haunted"]
json.dump(R, open(os.path.join(DATA, "results.json"), "w"), indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print({k: R[k] for k in ["green_scot_castle", "headless_england", "monknun_england", "monknun_scotland", "monknun_total", "poltergeist_house", "lady_castle", "lady_inn", "n_inn_texts", "scotland_share_haunted_gb", "scotland_share_listed", "n_false_hits_removed"]})
