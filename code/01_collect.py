"""Step 1. Collect every reportedly haunted place in Britain and Ireland from English Wikipedia.

Sources (wikitext retrieved 27 Oct 2026, CC BY-SA 4.0):
  * members of the categories "Reportedly haunted locations in the United Kingdom / England / Scotland / Wales / Ireland"
    (walked two levels deep by the downloader, so some non-places such as regalia and regiments come along; removed below);
  * bullet entries of "List of reportedly haunted locations in the United Kingdom" (with the county or country heading);
  * bullet entries of "Reportedly haunted locations in Scotland";
  * the Ireland section of "List of reportedly haunted locations";
  * the "Ghost sightings" table of "List of paranormal events reported in Wiltshire, England".
Output: work/entries.json (one record per place, before geocoding and classification).
Run: python3 code/01_collect.py
"""
import re, json, os
from common import load_wiki, WORK

W = load_wiki()
A = W["articles"]
REQ = {v["requested"]: k for k, v in A.items() if v.get("requested")}

# Titles reached by the two-level category walk that are not places (people, objects, units, events, lists, networks).
NOT_PLACE = {
    "1950 removal of the Stone of Scone": "event", "52nd Infantry Brigade (United Kingdom)": "military unit",
    "Burning of Edinburgh": "event", "Crown of Scotland": "object", "Eidyn": "historic region",
    "Honours of Scotland": "object", "James Home of Coldenknowes": "person", "James Kirkcaldy": "person",
    "Jewels of James III of Scotland": "object", "Jewels of James V": "object", "Jewels of Mary, Queen of Scots": "object",
    "List of governors of Edinburgh Castle": "list", "List of paranormal events reported in Wiltshire, England": "list (its entries are used)",
    "List of reportedly haunted locations in the United Kingdom": "list (its entries are used)",
    "Reportedly haunted locations in Scotland": "list (its entries are used)", "Mons Meg": "object",
    "Richard Clement Moody": "person", "Royal Edinburgh Military Tattoo": "event", "Royal Regiment of Scotland": "military unit",
    "Royal Scots Dragoon Guards": "military unit", "Sceptre of Scotland": "object", "Thomas McKay (gunner)": "person",
    "Wardrobe of Mary, Queen of Scots": "object", "William Kirkcaldy of Grange": "person",
    "Wild Knight and the Black Lady": "event (1507 tournament)", "London Underground": "network, not a single place",
    "National War Museum": "in Edinburgh Castle category only, no haunting in text",
    "Scottish National War Memorial": "in Edinburgh Castle category only, no haunting in text",
    "St Margaret's Chapel, Edinburgh": "in Edinburgh Castle category only, no haunting in text",
    "Witches' Well": "in Edinburgh Castle category only, no haunting in text",
    "Edinburgh": "city, listed only as the whole Old Town", "Epping Forest": "kept",
}
NOT_PLACE.pop("Epping Forest")

LINK = re.compile(r"\[\[([^\]|#]*)(#[^\]|]*)?(?:\|([^\]]*))?\]\]")


def strip_markup(s):
    s = re.sub(r"<ref.*$", "", s) if "</ref>" not in s and "<ref" in s and "/>" not in s[s.find("<ref"):] else s
    s = re.sub(r"<ref[^>]*/>", "", s)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = LINK.sub(lambda m: m.group(3) or m.group(1), s)
    s = re.sub(r"'''?", "", s)
    return re.sub(r"\s+", " ", s).strip()


def resolve(t):
    t = (t or "").strip().replace("_", " ")
    if not t:
        return None
    t = t[0].upper() + t[1:]
    if t in A:
        return t
    return REQ.get(t)


entries = {}
# The same place under two names (list link text against category title); merged under the second name.
ALIAS = {"Ducketts Grove": "Duckett's Grove", "The Witchery by the Castle": "The Witchery", "The Edinburgh Vaults": "Edinburgh Vaults",
         "The Tolbooth": "The Tolbooth, Aberdeen", "The Skirrid Mountain Inn": "The Skirrid Inn", "Metheringham Lass": "RAF Metheringham",
         "Fred Batt": "Caesar's Nightclub", "Enfield Poltergeist": "284 Green Street, Enfield", "Cock Lane ghost": "Cock Lane",
         "Kinnaird Wine Tower": "Kinnaird Head", "Montrose Air Station Museum": "RAF Montrose", "Glasshayes House": "Glasshayes",
         "Charles Fort (Ireland)": "Charles Fort", "Springhill House": "Springhill House", "The George Inn": "George Inn, Derby",
         "The Wellington Hotel": "Wellington Hotel, Boscastle", "Station Hotel, Dudley": "Station Hotel, Dudley",
         "Llancaiach Fawr Mannor": "Llancaiach Fawr", "Stockwell ghost": "Stockwell ghost"}


def add(key, **kw):
    key = ALIAS.get(key, key)
    e = entries.setdefault(key, {"name": key, "sources": [], "sections": [], "article": None, "anchor": None, "list_text": [], "broad": False})
    for s in kw.pop("sources", []):
        if s not in e["sources"]:
            e["sources"].append(s)
    for s in kw.pop("sections", []):
        if s and s not in e["sections"]:
            e["sections"].append(s)
    lt = kw.pop("list_text", None)
    if lt:
        e["list_text"].append(lt)
    for k, v in kw.items():
        if v is not None and not e.get(k):
            e[k] = v


# 1. categories
CATS = {"Category:Reportedly haunted locations in the United Kingdom": "cat_uk", "Category:Reportedly haunted locations in England": "cat_england",
        "Category:Reportedly haunted locations in Scotland": "cat_scotland", "Category:Reportedly haunted locations in Wales": "cat_wales",
        "Category:Reportedly haunted locations in Ireland": "cat_ireland"}
excluded = []
for c, tag in CATS.items():
    for t in W["categories"][c]:
        if t in NOT_PLACE:
            excluded.append((t, NOT_PLACE[t]))
            continue
        r = resolve(t)
        broad = bool(r and r != t)  # a redirect to a broader article (a town, a person, a road)
        add(t, sources=[tag], article=r, broad=broad)


def bullets(text, src, default_section=None):
    sec = default_section
    sub = None
    for line in text.split("\n"):
        h = re.match(r"^(=+)\s*(.+?)\s*=+\s*$", line)
        if h:
            name = strip_markup(h.group(2))
            if len(h.group(1)) == 2:
                sec, sub = name, None
            else:
                sub = name
            continue
        if not line.lstrip().startswith("*"):
            continue
        body = line.lstrip("* ").strip()
        m = LINK.search(body)
        raw = strip_markup(body)
        if not raw:
            continue
        if m and body.find(m.group(0)) < 25 and not body.startswith("A fifteen") and not body.startswith("In [["):
            target, anchor, disp = m.group(1), m.group(2), m.group(3)
            if body.startswith("In [[") or "Borley Rector" in body:
                pass
            r = resolve(target)
            disp_name = strip_markup(disp) if disp else target
            if anchor or (r and r != target.replace("_", " ")):
                key = disp_name
                add(key, sources=[src], sections=[sec, sub], article=r, anchor=(anchor or "")[1:].replace("_", " ") or None, broad=True, list_text=raw)
            else:
                key = r or target
                add(key, sources=[src], sections=[sec, sub], article=r, list_text=raw)
        else:
            yield_special(body, raw, src, sec, sub)


def yield_special(body, raw, src, sec, sub):
    if body.startswith("A fifteen"):
        add("A75 road", sources=[src], sections=[sec, sub], article=resolve("A75 road"), list_text=raw)
    elif body.startswith("In [["):
        ms = LINK.findall(body)
        tgt = ms[1][0]
        add(resolve(tgt) or tgt, sources=[src], sections=[sec, sub], article=resolve(tgt), list_text=raw)
    else:
        nm = raw.split(",")[0].split(" in the village")[0].strip()
        nm = {"Borley Rector": "Borley Rectory"}.get(nm, nm)
        r = resolve(nm)
        add(r or nm, sources=[src], sections=[sec, sub], article=r, list_text=raw)


# 2. the UK list
t = A["List of reportedly haunted locations in the United Kingdom"]["text"]
t = t[:t.find("==See also")]
bullets(t, "list_uk")
# 3. Scotland list
t = A["Reportedly haunted locations in Scotland"]["text"]
t = t[:t.find("==See also")] if "==See also" in t else t[:t.find("==References")]
bullets(t.replace("==List==", ""), "list_scotland", "Scotland")
# 4. Ireland section of the world list
t = A["List of reportedly haunted locations"]["text"]
i = t.find("==Ireland==")
j = t.find("\n==", i + 5)
bullets(t[i:j], "list_world_ireland", "Ireland")
# 5. Wiltshire table, ghost section only
t = A["List of paranormal events reported in Wiltshire, England"]["text"]
i = t.find("== Ghost sightings")
j = t.find("\n==", i + 5)
for r in t[i:j].split("|-")[1:]:
    cells = [c.strip() for c in r.strip().split("\n|")]
    if len(cells) < 3:
        continue
    loc, desc = cells[1], strip_markup(cells[2])
    if "/Red Lion" in loc:
        add("Red Lion, Avebury", sources=["list_wiltshire"], sections=["Wiltshire"], article=None, broad=True, list_text=desc, settlement="Avebury")
        continue
    m = LINK.search(loc)
    target, disp = m.group(1), m.group(3)
    nm = strip_markup(disp) if disp else target
    if nm == "Chapmanslade":
        nm = "Dead Maids crossroads, Chapmanslade"
    add(nm, sources=["list_wiltshire"], sections=["Wiltshire"], article=resolve(target), list_text=desc, settlement=target if nm != target else None)

# drop whole-town or non-place list entries
for k in list(entries):
    if k in NOT_PLACE:
        excluded.append((k, NOT_PLACE[k]))
        del entries[k]

out = {"entries": list(entries.values()), "excluded": sorted(set(excluded))}
json.dump(out, open(os.path.join(WORK, "entries.json"), "w"), indent=1, ensure_ascii=False)
print(len(entries), "entries;", len(set(excluded)), "excluded")
from collections import Counter
print(Counter(s for e in entries.values() for s in e["sources"]))
for e in entries.values():
    if not e["article"] or e["broad"]:
        print("  ", e["name"], "|", e["article"], "|", e.get("anchor"), "|", e["sections"], "|", e["list_text"][:1])
