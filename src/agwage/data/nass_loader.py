import os
import requests
import pandas as pd
import json
from pathlib import Path

from agwage import directories
from agwage.utils import api_tools
from agwage.utils.nass_api_helpers import get_available_parameters, save_options_report, explore_available_commidities
from agwage import load_api_key
from agwage.utils.api_tools import format_param_filename
from agwage.data.query_presets import FIELD_CROPS_BASE, CORE_VARIABLES

NASS_API_KEY = load_api_key("NASS_API_KEY")

# Base URL for NASS QuickStats
NASS_API_URL = "https://quickstats.nass.usda.gov/api/api_GET/"

def get_nass_data(params: dict, cache_filename: str = None, overwrite: bool = False) -> pd.DataFrame:
    """
    Request data from the USDA NASS QuickStats API and return as a DataFrame.
    Optionally cache the result to a CSV file in the raw data directory.
    
    Parameters:
        params (dict): API query parameters.
        cache_filename (str): Optional filename to cache the response.
        overwrite (bool): If True, overwrite existing cache file.
    
    Returns:
        pd.DataFrame: The requested data.
    """
    # Add API key to request parameters
    params["key"] = NASS_API_KEY
    params["format"] = "CSV"

    # Determine cache path
    if cache_filename:
        cache_path = directories.RAW_DIR / cache_filename
        if cache_path.exists() and not overwrite:
            print(f"Loading cached file: {cache_path}")
            return pd.read_csv(cache_path)

    # Make the API request
    print(f"Requesting data from NASS QuickStats API with params: {params}")
    response = requests.get(NASS_API_URL, params=params)
    response.raise_for_status()

    # Read into DataFrame
    from io import StringIO
    df = pd.read_csv(StringIO(response.text))

    # Save to cache if requested
    if cache_filename:
        df.to_csv(cache_path, index=False)
        print(f"Saved to cache: {cache_path}")

    return df

def run_core_variable_reports(core_variable_list, output_dir="unit_files", overwrite=True):
    """
    Loop through a list of (sector, group, variable_list) tuples and run save_options_report.

    Args:
        core_variable_list (list): Tuples like (sector_desc, group_desc, [commodity_descs])
        output_dir (str): Subfolder in METADATA_DIR where files will be saved
        overwrite (bool): If True, overwrite existing files
    """
    for sector, group, commodities in core_variable_list:
        print(f"\n[GROUP] {group} | [SECTOR] {sector} | {len(commodities)} commodities")
        
        filename = f"{group.replace(' ', '_').upper()}__unit_matrix.json"
        folder_path = directories.METADATA_DIR / output_dir
        folder_path.mkdir(parents=True, exist_ok=True)
        path = folder_path/ filename

        save_options_report(
            commodities=commodities,
            output_filename=path.name,
            overwrite=overwrite,
            filters={"sector_desc": sector, "group_desc": group}
        )

def collate_unit_files(directory: Path) -> pd.DataFrame:
    """
    Collate all unit matrix JSON files into a single long-form DataFrame.
    Uses CORE_VARIABLES to attach group/sector metadata.

    Args:
        directory (Path): Path to the 'unit_files' directory.

    Returns:
        pd.DataFrame with columns: COMMODITY, SECTOR, GROUP, STATISTIC, UNIT
    """
    # Flatten CORE_VARIABLES into commodity → (sector, group) lookup
    commodity_to_context = {}
    for sector, group, commodities in CORE_VARIABLES:
        for c in commodities:
            commodity_to_context[c.upper()] = (sector, group)

    records = []

    for file_path in directory.glob("*.json"):
        with open(file_path, "r") as f:
            data = json.load(f)

        for commodity, stat_map in data.items():
            commodity_upper = commodity.upper()
            sector, group = commodity_to_context.get(commodity_upper, ("UNKNOWN", "UNKNOWN"))

            for stat, units in stat_map.items():
                for unit in units:
                    records.append({
                        "SECTOR": sector,
                        "GROUP": group,
                        "COMMODITY": commodity_upper,
                        "STATISTIC": stat,
                        "UNIT": unit
                    })

    return pd.DataFrame(records)

if __name__ == '__main__':
    corn_query = {
        **FIELD_CROPS_BASE,
        "commodity_desc": "CORN",
        "statisticcat_desc": "AREA HARVESTED",
        "unit_desc": "ACRES",
        "year": "2022"
    }
    
    metadata_df = collate_unit_files(directories.METADATA_DIR/'unit_files')
    metadata_df.to_csv(directories.METADATA_DIR/'unit_files/collated_unit_metadata.csv', index=False)

    print(metadata_df.shape)

    if False:
        #GATHER metadata info for our commodities of interest
        run_core_variable_reports(CORE_VARIABLES, overwrite=True)

        #EXPLORE AVAILABLE COMMODITY VALUES
        explore_available_commidities(sector="CROPS", group="FIELD CROPS")
        explore_available_commidities(sector="ANIMALS & PRODUCTS", group="LIVESTOCK")
        explore_available_commidities(sector="ANIMALS & PRODUCTS", group="POULTRY")
        explore_available_commidities(sector="ECONOMICS", group="INCOME")
        explore_available_commidities(sector="ECONOMICS", group="EXPENSES")
        explore_available_commidities(sector="ECONOMICS", group="PRICES PAID")
    
        #SAVE Base values per parameter available
        for key in ["source_desc", "sector_desc", "group_desc", "commodity_desc", "statisticcat_desc", "unit_desc", "year", "agg_level_desc"]:
            print(f'processeing key: {key}')
            param_list = get_available_parameters(param=key)
            api_tools.save_parameter_values(key, param_list, format="json")