import os
import requests
import pandas as pd

from agwage import directories
from agwage.utils import api_tools
from agwage.utils.nass_api_helpers import get_available_parameters, get_valid_units, save_unit_options_report
from agwage import load_api_key
from agwage.utils.api_tools import format_param_filename
from agwage.data.query_presets import CROPS_BASE, CROP_CORE_STATS, CORE_CROPS

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

def run_crop_unit_report(commodity: str):
    """
    Generate and save unit_desc metadata for a given crop across core statistics.

    Args:
        commodity (str): e.g., "CORN", "SOYBEANS"
    """
    print(f"Running unit report for: {commodity}")
    save_unit_options_report(
        commodity=commodity,
        stats=CROP_CORE_STATS,
        sector_desc="CROPS",
        group_desc="FIELD CROPS"
    )

if __name__ == '__main__':
    corn_query = {
        **CROPS_BASE,
        "commodity_desc": "CORN",
        "statisticcat_desc": "AREA HARVESTED",
        "unit_desc": "ACRES",
        "year": "2022"
    }
    for crop in CORE_CROPS:
        run_crop_unit_report(commodity=crop)

    if False:
        filename = format_param_filename("unit_desc", sector_desc="CROPS", group_desc="FIELD CROPS")
        params = get_available_parameters("unit_desc", sector_desc="CROPS", group_desc="FIELD CROPS", statisticcat_desc="MOISTURE")
        print(params)
        api_tools.save_parameter_values(filename, params, format='json')


        filename = format_param_filename("statisticcat_desc", sector_desc="CROPS", group_desc="FIELD CROPS")
        params = get_available_parameters("statisticcat_desc", sector_desc="CROPS", group_desc="FIELD CROPS")
        api_tools.save_parameter_values(filename, params, format='json')

        for key in ["source_desc", "sector_desc", "group_desc", "commodity_desc", "statisticcat_desc", "unit_desc", "year", "agg_level_desc"]:
            print(f'processeing key: {key}')
            param_list = get_available_parameters(param=key)
            api_tools.save_parameter_values(key, param_list, format="json")