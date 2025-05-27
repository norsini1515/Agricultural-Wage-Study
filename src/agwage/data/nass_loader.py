import os
import json
import time
import requests
import pandas as pd
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

def run_core_variable_reports(core_variable_dict, output_dir="unit_files", overwrite=True):
    """
    Loop through a dictionary of core variables and run save_options_report for each group.

    Args:
        core_variable_dict (dict): Format {
            "GROUP_NAME": {
                "sector": "SECTOR_NAME",
                "commodities": [list of commodity_descs]
            }, ...
        }
        output_dir (str): Subfolder in METADATA_DIR where files will be saved
        overwrite (bool): If True, overwrite existing files
    """
    folder_path = directories.METADATA_DIR / output_dir
    folder_path.mkdir(parents=True, exist_ok=True)

    for group, config in core_variable_dict.items():
        sector = config["sector"]
        commodities = config["commodities"]

        print(f"\n[GROUP] {group} | [SECTOR] {sector} | {len(commodities)} commodities")

        filename = f"{group.replace(' ', '_').upper()}__unit_matrix.json"

        save_options_report(
            commodities=commodities,
            output_path=folder_path,
            output_filename=filename,
            overwrite=overwrite,
            filters={"sector_desc": sector, "group_desc": group}
        )

def collate_unit_files(directory: Path, core_variable_dict: dict) -> pd.DataFrame:
    """
    Collate all unit matrix JSON files into a single long-form DataFrame.
    Uses CORE_VARIABLES dict to attach group/sector metadata.

    Args:
        directory (Path): Path to the 'unit_files' directory.
        core_variable_dict (dict): Format {
            "GROUP_NAME": {
                "sector": "SECTOR_NAME",
                "commodities": [list of commodity_descs]
            }, ...
        }

    Returns:
        pd.DataFrame with columns: COMMODITY, SECTOR, GROUP, STATISTIC, UNIT
    """
    # Flatten CORE_VARIABLES into commodity → (sector, group) lookup
    commodity_to_context = {}
    for group, config in core_variable_dict.items():
        sector = config["sector"]
        for c in config["commodities"]:
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

def download_timeseries_group(
    base_query: dict,
    group: str,
    statistic: str,
    unit: str = None,
    year_range: tuple = (2010, 2024),
    state: str = "US",  # or None for national
    freq: str = "ANNUAL",  # or "MONTHLY"
    include_units: bool = False,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Download time series data from NASS QuickStats for all commodities in a given group and statistic.

    Parameters:
        group (str): The commodity group (e.g., "FIELD CROPS").
        statistic (str): The statistical category (e.g., "PRICE RECEIVED").
        year_range (tuple): Start and end year (inclusive).
        state (str): US state abbreviation or "US" for national.
        freq (str): Frequency ("ANNUAL" or "MONTHLY").
        include_units (bool): If True, include unit_desc in final output.
        verbose (bool): If True, print progress.

    Returns:
        pd.DataFrame: Combined time series data.
    """
    # Load and filter metadata
    unit_metadata_path = directories.METADATA_DIR / "unit_files" / "collated_unit_metadata.csv"
    metadata = pd.read_csv(unit_metadata_path)
    
    filtered_df = metadata[(metadata["GROUP"] == group) & (metadata["STATISTIC"] == statistic)]

    if unit:
        filtered_df = filtered_df[filtered_df["UNIT"] == unit]

    all_results = []

    for _, row in filtered_df.iterrows():
        commodity = row["COMMODITY"]
        units = [unit] if unit else [row["UNIT"]]

        for u in units:
            for year in range(year_range[0], year_range[1] + 1):
                query = {
                    **base_query,
                    "commodity_desc": commodity,
                    "statisticcat_desc": statistic,
                    "unit_desc": u,
                    "year": year
                }
                print(query)
                try:
                    cache_filename = format_param_filename("nas_group", **query)
                    print(f"{cache_filename=}")
                    df = get_nass_data(query, cache_filename=cache_filename, overwrite=False)

                    if not df.empty:
                        if verbose:
                            print(f"[SUCCESS] {commodity} {statistic} {u} {year}")
                        df["UNIT_USED"] = u
                        all_results.append(df)

                except Exception as e:
                    if verbose:
                        print(f"[FAILURE] {commodity} {statistic} {u} {year} failed: {e}")
                    continue

                time.sleep(1)

    if not all_results:
        return pd.DataFrame()

    return pd.concat(all_results, ignore_index=True)






if __name__ == '__main__':
    crop = 'CORN'
    stat = "" #to replace
    unit = "" #to replace
    year = 2015
    df = download_timeseries_group(
        group="FIELD CROPS",
        statistic="AREA PLANTED",
        base_query=FIELD_CROPS_BASE,
        unit="ACRES",  # or None
        year_range=(2015, 2020)
        )
    
    

    if False:
        #GROUP metadata interests
        metadata_df = collate_unit_files(directories.METADATA_DIR/'unit_files', CORE_VARIABLES)
        metadata_df.to_csv(directories.METADATA_DIR/'unit_files/collated_unit_metadata.csv', index=False)

        print(metadata_df.shape)


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