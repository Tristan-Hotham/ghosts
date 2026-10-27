"""Place kinds, shared by the haunted places and the baseline of listed buildings.

A place is given the first kind whose pattern matches its name, then its description (Wikipedia short description and
infobox type, or Wikidata class label). The order matters: "Castle Hotel" is an inn, "Castle Huntly" prison is a gaol.
"""
import re

KINDS = ["castle", "house", "inn", "church", "theatre", "gaol", "military", "civic", "other_building", "road", "outdoor", "settlement"]
LABEL = {"castle": "Castle or tower", "house": "House, hall or palace", "inn": "Inn, pub or hotel", "church": "Church, abbey or chapel",
         "theatre": "Theatre", "gaol": "Gaol or court", "military": "RAF base or military site", "civic": "Guildhall, school or museum",
         "other_building": "Other building", "road": "Road, street, bridge or tunnel", "outdoor": "Wood, hill, cave or stone",
         "settlement": "Whole village or town"}
BUILDING_KINDS = ["castle", "house", "inn", "church", "theatre", "gaol", "military", "civic", "other_building"]

# patterns tried on the name first, then on the description
RULES = [
    ("gaol", r"\b(gaol|jail|prison|tolbooth|justice museum|courthouse|county gaol|bridewell|lock-?up)\b"),
    ("military", r"\b(raf|air station|airfield|dockyard|nuclear bunker|barracks|military museum|muckleburgh|military installation|army camp|drill hall|armoury)\b"),
    ("theatre", r"\b(theatre|playhouse|opera house|music hall|carnegie hall|lyceum)\b"),
    ("inn", r"\b(inn|pub|public house|tavern|hotel|arms|witchery|nightclub|restaurant|bar|alehouse|coaching inn|grenadier|flask|golden fleece|lower bell|owd betts|schooner|red lion|black swan|golden lion|punch bowl|ostrich)\b"),
    ("church", r"\b(church|abbey|priory|chapel|cathedral|kirk|minster|friary|nunnery|monastery|parish church|church building|chantry|clergy house)\b"),
    ("castle", r"\b(castle|tower house|keep|peel tower|pele|bastle|fort|motte|tower|fortalice|fortified house|castle hall|citadel|fortification)\b"),
    ("road", r"\b(road|bypass|street|lane|close|walk|causeway|bridge|tunnel|crossroads|terrace|footpath|highway|tube station|underground streets|vaults|leap|hands)\b"),
    ("outdoor", r"\b(wood|woods|forest|hill|mountain|cave|caves|lake|loch|stone|henge|down|moor|tree|grave|hole|park|garden|stone circle|common)\b"),
    ("house", r"\b(house|hall|manor|mansion|palace|rectory|vicarage|grange|lodge|court|townhouse|stately home|country house|farmhouse|cottage|villa|estate home|estate|althorp|longleat|guy's cliffe|plas teg|craigdarroch|hinton ampner|glasshayes|ballechin|appuldurcombe|aberglasney|bramshill|menacuddle|duckett's grove|springhill|25 berkeley|berkeley square|green street|wymering|flitwick|athelhampton|llancaiach|sker|newton house|maesmawr|loftus|raynham|chavenage|woodchester)\b"),
    ("civic", r"\b(guildhall|school|museum|museum building|city hall|town hall|library|university|college|institute|masonic|cloisters)\b"),
    ("other_building", r"\b(lighthouse|shop|department store|barn|mill|warehouse|station|building|built structure|bank)\b"),
    ("settlement", r"\b(village|town|hamlet|parish|uk place|settlement)\b"),
]


def kind_of(name, desc=""):
    for text in (name or "", desc or ""):
        t = text.lower()
        for k, pat in RULES:
            if re.search(pat, t):
                return k
    return None


# Wikidata class labels of the listed-building baseline that are not buildings people would tell a ghost story about as such
# (walls, gates, monuments, bridges...) are kept but fall into 'other_building' or 'road'; generic labels ("building",
# "built structure") are classified by the item's name.
LISTED_CLASS = {
    "castle": ["castle", "tower house", "keep", "motte", "bastle house", "pele tower", "peel tower", "fortified house", "fort", "artillery fort", "fortified tower", "ruined castle", "castle ruin", "citadel", "fortification", "shell keep", "concentric castle"],
    "house": ["house", "english country house", "country house", "manor house", "mansion", "stately home", "palace", "royal residence", "townhouse", "villa", "farmhouse", "historic house museum", "hall house", "rectory", "vicarage", "clergy house", "lodge", "hunting lodge", "thatched farmhouse", "cottage", "thatched cottage", "terrace house", "detached house", "semi-detached house", "terrace of houses", "tenement", "estate", "manor", "bishop's palace", "deanery", "almshouse", "mews", "rural house", "residential building", "official residence", "great house", "wealden hall house", "longhouse", "hall", "summer house", "town house"],
    "inn": ["pub", "inn", "hotel", "coaching inn", "tavern", "public house", "thatched pub", "restaurant", "bar", "hostel", "youth hostel", "brewery"],
    "church": ["church building", "parish church", "chapel", "cathedral", "abbey", "priory", "catholic church building", "church", "minster", "friary", "monastery", "church ruin", "ruined church", "chapel of ease", "chantry chapel", "collegiate church", "nonconformist chapel", "methodist chapel", "baptist chapel", "quaker meeting house", "meeting house", "synagogue", "mosque", "nunnery", "convent", "cistercian monastery", "benedictine monastery", "augustinian priory", "former church", "mortuary chapel", "private chapel", "free church", "united reformed church", "church hall", "kirk", "parish kirk"],
    "theatre": ["theatre building", "theatre", "music hall", "opera house", "concert hall", "cinema"],
    "gaol": ["prison", "gaol", "jail", "courthouse", "tolbooth", "lock-up", "police station", "court"],
    "military": ["barracks", "military base", "air base", "airfield", "drill hall", "armoury", "military building", "naval base", "dockyard", "bunker", "pillbox"],
    "civic": ["city hall", "town hall", "guildhall", "school building", "school", "museum building", "museum", "library", "university building", "local authority museum", "art museum", "history museum", "grammar school", "college", "hospital building", "hospital", "market hall", "corn exchange", "assembly rooms", "masonic hall"],
}
CLASS2KIND = {c: k for k, cs in LISTED_CLASS.items() for c in cs}
NON_BUILDING = re.compile(r"\b(wall|walls|gate|gates|gatepiers?|gatepost|railings?|bridge|footbridge|viaduct|monument|memorial|statue|cross|tomb|tombs|headstone|milestone|sundial|fountain|obelisk|urn|steps|kiosk|telephone|lamp|pump|bollard|boundary|well|garden|park|grotto|folly|ha-ha|lych|mausoleum|war memorial|churchyard)\b")
