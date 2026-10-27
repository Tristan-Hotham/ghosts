"""Step 3. For every haunted place: its kind, its ghosts (mined from the text) and its date.

Kind: the first matching rule in kinds.py on the place name, then on the Wikipedia short description and infobox type;
a handful of hand corrections below (each with a reason).
Ghosts: the article text (or, for an entry that only redirects to a broader article, the named section and the list entry
itself) is stripped of markup and split into sentences. Sentences that mention a ghost word (ghost, haunt, apparition,
spectre, phantom, spirit, poltergeist, wraith, paranormal, supernatural) are kept with the sentence either side. The ghost
types in GHOSTS are then searched for in that text. This is a count of what the written stories mention, not a census.
Date: the earliest of Wikidata inception (P571) for the place's own Wikidata item (from the listed-building and UK
structures bundles), the Oldest Buildings project's date for that item, or else the first year in the infobox fields
built / completed / construction / established / founded (with "Nth century" read as the middle of the century).
Output: data/haunted_places.csv and work/haunted.json
"""
import json, os, re, csv
import pandas as pd
from common import *
from kinds import kind_of, LABEL, BUILDING_KINDS

W = load_wiki(); A = W["articles"]
P = json.load(open(os.path.join(WORK, "placed.json")))
B = load_bundle()

KIND_FIX = {  # name: (kind, reason)
    "Althorp": ("house", "stately home"), "Longleat House": ("house", "stately home"), "Edinburgh Vaults": ("road", "underground chambers below a street (with Mary King's Close)"),
    "Mary King's Close": ("road", "underground street"), "Hellfire Caves": ("outdoor", "man-made caves"), "Chislehurst Caves": ("outdoor", "former mine caves"),
    "Jingling Geordie's Hole": ("outdoor", "cave"), "Kinnaird Head": ("castle", "the haunted part is the Wine Tower"),
    "Box Tunnel": ("road", "railway tunnel"), "Dead Maids crossroads, Chapmanslade": ("road", "crossroads"), "Stockwell ghost": ("house", "a house in Stockwell"),
    "284 Green Street, Enfield": ("house", "council house"), "50 Berkeley Square": ("house", "townhouse"), "Cock Lane": ("road", "the haunted house was in Cock Lane; the list names the street"),
    "Regent Terrace": ("road", "a street of houses"), "Trigg's Barn": ("other_building", "barn"), "Groaning Tree of Baddesley": ("outdoor", "a tree"),
    "Kitnocks Hill": ("outdoor", "hill"), "Major's Leap": ("outdoor", "cliff on Wenlock Edge"), "Jay's Grave": ("outdoor", "a roadside grave on Dartmoor"),
    "Rufus Stone": ("outdoor", "memorial stone in the New Forest"), "Avebury Henge": ("outdoor", "prehistoric henge"), "Durdham Down": ("outdoor", "open downland"),
    "Ben Macdui": ("outdoor", "mountain"), "Montpelier Hill": ("outdoor", "hill (with a ruined lodge)"), "Shard End Lake": ("outdoor", "lake"),
    "Bradley Woods": ("outdoor", "wood"), "Epping Forest": ("outdoor", "forest"), "Hairy Hands": ("road", "a stretch of road"),
    "Edge Hill, Warwickshire": ("outdoor", "escarpment and battlefield"), "Chute Causeway": ("road", "Roman road"), "Auchentiber": ("settlement", "hamlet"),
    "Kelvedon Hatch Secret Nuclear Bunker": ("military", "cold war bunker"), "Muckleburgh Collection": ("military", "military museum on a former army camp"),
    "RAF Montrose": ("military", "air station"), "Chatham Historic Dockyard": ("military", "naval dockyard"),
    "HM Prison Castle Huntly": ("gaol", "prison"), "National Justice Museum": ("gaol", "court and county gaol"), "The Tolbooth, Aberdeen": ("gaol", "tolbooth gaol"),
    "Leicester Guildhall": ("civic", "guildhall"), "Carnegie Hall, Dunfermline": ("theatre", "theatre"), "Hill House, Helensburgh": ("house", "house"),
    "Old Rectory, Epworth": ("house", "rectory"), "Borley Rectory": ("house", "rectory"), "Borley Church": ("church", "parish church"),
    "The Cloisters (Letchworth)": ("civic", "masonic centre, built as an open-air school"), "Ducker & Son": ("other_building", "shoe shop"),
    "Bradbeers Department Store, Romsey": ("other_building", "department store"), "Caesar's Nightclub": ("inn", "nightclub"),
    "Owd Betts": ("inn", "pub"), "Red Lion, Avebury": ("inn", "pub"), "Golden Lion, St Ives": ("inn", "pub"), "Lower Bell": ("inn", "pub"),
    "Craig House, Edinburgh": ("house", "house (later hospital)"), "Menacuddle": ("house", "house and holy well"), "Point of Ayr Lighthouse": ("other_building", "lighthouse"),
    "Souter Lighthouse": ("other_building", "lighthouse"), "Guy's Cliffe": ("house", "manor house"), "Wild Knight and the Black Lady": ("outdoor", ""),
    "Aldwych tube station": ("road", "tube station"), "Northam Bridge": ("road", "bridge"), "Abingdon Bridge": ("road", "bridge"),
    "Dead Man's Walk, Oxford": ("road", "footpath"), "New College Lane": ("road", "street"), "A75 road": ("road", "road"), "A229 road": ("road", "road"),
    "Stocksbridge bypass": ("road", "road"), "Duckett's Grove": ("house", "ruined house"), "Ballechin House": ("house", "house"),
    "Witches' Well": ("outdoor", ""), "Old Farmhouse, Southampton": ("inn", "the Old Farmhouse is a pub in Southampton"),
    "Crosbie Castle and the Fullarton estate": ("castle", "castle"), "Kinneil House": ("house", "house"), "Pinkie House": ("house", "house"),
    "Queensberry House": ("house", "house"), "Holyrood Palace": ("house", "palace"), "Linlithgow Palace": ("house", "palace"),
    "Eltham Palace": ("house", "palace"), "Beaulieu Palace House": ("house", "house"), "Tower of London": ("castle", "castle"),
    "Lennox Tower": ("castle", "tower house"), "Ackergill Tower": ("castle", "tower house"), "Charles Fort": ("castle", "bastioned fort"),
    "British Museum": ("civic", "museum"), "Montrose Air Station Museum": ("military", "air station"), "The Witchery": ("inn", "restaurant and hotel"),
    "Wymering Manor": ("house", "manor"), "Manor of Clifton": ("house", "manor house"), "Chirton Hall": ("house", "country house"),
    "Burford Priory": ("house", "a country house on the site of a priory"), "Treasurer's House, York": ("house", "house"),
    "Abbey House, Cambridge": ("house", "house"), "Glasshayes": ("house", "country house, later hotel"), "Craigdarroch": ("house", "house"),
    "Kinnitty Castle": ("castle", "castle"), "Loftus Hall": ("house", "country house"), "Red House (Youghal)": ("house", "house"),
    "St. Kevin's Church, Camden Row, Dublin": ("church", "church"), "Jamaica Inn": ("inn", "inn"), "Brookside Theatre": ("theatre", "theatre"),
    "Edinburgh Castle": ("castle", "castle"), "Bruce Castle": ("house", "a 16th-century manor house despite the name"), "Colchester": ("settlement", "the list calls the whole town haunted"), "Devizes": ("settlement", "the list calls the whole town haunted"),
    "Aldbourne": ("settlement", "village where a headless spirit was met on the road"), "All Cannings": ("house", "a cottage in the village"), "Stirling Castle": ("castle", "castle"), "Minsden Chapel": ("church", "ruined chapel"),
}

GHOST_WORDS = re.compile(r"\b(ghosts?|ghostly|haunt\w*|apparitions?|apparitional|spectr\w*|phantoms?|spirits?|poltergeists?|wraiths?|paranormal|supernatural|spook\w*|banshee)\b", re.I)
GHOSTS = {  # key: (label, pattern)
    "grey_lady": ("Grey Lady", r"\bgr[ae]y lad(?:y|ies)\b|\blady in gr[ae]y\b|\bwoman in gr[ae]y\b"),
    "white_lady": ("White Lady", r"\bwhite lad(?:y|ies)\b|\blady in white\b|\bwoman in white\b|\bwhite-clad\b"),
    "green_lady": ("Green Lady", r"\bgreen lad(?:y|ies)\b|\blady in green\b|\bwoman in green\b|\bgreen jean(?:ie)?\b"),
    "other_lady": ("Brown, black, blue or red lady", r"\b(?:brown|black|blue|pink|red) lad(?:y|ies)\b|\blady in (?:black|blue|pink|red|brown)\b"),
    "monk": ("Monk, friar or abbot", r"\bmonks?\b|\bfriars?\b|\babbots?\b|\bmonastic\b"),
    "nun": ("Nun", r"\bnuns?\b"),
    "headless": ("Headless or beheaded", r"\bheadless\b|\bwithout (?:a|his|her) head\b|\b(?:carrying|carries|holding) (?:his|her) (?:own )?head\b|\bdecapitated\b|\bbeheaded\b"),
    "drummer": ("Drummer or piper", r"\bdrummers?\b|\bdrumming\b|\bdrums?\b|\bpipers?\b|\bbagpipes?\b"),
    "dog": ("Black dog or phantom dog", r"\bdogs?\b|\bhounds?\b|\bhellhounds?\b|\bbarghest\b|\bshuck\b"),
    "soldier": ("Soldier, knight or airman", r"\bsoldiers?\b|\bcavaliers?\b|\broundheads?\b|\bredcoats?\b|\blegionar\w+\b|\btroops?\b|\bin armou?r\b|\bairm[ae]n\b|\bpilots?\b|\baircrew\b|\bhighlanders?\b|\bjacobites?\b|\bknights?\b|\bguardsm[ae]n\b"),
    "child": ("Child", r"\bchild(?:ren)?\b|\b(?:little|young|small) (?:boy|girl)s?\b|\bboys?\b|\bgirls?\b|\bbab(?:y|ies)\b|\binfants?\b"),
    "poltergeist": ("Poltergeist", r"\bpoltergeists?\b"),
    "coach": ("Phantom coach or horseman", r"\bcoach(?:es)? and (?:horses|four)\b|\b(?:phantom|ghostly|spectral) (?:coach|carriage|horse(?:man|men)?|rider)s?\b|\bhorsem[ae]n\b|\bheadless horse"),
    "royal": ("King, queen or famous figure", r"\banne boleyn\b|\bmary,? queen of scots\b|\bking charles\b|\bcharles i\b|\bhenry viii\b|\bqueen (?:anne|elizabeth|mary|catherine)\b|\bking (?:james|henry|richard|edward|william)\b|\bwilliam wallace\b|\bdick turpin\b|\bcromwell\b"),
}
# Every automatic match was read in context; these were false hits (the word is in the text but not about a ghost of that kind).
GHOST_FIX = {
    ("Linlithgow Palace", "drummer"): "a bagpipe tune named after the palace", ("Jay's Grave", "dog"): "the place name Hound Tor",
    ("Ardrossan Castle", "soldier"): "Cromwell's soldiers demolished it", ("Fyvie Castle", "soldier"): "a singer named Knight",
    ("Charleville Castle", "soldier"): "film titles", ("Bramshill House", "headless"): "a husband beheaded; the ghost is the Grey Lady",
    ("Preston Manor, Brighton", "monk"): "nuns excommunicated by a friar", ("Wymering Manor", "monk"): "monks in a story about the room; the ghost is a nun",
    ("Lumley Castle", "nun"): "Lily of Lumley was said to have become a nun; the ghost is Lily", ("Burford Priory", "nun"): "nuns lived there later",
    ("Loftus Hall", "nun"): "orders of nuns owned the house", ("Belgrave Hall", "royal"): "Queen Anne style", ("Bramshill House", "royal"): "Queen Anne-style dress",
    ("Craigdarroch", "royal"): "King William in the family history", ("Barnbougle Castle", "royal"): "the antiquary William Wallace Fyfe",
    ("Malahide Castle", "royal"): "Henry VIII detained a lady there", ("Stirling Castle", "royal"): "Queen Mary in the Green Lady story",
    ("The Flask, Highgate", "royal"): "Dick Turpin is said to have hidden there, not to haunt it",
    ("Old Rectory, Epworth", "child"): "the family's children", ("Abbey House, Cambridge", "child"): "children of a family living there",
    ("Borley Rectory", "child"): "the rector's children", ("Littleport", "child"): "a girl rescued in the legend; the ghost is the black dog",
    ("Beaulieu Abbey", "child"): "local boys as witnesses", ("Burford", "child"): "a novel for children", ("Preston Manor, Brighton", "child"): "a family's children",
    ("Fyvie Castle", "child"): "a children's game show", ("Tulloch Castle", "child"): "a boy took a photograph", ("Queensberry House", "child"): "a boy sent away; not a ghost",
    ("Royal Lyceum Theatre", "child"): "a play title", ("Plas Teg", "child"): "the band Girls Aloud", ("Montpelier Hill", "child"): "a skeleton found",
    ("Hampton Court Palace", "child"): "a royal birth", ("Berry Pomeroy Castle", "child"): "the White Lady's murdered baby; the ghost is the mother",
}

CAST = ["grey_lady", "white_lady", "green_lady", "other_lady", "monk", "nun", "headless", "drummer", "dog", "soldier", "child", "poltergeist", "coach", "royal"]

LINK = re.compile(r"\[\[([^\]|]*)(?:\|([^\]]*))?\]\]")


def plain(t):
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    t = re.sub(r"<ref[^>]*/>", "", t)
    t = re.sub(r"<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    for _ in range(4):
        t = re.sub(r"\{\{[^{}]*\}\}", " ", t)
    t = re.sub(r"\[\[(?:File|Image|Category):[^\]]*(?:\[\[[^\]]*\]\][^\]]*)*\]\]", " ", t)
    t = LINK.sub(lambda m: m.group(2) or m.group(1), t)
    t = re.sub(r"\[https?://\S+\s*([^\]]*)\]", r"\1", t)
    t = re.sub(r"'{2,}", "", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\{\|.*?\|\}", " ", t, flags=re.S)
    return t


def section(t, anchor):
    m = re.search(r"^(=+)\s*" + re.escape(anchor) + r"\s*=+\s*$", t, re.M | re.I)
    if not m:
        return ""
    lvl = len(m.group(1))
    rest = t[m.end():]
    n = re.search(r"^={2,%d}[^=].*=+\s*$" % lvl, rest, re.M)
    return rest[: n.start()] if n else rest


def ghost_text(e):
    parts = list(e.get("list_text") or [])
    art = A.get(e["article"]) if e.get("article") else None
    if art and art.get("text"):
        t = art["text"]
        t = re.split(r"\n==\s*(?:References|Notes|Further reading|External links|See also|Sources|Bibliography)\s*==", t)[0]
        if e.get("broad") and e["name"] != e["article"]:
            sec = section(t, e["anchor"]) if e.get("anchor") else ""
            if sec:
                parts.append(plain(sec))
            else:  # sentences that name the place
                key = re.sub(r",.*$", "", e["name"]).replace("The ", "")
                parts += [s for s in re.split(r"(?<=[.!?])\s+", plain(t)) if key.lower() in s.lower()]
        else:
            parts.append(plain(t))
    sents = []
    for p in parts:
        for para in p.split("\n"):
            sents += [s.strip() for s in re.split(r"(?<=[.!?])\s+", para) if s.strip()]
    keep = set()
    for i, s in enumerate(sents):
        if GHOST_WORDS.search(s):
            keep.update([i - 1, i, i + 1])
    lt = " ".join(e.get("list_text") or [])
    body = " ".join(sents[i] for i in sorted(keep) if 0 <= i < len(sents) and sents[i] not in lt)
    return (lt + " " + body).strip(), len(sents)


# ---- dates ----
INC = {}
for r in tsv_rows(B["wd_listed_top"]):
    y = year(r["inception"])
    if y is not None:
        q = qid(r["x"]); INC[q] = min(INC.get(q, 9999), y)
uk = json.load(open(os.path.join(D8, "uk_bundle_wikidata_osm.json")))
for r in tsv_rows(uk["wd_structures_tsv"]):
    y = year(r["inception"])
    if y is not None:
        q = qid(r["item"]); INC[q] = min(INC.get(q, 9999), y)
OB = pd.read_csv(OLDEST, usecols=["qid", "year"]).dropna()
OBY = dict(zip(OB.qid, OB.year.astype(int)))
LISTED = {qid(r["x"]): r for r in tsv_rows(B["wd_listed_top"])}
DES = {"Q15700818": "Grade I", "Q15700831": "Grade II*", "Q10729054": "Category A"}


def infobox(t):
    m = re.search(r"\{\{\s*Infobox", t or "", re.I)
    if not m:
        return ""
    depth, i = 0, m.start()
    while i < len(t):
        if t.startswith("{{", i):
            depth += 1; i += 2; continue
        if t.startswith("}}", i):
            depth -= 1; i += 2
            if depth == 0:
                return t[m.start():i]
            continue
        i += 1
    return t[m.start():]


def ib_year(t):
    ib = infobox(t)
    for f in ["built", "year_built", "completed", "construction_start_date", "construction", "built_date", "established", "founded", "date_built"]:
        m = re.search(r"\|\s*" + f + r"\s*=\s*([^\n|]*(?:\{\{[^}]*\}\}[^\n|]*)?)", ib, re.I)
        if not m:
            continue
        v = re.sub(r"<ref.*", "", m.group(1))
        c = re.search(r"(\d{1,2})(?:st|nd|rd|th)[ -]century", v, re.I)
        y = re.search(r"(?<!\d)(\d{3,4})(?!\d)", v)
        cands = []
        if y and 400 <= int(y.group(1)) <= 2026:
            cands.append((int(y.group(1)), f"infobox '{f}': {v.strip()[:60]}"))
        if c:
            n = int(c.group(1)); cands.append(((n - 1) * 100 + 50, f"infobox '{f}': {v.strip()[:60]} (middle of century)"))
        if cands:
            cands.sort(key=lambda z: v.find(str(z[0])) if str(z[0]) in v else v.lower().find("century"))
            return cands[0]
    return None


STRICT = re.compile(r"\b(ghosts?|ghostly|haunted|hauntings?|haunts (?:the|its)|apparitions?|spectres?|spectral|phantoms?|poltergeists?|wraiths?|banshee|spirits? of)\b", re.I)


def first_ghost_sentence(gt):
    for s_ in re.split(r"(?<=[.!?])\s+", gt):
        if "==" in s_:
            s_ = re.sub(r"^.*==\s*", "", s_)
        if STRICT.search(s_) and len(s_) > 25 and not s_.rstrip().endswith('"...'):
            s_ = re.sub(r"\s+", " ", s_).strip()
            return s_ if len(s_) <= 240 else s_[:237].rsplit(" ", 1)[0] + "..."
    return ""


rows = []
for e in P:
    art = A.get(e["article"]) if e.get("article") else None
    own = art if (art and (not e.get("broad") or e["name"] == e["article"])) else None
    txt = own["text"] if own else ""
    sd = re.search(r"\{\{\s*[Ss]hort description\|([^}]*)\}\}", txt)
    ib = re.search(r"\{\{\s*[Ii]nfobox ([^\n|}]*)", txt)
    desc = " ".join(x for x in [sd.group(1) if sd else "", ib.group(1) if ib else ""] if x)
    if e["name"] in KIND_FIX:
        k, why = KIND_FIX[e["name"]]; how = "by hand: " + why if why else "by hand"
    else:
        k = kind_of(e["name"], desc); how = "rule"
    if k is None:
        raise SystemExit(f"no kind for {e['name']} / {desc}")
    gt, nsent = ghost_text(e)
    low = gt.lower()
    g = {c: int(bool(re.search(GHOSTS[c][1], low)) and (e["name"], c) not in GHOST_FIX) for c in GHOSTS}
    # date
    q = e.get("wd")
    dy, dsrc = None, ""
    if q and q in INC:
        dy, dsrc = INC[q], f"Wikidata inception (P571) of {q}"
    if q and q in OBY and (dy is None or OBY[q] < dy):
        dy, dsrc = OBY[q], f"Oldest Buildings project date for {q}"
    if dy is None and own:
        r = ib_year(txt)
        if r:
            dy, dsrc = r[0], "Wikipedia " + r[1]
    if dy is not None and dy > 2026:
        dy, dsrc = None, ""
    lst = LISTED.get(q)
    prec = e["geo_precision"]
    if prec == "building" and k in ("settlement",):
        prec = "settlement"
    elif prec == "building" and k in ("road", "outdoor"):
        prec = "site"
    rows.append(dict(
        name=e["name"], kind=k, kind_label=LABEL[k], kind_basis=how, is_building=int(k in BUILDING_KINDS),
        country=e["country"], region=e["region"], county=e.get("county"), district=e.get("district"),
        lat=e["lat"], lon=e["lon"], geo_method=e["geo_method"], geo_source=e["geo_source"], geo_precision=prec, geo_note=e.get("geo_note", ""),
        wikidata=q or "", listed=DES.get(qid(lst["des"]), "") if lst else "",
        year=dy, year_source=dsrc, article=e.get("article") or "",
        wikipedia_url=("https://en.wikipedia.org/wiki/" + e["article"].replace(" ", "_")) if e.get("article") else "",
        sources="|".join(e["sources"]), list_section=" / ".join(s for s in e["sections"] if s),
        description=desc, ghost_text_chars=len(gt), **{"g_" + c: g[c] for c in GHOSTS},
        ghost_sentence=first_ghost_sentence(gt),
    ))

df = pd.DataFrame(rows)
used = {k for k in GHOST_FIX if k[0] in set(df.name)}
assert used == set(GHOST_FIX), set(GHOST_FIX) - used
pd.DataFrame([dict(place=a, ghost_type=b, reason=r) for (a, b), r in GHOST_FIX.items()]).to_csv(os.path.join(DATA, "ghost_false_hits.csv"), index=False)
df.to_csv(os.path.join(DATA, "haunted_places.csv"), index=False, quoting=csv.QUOTE_MINIMAL)
json.dump(rows, open(os.path.join(WORK, "haunted.json"), "w"), ensure_ascii=False)
print(len(df), "places")
print(df.kind.value_counts().to_string())
print("dated", df.year.notna().sum(), df.year_source.str.slice(0, 18).value_counts().to_string())
print("listed", df.listed.value_counts().to_string())
print({c: int(df["g_" + c].sum()) for c in GHOSTS})
print("no ghost text", (df.ghost_text_chars == 0).sum(), df[df.ghost_text_chars == 0].name.tolist())
