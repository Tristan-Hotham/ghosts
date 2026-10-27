"""Step 2. Give every haunted place a coordinate and record how it was placed.

Order of preference:
  1. the place's own Wikipedia article: its coordinates from the Wikipedia API (in the download), else a {{coord}} template
     or infobox latitude/longitude in the article text;
  2. a Wikidata item of the same name (Grade I, II* or Category A listed building, or a UK structure in the Wikidata bundle),
     a Wikidata church (Ireland), or a record in the Republic of Ireland Sites and Monuments Record, chosen by hand below;
  3. the town, village or natural feature that the source names, from OS Open Names (or a broader article's coordinates).
Every row keeps `geo_method`, `geo_source` and `geo_precision` (building, site, settlement, stretch).
Then: country (Natural Earth for the island of Ireland), and for Great Britain the region, county and district of the
nearest OS Open Names populated place.
Output: work/placed.json
"""
import json, os, re
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from pyproj import Transformer
from shapely.geometry import shape, Point
from common import *
from coords import coord_template, infobox_latlon

W = load_wiki(); A = W["articles"]
E = json.load(open(os.path.join(WORK, "entries.json")))["entries"]
B = load_bundle()
os_ = pd.read_csv(OSNAMES, sep="\t", usecols=["name1", "name2", "type", "local_type", "lat", "lon", "x", "y", "district", "county", "region", "country"],
                  dtype={"name1": str, "name2": str, "district": str, "county": str, "region": str, "country": str})

# Wikidata items by QID: listed buildings and the UK structures bundle
WD = {}
for r in tsv_rows(B["wd_listed_top"]):
    q = qid(r["x"]); la, lo = wkt(r["coord"])
    WD.setdefault(q, (la, lo, lit(r["xLabel"]), "Wikidata listed building " + q))
uk = json.load(open(os.path.join(D8, "uk_bundle_wikidata_osm.json")))
for r in tsv_rows(uk["wd_structures_tsv"]):
    q = qid(r["item"]); la, lo = wkt(r["coord"])
    WD.setdefault(q, (la, lo, lit(r["label"]), "Wikidata structure " + q))
CH_IE = {c["ch"]: c for c in json.load(open(os.path.join(HIST, "_data2", "wikidata", "ch_IE.json")))}

# Hand-chosen placements for places whose own article is not in the download or has no coordinates.
# kind: wd (Wikidata QID), smr (Ireland SMR entity), chie (Wikidata church, Ireland), os (OS Open Names name, filter), art (another article's coordinates), mid (midpoint of two OS names), none
GEO = {
    "Moresby Hall": ("wd", "Q13529101", "building"), "Chavenage House": ("wd", "Q5088488", "building"),
    "Woodchester Mansion": ("wd", "Q8032495", "building"), "Clitheroe Castle": ("wd", "Q5134437", "building"),
    "Tamworth Castle": ("wd", "Q7681908", "building"), "Tutbury Castle": ("wd", "Q7856912", "building"),
    "Souter Lighthouse": ("wd", "Q7565258", "building"), "Edinample Castle": ("wd", "Q5338115", "building"),
    "Pinkie House": ("wd", "Q7196201", "building"), "Aberglasney House": ("wd", "Q4667099", "building"),
    "Malmesbury Abbey": ("wd", "Q550064", "building"), "Longleat House": ("wd", "Q1726158", "building"),
    "Athelhampton Hall": ("wd", "Q19832956", "building"), "Hall Place": ("wd", "Q5642615", "building"),
    "British Museum": ("wd", "Q41778642", "building"), "Black Swan Hotel, Devizes": ("wd", "Q4921966", "building"),
    "National Justice Museum": ("wd", "Q17553836", "building"), "Ostrich Inn, Colnbrook": ("wd", "Q17551721", "building"),
    "Manor of Clifton": ("wd", "Q5133221", "building"), "Box Tunnel": ("wd", "Q99670929", "site"),
    "Major's Leap": ("wd", "Q8001111", "site"),
    "Malahide Castle": ("smr", "DU00499", "building"), "Charles Fort": ("smr", "CO15816", "building"),
    "Kinnitty Castle": ("smr", "OF01590", "building"), "St. Michan's Church": ("chie", "Q7590764", "building"),
    "Jamaica Inn": ("os", ("Bolventor", "Cornwall"), "settlement"), "Wellington Hotel, Boscastle": ("os", ("Boscastle", None), "settlement"),
    "Derby Gaol": ("os", ("Derby", "City of Derby"), "settlement"), "Old Grammar School, Derby": ("os", ("Derby", "City of Derby"), "settlement"),
    "George Inn, Derby": ("os", ("Derby", "City of Derby"), "settlement"), "The Old Bell Hotel, Derby": ("os", ("Derby", "City of Derby"), "settlement"),
    "Gresley Old Hall": ("os", ("Church Gresley", None), "settlement"), "Epping Forest": ("os", ("Epping Forest", None), "site"),
    "Kelvedon Hatch Secret Nuclear Bunker": ("os", ("Kelvedon Hatch", None), "settlement"), "Owd Betts": ("os", ("Norden", "Rochdale"), "settlement"),
    "Rufus Stone": ("os", ("Minstead", None), "settlement"), "Chatham Historic Dockyard": ("os", ("Chatham", None), "settlement"),
    "Bradley Woods": ("os", ("Bradley", "North East Lincolnshire"), "settlement"), "RAF Metheringham": ("os", ("Metheringham", None), "settlement"),
    "Aldwych tube station": ("os", ("Holborn", None), "settlement"), "284 Green Street, Enfield": ("os", ("Enfield", None), "settlement"),
    "Cock Lane": ("os", ("City of London", None), "settlement"), "Viaduct Tavern": ("os", ("Holborn", None), "settlement"),
    "Muckleburgh Collection": ("os", ("Weybourne", "North Norfolk"), "settlement"), "RAF Bircham Newton": ("os", ("Bircham Newton", None), "settlement"),
    "Guy's Cliffe": ("os", ("Warwick", "Warwickshire"), "settlement"), "Station Hotel, Dudley": ("os", ("Dudley", "Dudley"), "settlement"),
    "Avebury Henge": ("os", ("Avebury", None), "site"), "Devizes": ("os", ("Devizes", None), "settlement"), "Colchester": ("os", ("Colchester", None), "settlement"),
    "Dead Maids crossroads, Chapmanslade": ("os", ("Chapmanslade", None), "settlement"), "Red Lion, Avebury": ("os", ("Avebury", None), "settlement"),
    "Aldbourne": ("os", ("Aldbourne", None), "settlement"), "All Cannings": ("os", ("All Cannings", None), "settlement"),
    "Stocksbridge bypass": ("os", ("Stocksbridge", None), "stretch"), "Chirton Hall": ("os", ("North Shields", None), "settlement"),
    "Stockwell ghost": ("os", ("Stockwell", "Lambeth"), "settlement"), "A229 road": ("os", ("Blue Bell Hill", "Tonbridge and Malling"), "stretch"),
    "Hairy Hands": ("os", ("Postbridge", None), "stretch"), "A75 road": ("mid", ("Annan", "Dumfries"), "stretch"),
    "Golden Lion, St Ives": ("art", None, "settlement"), "Trigg's Barn": ("art", None, "settlement"), "All Saints' Church, Faringdon": ("art", None, "settlement"),
    "Bradbeers Department Store, Romsey": ("os", ("Romsey", None), "settlement"), "Groaning Tree of Baddesley": ("art", None, "settlement"),
    "Kitnocks Hill": ("art", None, "settlement"), "Chute Causeway": ("art", None, "settlement"),
    "Luibeilt Lodge": ("none", None, None), "Ross Castle": ("none", None, None), "Springhill House": ("none", None, None), "Caesar's Nightclub": ("none", None, None),
}
NOTES = {
    "Jamaica Inn": "Jamaica Inn stands at Bolventor on Bodmin Moor; placed at the OS hamlet.",
    "Wellington Hotel, Boscastle": "The list links the hotel to the Boscastle article; placed at the OS village.",
    "Major's Leap": "The title redirects to Wilderhope Manor; the leap is on Wenlock Edge by the manor. Placed at the manor (Wikidata).",
    "Kinnitty Castle": "SMR OF01590, 'Castle Bernard', the older name of Kinnitty Castle, Co. Offaly.",
    "Charles Fort": "SMR CO15816, bastioned fort marked 'Charles Fort' on the OS 6-inch map, Co. Cork.",
    "Malahide Castle": "SMR DU00499, tower house in Malahide Demesne marked 'Malahide Castle'.",
    "Manor of Clifton": "The article is about Clifton Hall, Nottingham; placed at Wikidata 'Clifton Hall, Nottingham'.",
    "A75 road": "The list names a fifteen-mile stretch between Annan and Dumfries; placed at the midpoint of the two OS towns.",
    "A229 road": "The road article places the phantom hitch-hiker at Blue Bell Hill; placed at the OS village.",
    "Hairy Hands": "The article sets the legend on the road near Postbridge, Dartmoor; placed at the OS hamlet.",
    "Stocksbridge bypass": "Redirects to A616 road; placed at Stocksbridge (OS town).",
    "Chirton Hall": "Chirton Hall stood in Chirton, North Shields (the article's category is North East England); placed at North Shields (OS).",
    "Guy's Cliffe": "The list calls it a manor house in the eponymous hamlet in Warwickshire; placed at Warwick (OS), the nearest OS town.",
    "Aldwych tube station": "Placed at Holborn (OS suburban area); the station is on the Strand nearby.",
    "Ross Castle": "Not placed: several Ross Castles exist and the list does not say which county; this one (Nugent, O'Reilly) is in Co. Westmeath but no record was found.",
    "Luibeilt Lodge": "Not placed: no OS Open Names or Wikidata record found.",
    "Springhill House": "Not placed: Northern Ireland is outside OS Open Names and the listed-building data.",
    "Caesar's Nightclub": "Not placed: the list gives no address and the linked article is not in the download.",
}

o_lookup = os_[os_.type.isin(["populatedPlace", "landcover", "landform", "other"])]


def os_find(name, filt):
    m = os_[(os_.name1 == name) | (os_.name2 == name)]
    if filt:
        m2 = m[(m.district == filt) | (m.county == filt)]
        if len(m2):
            m = m2
    if not len(m):
        return None
    pri = {"City": 0, "Town": 1, "Village": 2, "Suburban Area": 3, "Hamlet": 4}
    m = m.assign(p=m.local_type.map(pri).fillna(9)).sort_values("p")
    r = m.iloc[0]
    return float(r.lat), float(r.lon), f"OS Open Names: {name} ({r.local_type}, {r.county if isinstance(r.county, str) else r.district})"


smr = None
placed = []
for e in E:
    nm = e["name"]
    art = A.get(e["article"]) if e.get("article") else None
    res = None
    if nm in GEO:
        kind, key, prec = GEO[nm]
        if kind == "wd":
            la, lo, lab, src = WD[key]
            res = (la, lo, "Wikidata item of the same place", f"{src} ({lab})", prec, key)
        elif kind == "smr":
            if smr is None:
                smr = {r["ENTITY_ID"]: r for r in json.load(gzip.open(os.path.join(D10, "ireland_smr_all.json.gz")))}
            r = smr[key]
            res = (float(r["LATITUDE"]), float(r["LONGITUDE"]), "Sites and Monuments Record, Ireland", f"SMR {key}: {r['MONUMENT_CLASS']}, {r['TOWNLAND'].title()}, Co. {r['COUNTY'].title()}", prec, None)
        elif kind == "chie":
            c = CH_IE[key]; lo, la = [float(v) for v in re.findall(r"[-\d.]+", c["c"])]
            res = (la, lo, "Wikidata church of the same name", f"Wikidata {key} ({c['lab']})", prec, key)
        elif kind == "os":
            f = os_find(*key)
            res = (f[0], f[1], "Named town, village or feature", f[2], prec, None)
        elif kind == "mid":
            a, b = os_find(key[0], None), os_find(key[1], None)
            res = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, "Midpoint of the two places the list names", f"{a[2]}; {b[2]}", prec, None)
        elif kind == "art":
            c = art.get("coord")
            if c:
                res = (c["lat"], c["lon"], "Coordinates of the broader article the title redirects to", f"Wikipedia: {e['article']} (Wikipedia API)", prec, None)
            else:
                c = coord_template(art["text"])
                res = (c[0], c[1], "Coordinates of the broader article the title redirects to", f"Wikipedia: {e['article']} ({{{{coord}}}} in article text)", prec, None)
        else:
            res = (None, None, "Not placed", "", None, None)
    elif art and not e.get("broad") or (art and nm == e.get("article")):
        if art.get("coord"):
            res = (art["coord"]["lat"], art["coord"]["lon"], "Own Wikipedia article", f"Wikipedia: {e['article']} (Wikipedia API coordinates)", "building", None)
        else:
            c = coord_template(art["text"]) or infobox_latlon(art["text"])
            if c:
                res = (c[0], c[1], "Own Wikipedia article", f"Wikipedia: {e['article']} ({{{{coord}}}} in article text)" if "{{" in c[2] else f"Wikipedia: {e['article']} ({c[2]})", "building", None)
    if res is None:
        raise SystemExit(f"no placement rule for {nm!r} ({e.get('article')})")
    la, lo, meth, src, prec, wdq = res
    e.update(lat=None if la is None else round(la, 6), lon=None if lo is None else round(lo, 6), geo_method=meth, geo_source=src, geo_precision=prec,
             geo_note=NOTES.get(nm, ""), wd=(art.get("wd") if art and not e.get("broad") else None) or wdq)
    placed.append(e)

# precision of article-based places: villages, roads, woods and hills are 'site' or 'settlement' rather than 'building'
# (set later from the place type in step 3)

# Country: island of Ireland from Natural Earth; Great Britain from the nearest OS Open Names populated place
ne = json.load(open(os.path.join(NE, "ne_10m_admin_0_countries.geojson")))
IRL = [shape(f["geometry"]) for f in ne["features"] if f["properties"].get("ADM0_A3") == "IRL"][0]
tr = Transformer.from_crs(4326, 27700, always_xy=True)
pp = os_[os_.type == "populatedPlace"].reset_index(drop=True)
tree = cKDTree(np.c_[pp.x.astype(float), pp.y.astype(float)])
for e in placed:
    sec = " ".join(e["sections"])
    if e["lat"] is None:
        e["country"] = "Ireland" if "Ireland" in sec and "Northern" not in sec else ("Northern Ireland" if "Northern" in sec else ("Scotland" if "Scotland" in sec or "cat_scotland" in e["sources"] else "England"))
        e["region"] = {"Scotland": "Scotland", "Ireland": "Ireland", "Northern Ireland": "Northern Ireland"}.get(e["country"], "London" if "London" in sec else None)
        e["county"] = e["district"] = None
        continue
    if e["lon"] < -5.3 and e["lat"] < 55.45 and e["lat"] > 51.3:  # the island of Ireland
        e["country"] = "Ireland" if IRL.buffer(0.01).contains(Point(e["lon"], e["lat"])) else "Northern Ireland"
        e["region"] = e["country"]; e["county"] = e["district"] = None
        continue
    x, y = tr.transform(e["lon"], e["lat"])
    d, i = tree.query([x, y])
    r = pp.iloc[i]
    e["country"] = r.country; e["region"] = r.region
    e["county"] = r.county if isinstance(r.county, str) else None
    e["district"] = r.district if isinstance(r.district, str) else (r.county if isinstance(r.county, str) else None)
    e["nearest_os_place"] = r.name1
    e["x"], e["y"] = round(x), round(y)

json.dump(placed, open(os.path.join(WORK, "placed.json"), "w"), indent=1, ensure_ascii=False)
from collections import Counter
print(len(placed), Counter(e["geo_method"] for e in placed))
print(Counter(e["country"] for e in placed))
print(Counter(e["region"] for e in placed))
