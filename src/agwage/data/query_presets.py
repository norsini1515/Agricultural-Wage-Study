# src/agwage/data/query_presets.py

# Base presets (category-wide)
FIELD_CROPS_BASE = {
    "source_desc": "SURVEY",
    "sector_desc": "CROPS",
    "group_desc": "FIELD CROPS",
    "agg_level_desc": "COUNTY"
}
FIELD_CROPS_CORE_STATS = [
    "AREA PLANTED",
    "AREA HARVESTED",
    "YIELD",
    "PRODUCTION",
    "PRICE RECEIVED",
    "CONDITION"
]

LIVESTOCK_BASE = {
    "source_desc": "SURVEY",
    "sector_desc": "ANIMALS & PRODUCTS",
    "group_desc": "LIVESTOCK",
    "agg_level_desc": "COUNTY"
}


POULTRY_BASE = {
    "source_desc": "SURVEY",
    "sector_desc": "ANIMALS & PRODUCTS",
    "group_desc": "POULTRY",
    "agg_level_desc": "COUNTY"
}

ECONOMICS_BASE = {
    "source_desc": "SURVEY",
    "sector_desc": "ECONOMICS",
    "agg_level_desc": "STATE"
}


FIELD_CROPS_CORE = [
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
    "HAY",
    "SUNFLOWER",
    "SMALL GRAINS"
]
LIVESTOCK_CORE = [
    "RED MEAT",
    "PORK",
    "FEED",
    "LIVESTOCK TOTALS",
    "CATTLE",
    "HOGS",
    "SHEEP",
    "GOATS"
]
POULTRY_CORE = [
    "DUCKS"
    "CHICKENS",
    "EGGS",
    "MEAL",
    "TURKEYS",
    "POULTRY TOTALS"
]
INCOME_CORE = [
    "INCOME, NET CASH FARM",
    "INCOME, FARM-RELATED",
    "GOVT PROGRAMS",
    "ANIMAL TOTALS",
    "CROP TOTALS"
]
EXPENSES_CORE = [
    "FEED",
    "FERTILIZER TOTALS",
    "LABOR",
    "EXPENSE TOTALS",
    "ANIMAL TOTALS",
    "FERTILIZER & CHEMICAL TOTALS",
    "SEEDS & PLANTS TOTALS",
    "WATER",
    "FUEL",
    "RENT",
    "TAXES",
    "EXPENSE TOTALS",
    "INTEREST",
]
PRICES_PAID_CORE = [
    "FERTILIZER TOTALS",            # Broad fertilizer index
    "FERTILIZER, MIXED",            # Sub-type for granularity
    "FUELS",                        # Volatile, often modeled alongside energy prices
    "LABOR",                        # Direct link to your wage study
    "SUPPLIES & REPAIRS",           # Operating costs
    "RENT",                         # Land access costs
    "TRACTORS",                     # Machinery investment
    "SEEDS & PLANTS TOTALS",        # Crop-specific inputs
    "CHEMICAL TOTALS",              # Herbicides/fungicides/pesticides
    "MACHINERY TOTALS"              # Broad capital costs
]


# CORE_VARIABLES = [
#     #sector, group, commodity
#     ("CROPS", "FIELD CROPS", FIELD_CROPS_CORE),
#     ("ANIMALS & PRODUCTS", "LIVESTOCK", LIVESTOCK_CORE),
#     ("ANIMALS & PRODUCTS", "POULTRY", POULTRY_CORE),
#     ("ECONOMICS", "INCOME", INCOME_CORE),
#     ("ECONOMICS", "EXPENSES", EXPENSES_CORE),
#     ("ECONOMICS", "PRICES PAID", PRICES_PAID_CORE),
# ]

CORE_VARIABLES = {
    "FIELD CROPS": {
        "sector": "CROPS",
        "commodities": FIELD_CROPS_CORE
    },
    "LIVESTOCK": {
        "sector": "ANIMALS & PRODUCTS",
        "commodities": LIVESTOCK_CORE
    },
    "POULTRY": {
        "sector": "ANIMALS & PRODUCTS",
        "commodities": POULTRY_CORE
    },
    "INCOME": {
        "sector": "ECONOMICS",
        "commodities": INCOME_CORE
    },
    "EXPENSES": {
        "sector": "ECONOMICS",
        "commodities": EXPENSES_CORE
    },
    "PRICES PAID": {
        "sector": "ECONOMICS",
        "commodities": PRICES_PAID_CORE
    }
}
