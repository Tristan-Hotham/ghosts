"""Parse coordinates from Wikipedia wikitext ({{coord}} templates and infobox latitude/longitude fields)."""
import re

NUM = r"[-+]?\d+(?:\.\d+)?"


def _dms(parts):
    """parts: list of tokens up to and including N/S then E/W."""
    vals, out = [], []
    for p in parts:
        p = p.strip()
        if p.upper() in ("N", "S", "E", "W"):
            v = 0.0
            for i, x in enumerate(vals):
                v += float(x) / (60 ** i)
            if p.upper() in ("S", "W"):
                v = -v
            out.append(v)
            vals = []
            if len(out) == 2:
                break
        elif re.fullmatch(NUM, p):
            vals.append(p)
        elif p == "":
            continue
        else:
            return None
    return tuple(out) if len(out) == 2 else None


def coord_template(text):
    """Return (lat, lon, raw) for the best {{coord}} in text: one with display=title first, else the first one."""
    cands = []
    for m in re.finditer(r"\{\{\s*[Cc]oord\s*\|([^{}]*)\}\}", text or ""):
        raw = m.group(1)
        parts = [p.strip() for p in raw.split("|")]
        pos = [p for p in parts if "=" not in p]
        title = "title" in raw
        res = None
        if any(p.upper() in ("N", "S") for p in pos):
            res = _dms(pos)
        elif len(pos) >= 2 and re.fullmatch(NUM, pos[0]) and re.fullmatch(NUM, pos[1]):
            res = (float(pos[0]), float(pos[1]))
        if res and 49 < res[0] < 61.5 and -11 < res[1] < 2.5:
            cands.append((0 if title else 1, m.start(), res, m.group(0)))
    if not cands:
        return None
    cands.sort()
    c = cands[0]
    return c[2][0], c[2][1], c[3]


def infobox_latlon(text):
    t = text or ""
    m1 = re.search(r"\|\s*latitude\s*=\s*(" + NUM + r")", t)
    m2 = re.search(r"\|\s*longitude\s*=\s*(" + NUM + r")", t)
    if m1 and m2:
        la, lo = float(m1.group(1)), float(m2.group(1))
        if 49 < la < 61.5 and -11 < lo < 2.5:
            return la, lo, "infobox latitude/longitude"
    return None
