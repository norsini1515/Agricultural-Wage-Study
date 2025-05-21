# src/agwage/data/query_presets.py

# Base presets (category-wide)
CROPS_BASE = {
    "source_desc": "SURVEY",
    "sector_desc": "CROPS",
    "group_desc": "FIELD CROPS",
    "agg_level_desc": "COUNTY"
}
CROP_CORE_STATS = [
    "AREA PLANTED",
    "AREA HARVESTED",
    "YIELD",
    "PRODUCTION",
    "PRICE RECEIVED",
    "CONDITION"
]

CORE_CROPS = [
    "CORN",
    "SOYBEANS",
    "WHEAT",
    "COTTON",
    "RICE",
    "OATS",
    "BARLEY",
    "SORGHUM",
    "PEANUTS",
    "SUGARBEETS",
    "TOBACCO",
    "HAY"
]


ANIMALS_BASE = {
    "source_desc": "SURVEY",
    "sector_desc": "ANIMALS & PRODUCTS",
    "group_desc": "LIVESTOCK",
    "agg_level_desc": "COUNTY"
}

ECONOMICS_BASE = {
    "source_desc": "SURVEY",
    "sector_desc": "ECONOMICS",
    "agg_level_desc": "STATE"
}
