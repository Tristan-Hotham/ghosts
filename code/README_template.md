# Haunted, or Just Old?

Is a haunted place just an old place? This study takes the {{n_places|int}} reportedly haunted places in Britain and Ireland recorded by English Wikipedia (its categories and lists of "reportedly haunted locations"), places each on the map, sorts it by kind, dates it where possible and mines its text for the stock characters of ghost lore. It sets them against a baseline of old notable buildings: the {{n_listed_all|int}} Grade I, Grade II* and Category A listed buildings in Wikidata, {{inns_near_listed.n_pubs|int}} OpenStreetMap pubs and the castles and tower houses in Wikidata.

Wikipedia's list is a record of stories told and written down, not of ghosts. Every pattern here is a pattern in the telling.

**Interactive version:** https://tristan-hotham.github.io/ghosts/

**Paper:** https://doi.org/10.5281/zenodo.23691866

**Blog post:** https://blog.tristanhotham.com/2026/10/27/ghosts/

By Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Companion studies: [The oldest buildings](https://tristan-hotham.github.io/oldest-buildings/), [Here Be Dragons](https://tristan-hotham.github.io/here-be-dragons/).

## Headline results

- The record: {{n_places|int}} places ({{by_country.England|int}} in England, {{by_country.Scotland|int}} in Scotland, {{by_country.Wales|int}} in Wales, {{by_country.Ireland|int}} in Ireland, {{by_country.Northern Ireland|int}} in Northern Ireland); {{n_placed|int}} placed, {{geo_precision.building|int}} at the building itself.
- Kind matters more than age. Among {{n_haunted_gb_buildings|int}} haunted buildings in Great Britain, castles and towers are {{mix.castle.share_haunted|pct0}} (listed buildings: {{mix.castle.share_listed|pct1}}; {{mix.castle.ratio|f1}} times), inns, pubs and hotels {{mix.inn.share_haunted|pct0}} ({{mix.inn.share_listed|pct1}}; {{mix.inn.ratio|f1}} times), churches, chapels and abbeys {{mix.church.share_haunted|pct0}} ({{mix.church.share_listed|pct0}}; {{mix.church.ratio|f2}} times).
- Only a little older: the median dated haunted building sits at the {{age_percentile.median|per100}}th percentile of dated listed buildings of the same kind (95% range {{age_percentile.lo|per100}} to {{age_percentile.hi|per100}}; {{age_percentile.n|int}} buildings; sign test chance {{age_percentile.p_sign|p}}). Haunted houses are older than listed houses (median {{age.house.median_haunted|yr}} against {{age.house.median_listed|yr}}); haunted castles are not ({{age.castle.median_haunted|yr}} against {{age.castle.median_listed|yr}}).
- Old inns: {{inns_near_listed.share|pct0}} of the {{inns_near_listed.n|int}} haunted inns placed at the building are within 50 m of a Grade I, II* or Category A listed building, against {{inns_near_listed.pubs_share|pct1}} of all {{inns_near_listed.n_pubs|int}} pubs in Great Britain.
- Scotland: {{countries.Scotland.per_1000|f1}} haunted places per 1,000 listed buildings against {{countries.England.per_1000|f1}} in England and {{countries.Wales.per_1000|f1}} in Wales; {{castle_share_scotland|pct0}} of Scotland's haunted buildings are castles (England {{castle_share_england|pct0}}). Haunted castles per 100 Wikidata castles: Scotland {{castles_by_country.Scotland.per_100|f1}}, England {{castles_by_country.England.per_100|f1}}, Wales {{castles_by_country.Wales.per_100|f1}}.
- Cities: Edinburgh {{cities.Edinburgh.haunted|int}} places ({{cities.Edinburgh.ratio|f1}} times what its listed buildings predict), York {{cities.York.haunted|int}}, London {{cities.London.haunted|int}} ({{cities.London.ratio|f1}} times); Oxford {{cities.Oxford.haunted|int}} and Southampton {{cities.City of Southampton.haunted|int}} stand out, probably from local editing.
- The cast ({{cast_n_texts|int}} places with a ghost passage, {{n_false_hits_removed|int}} false matches removed by hand): White Lady {{cast.white_lady|int}}, Grey Lady {{cast.grey_lady|int}}, Green Lady {{cast.green_lady|int}} ({{green_scot_castle|int}} in Scottish castles), monk or abbot {{cast.monk|int}}, nun {{cast.nun|int}}, child {{cast.child|int}}, headless {{cast.headless|int}} (all English). Coloured ladies: {{lady_castle|int}} of {{n_castle_texts|int}} castles, {{lady_inn|int}} of {{n_inn_texts|int}} inns.

## Files

- `index.html`: the interactive page (Leaflet map, charts). Data are embedded.
- `header.png`: social card (1200 by 630).
- `data/haunted_places.csv`: one row per place: name, kind (and how it was decided), country, region, county, district, coordinates, how and from what it was placed (`geo_method`, `geo_source`, `geo_precision`, `geo_note`), Wikidata QID, listing grade if top-listed, year and its source, Wikipedia article and URL, source categories or lists, the ghost types found (`g_*` columns, 1 = mentioned) and the first sentence that makes it haunted.
- `data/ghost_false_hits.csv`: every automatic ghost-type match removed by hand, with the reason.
- `data/listed_baseline.csv.gz`: the {{n_listed_all|int}} Grade I, II* and Category A listed items with kind, building flag, region and inception year.
- `data/kind_mix.csv`, `data/regions.csv`, `data/cast_by_kind.csv`: the main result tables.
- `data/results.json`: every number used on the page, in the paper, the blog post and the collage.
- `code/`: `01_collect.py`, `02_geocode.py`, `03_classify.py`, `04_baseline.py`, `05_analyse.py`, `06_build_site.py`, `07_header.py`, run in that order (with `common.py`, `coords.py`, `kinds.py`). `release/` holds the paper and blog figure scripts and `reddit/` the collage.

## Method in brief

Places: English Wikipedia categories "Reportedly haunted locations in" the United Kingdom, England, Scotland, Wales and Ireland (two levels), "List of reportedly haunted locations in the United Kingdom", "Reportedly haunted locations in Scotland", the Ireland section of "List of reportedly haunted locations" and the ghost sightings in "List of paranormal events reported in Wiltshire, England" (wikitext of 27 October 2026); {{n_excluded|int}} non-places removed. Coordinates from the article, a Wikidata item of the same building, the Sites and Monuments Record (Ireland), or the named town or feature in OS Open Names; {{n_unplaced|int}} not placed. Kinds by rules on name and description, with recorded hand corrections. Dates: Wikidata inception (P571) or the first year in the infobox. Baseline: Wikidata items designated Grade I (Q15700818), Grade II* (Q15700831) or Category A (Q10729054) with coordinates; kinds from the Wikidata class label or name. Regions from the nearest OS Open Names populated place. Ghost types: regular expressions on the sentences around each ghost word, every match read by hand.

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
