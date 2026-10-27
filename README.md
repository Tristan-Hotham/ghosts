# Haunted, or Just Old?

Is a haunted place just an old place? This study takes the 260 reportedly haunted places in Britain and Ireland recorded by English Wikipedia (its categories and lists of "reportedly haunted locations"), places each on the map, sorts it by kind, dates it where possible and mines its text for the stock characters of ghost lore. It sets them against a baseline of old notable buildings: the 40,409 Grade I, Grade II* and Category A listed buildings in Wikidata, 37,982 OpenStreetMap pubs and the castles and tower houses in Wikidata.

Wikipedia's list is a record of stories told and written down, not of ghosts. Every pattern here is a pattern in the telling.

**Interactive version:** https://tristan-hotham.github.io/ghosts/

**Paper:** https://doi.org/10.5281/zenodo.23691866

**Blog post:** https://blog.tristanhotham.com/2026/10/27/ghosts/

By Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Companion studies: [The oldest buildings](https://tristan-hotham.github.io/oldest-buildings/), [Here Be Dragons](https://tristan-hotham.github.io/here-be-dragons/).

## Headline results

- The record: 260 places (146 in England, 85 in Scotland, 10 in Wales, 17 in Ireland, 2 in Northern Ireland); 256 placed, 188 at the building itself.
- Kind matters more than age. Among 199 haunted buildings in Great Britain, castles and towers are 34% (listed buildings: 3.7%; 9.0 times), inns, pubs and hotels 20% (2.4%; 8.5 times), churches, chapels and abbeys 4% (35%; 0.11 times).
- Only a little older: the median dated haunted building sits at the 45th percentile of dated listed buildings of the same kind (95% range 33 to 51; 83 buildings; sign test chance 0.272). Haunted houses are older than listed houses (median 1678 against 1757); haunted castles are not (1410 against 1350).
- Old inns: 60% of the 30 haunted inns placed at the building are within 50 m of a Grade I, II* or Category A listed building, against 7.1% of all 37,982 pubs in Great Britain.
- Scotland: 13.3 haunted places per 1,000 listed buildings against 4.6 in England and 3.9 in Wales; 71% of Scotland's haunted buildings are castles (England 10%). Haunted castles per 100 Wikidata castles: Scotland 5.3, England 1.2, Wales 0.0.
- Cities: Edinburgh 16 places (1.1 times what its listed buildings predict), York 2, London 18 (1.5 times); Oxford 5 and Southampton 4 stand out, probably from local editing.
- The cast (237 places with a ghost passage, 33 false matches removed by hand): White Lady 13, Grey Lady 8, Green Lady 7 (6 in Scottish castles), monk or abbot 12, nun 9, child 15, headless 6 (all English). Coloured ladies: 17 of 67 castles, 0 of 38 inns.

## Files

- `index.html`: the interactive page (Leaflet map, charts). Data are embedded.
- `header.png`: social card (1200 by 630).
- `data/haunted_places.csv`: one row per place: name, kind (and how it was decided), country, region, county, district, coordinates, how and from what it was placed (`geo_method`, `geo_source`, `geo_precision`, `geo_note`), Wikidata QID, listing grade if top-listed, year and its source, Wikipedia article and URL, source categories or lists, the ghost types found (`g_*` columns, 1 = mentioned) and the first sentence that makes it haunted.
- `data/ghost_false_hits.csv`: every automatic ghost-type match removed by hand, with the reason.
- `data/listed_baseline.csv.gz`: the 40,409 Grade I, II* and Category A listed items with kind, building flag, region and inception year.
- `data/kind_mix.csv`, `data/regions.csv`, `data/cast_by_kind.csv`: the main result tables.
- `data/results.json`: every number used on the page, in the paper, the blog post and the collage.
- `code/`: `01_collect.py`, `02_geocode.py`, `03_classify.py`, `04_baseline.py`, `05_analyse.py`, `06_build_site.py`, `07_header.py`, run in that order (with `common.py`, `coords.py`, `kinds.py`). `release/` holds the paper and blog figure scripts and `reddit/` the collage.

## Method in brief

Places: English Wikipedia categories "Reportedly haunted locations in" the United Kingdom, England, Scotland, Wales and Ireland (two levels), "List of reportedly haunted locations in the United Kingdom", "Reportedly haunted locations in Scotland", the Ireland section of "List of reportedly haunted locations" and the ghost sightings in "List of paranormal events reported in Wiltshire, England" (wikitext of 27 October 2026); 30 non-places removed. Coordinates from the article, a Wikidata item of the same building, the Sites and Monuments Record (Ireland), or the named town or feature in OS Open Names; 4 not placed. Kinds by rules on name and description, with recorded hand corrections. Dates: Wikidata inception (P571) or the first year in the infobox. Baseline: Wikidata items designated Grade I (Q15700818), Grade II* (Q15700831) or Category A (Q10729054) with coordinates; kinds from the Wikidata class label or name. Regions from the nearest OS Open Names populated place. Ghost types: regular expressions on the sentences around each ghost word, every match read by hand.

Caveats: this is Wikipedia's record, shaped by notability and by editors (a few cities are heavily edited); Northern Ireland and the Republic of Ireland have no baseline here; the baseline omits Grade II and Category B buildings; Wikidata dates a fifth of listed buildings and sometimes dates the present building; infobox dates are cruder; the ghost search was checked for false hits, not misses; small kinds have tiny counts.

## Rerun

Needs Python 3 with pandas, numpy, scipy, shapely 2 and pyproj (and playwright for the header). Place these one folder above this repository (or set `HIST`): `_data10/wikipedia_batch10.json.gz`, `_data10/wd_osm_bundle10.json.gz`, `_data10/ireland_smr_all.json.gz`, `_data8/uk_bundle_wikidata_osm.json`, `_data2/wikidata/ch_IE.json`, `osnames_gb.tsv` (OS Open Names extract), `_data3/ne/geojson/` (Natural Earth) and `oldest-buildings/data/buildings.csv`. Then run the scripts in `code/` in order.

## Sources and licence

- Haunted places and quoted sentences: English Wikipedia, CC BY-SA 4.0 (article links in `data/haunted_places.csv`).
- Listed buildings, castles, inception dates, Irish church: Wikidata, CC0.
- Pubs: © OpenStreetMap contributors, ODbL 1.0.
- Place names and regions: OS Open Names. Contains OS data © Crown copyright and database right 2026. Open Government Licence v3.0.
- Irish sites: Sites and Monuments Record, National Monuments Service, Department of Housing, Local Government and Heritage, CC BY 4.0.
- Land outline: Natural Earth, public domain. Base map tiles on the page: Esri. Map library: Leaflet.

The derived data (`data/`) and the text are released under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/); the pub distances derive from OpenStreetMap data under the ODbL. Code is MIT (see `LICENSE`).

## Citation

Hotham, T. (2026) *Haunted, or Just Old? Britain and Ireland's reportedly haunted places against its oldest notable buildings.* Data study and paper. Zenodo. https://doi.org/10.5281/zenodo.23691866

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
