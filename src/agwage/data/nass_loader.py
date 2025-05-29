#src/agwage/data/nass_loader.py
import os
import json
import time
import requests
import pandas as pd
from typing import Dict
from pathlib import Path
from agwage import directories
from agwage.utils import api_tools
from agwage.utils.nass_api_helpers import get_available_parameters, save_options_report, explore_available_commidities
from agwage import load_api_key
from agwage.data.query_presets import FIELD_CROPS_BASE, CORE_VARIABLES

NASS_API_KEY = load_api_key("NASS_API_KEY")

# Base URL for NASS QuickStats
NASS_API_URL = "https://quickstats.nass.usda.gov/api/api_GET/"

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

def inject_download_metadata(df: pd.DataFrame, params: Dict, additional_fields: Dict = None) -> pd.DataFrame:
    """
    Inject standard metadata columns into the DataFrame using API query parameters
    and optionally additional custom metadata.

    Parameters:
        df (pd.DataFrame): The original NASS response data.
        params (dict): The original API request parameters.
        additional_fields (dict, optional): Extra metadata fields to inject.

    Returns:
        pd.DataFrame: Modified DataFrame with metadata and uppercased columns.
    """
    df = df.copy()

    # From API params
    metadata_fields = {
        "COMMODITY": params.get("commodity_desc"),
        "STATISTIC": params.get("statisticcat_desc"),
        "UNIT": params.get("unit_desc"),
        "YEAR": params.get("year"),
        "GROUP": params.get("group_desc"),
        "SECTOR": params.get("sector_desc"),
        "DOWNLOAD_DATE": pd.Timestamp.now().isoformat()
    }

    # Merge with any additional user-defined fields
    if additional_fields:
        metadata_fields.update({k.upper(): v for k, v in additional_fields.items()})

    # Inject into DataFrame
    for col, val in metadata_fields.items():
        df[col] = val

    # Uppercase all column names
    df.columns = df.columns.str.upper()

    return df

def download_nass_data(
    params: dict,
    filename: str = None,
    filepath: Path = directories.RAW_DIR,
    overwrite: bool = False,
    verbose: bool = False
    ) -> None:
    """
    Fetch data from the USDA NASS QuickStats API as a DataFrame.
    Optionally read from or write to a local CSV file to avoid repeat downloads.

    Parameters:
        params (dict): Query parameters for the API (excluding key/format).
        filename (str): Optional file name to read from/write to.
        filepath (Path): Directory to read/write file from.
        overwrite (bool): If True, overwrite existing file.

    Returns:
        pd.DataFrame: The requested or cached data.
    """
    # Add API key to request parameters
    params["key"] = NASS_API_KEY
    params["format"] = "CSV"

    # Determine cache path
    if filename:
        cache_path = filepath / filename
        if cache_path.exists() and not overwrite:
            print(f"Loading cached file: {cache_path}")
            return pd.read_csv(cache_path)

    # Make the API request
    if verbose:
        print(f"Requesting data from NASS QuickStats API with params: {params}")
    response = requests.get(NASS_API_URL, params=params)
    response.raise_for_status()

    # Read into DataFrame
    from io import StringIO
    df = pd.read_csv(StringIO(response.text))

    # Save to cache if requested
    if filename:
        # Inject useful metadata (in case it's missing or for standardization)
        df = inject_download_metadata(df, params)
        # Write to disk
        df.to_csv(cache_path, index=False)
        print(f"Saved to cache: {cache_path}")

    return df

def download_timeseries_group(
    base_query: dict,
    group: str,
    statistic: str,
    unit: str = None,
    year_range: tuple = (1996, 2024),
    verbose: bool = False
) -> None:
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
    if not unit_metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found at: {unit_metadata_path}")

    metadata = pd.read_csv(unit_metadata_path)
    
    filtered_df = metadata[(metadata["GROUP"] == group) & (metadata["STATISTIC"] == statistic)]

    if unit:
        filtered_df = filtered_df[filtered_df["UNIT"] == unit]

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
                if verbose:
                    print(query)
                try:
                    filename = api_tools.sanitize_filename(commodity, statistic, u, year) + ".csv"
                    filepath = directories.RAW_DIR / query['group_desc']
                    filepath.mkdir(exist_ok=True, parents=True)
                    if verbose:
                        print(f"{filename=}")
                    download_nass_data(query, filename=filename, filepath=filepath,
                                       overwrite=False)

                except Exception as e:
                    if verbose:
                        print(f"[FAILURE] {commodity} {statistic} {u} {year} failed: {e}")
                    continue

                api_tools.rate_limit_pause(1)

def run_group_metric_downloads(
    base_query: dict,
    metrics_dict: dict,
    skip_classifications: list[str] = None,
    group_name: str = "FIELD CROPS",
    year_range: tuple = (1980, 2024),
    verbose: bool = True
) -> None:
    """
    Run batch downloads for a group using a metric dictionary.

    Args:
        base_query (dict): Base query dictionary (e.g., FIELD_CROPS_BASE).
        metrics_dict (dict): Dictionary of {classification: [(stat, unit), ...]}.
        skip_classifications (list): Optional list of classifications to skip.
        group_name (str): NASS group name (e.g., "FIELD CROPS").
        year_range (tuple): Year span to download.
        verbose (bool): Print progress messages.
    """
    skip_classifications = skip_classifications or []

    for classification, groupings in metrics_dict.items():
        if classification in skip_classifications:
            if verbose:
                print(f"SKIPPING {classification} (already downloaded)\n")
            continue

        for statistic, unit in groupings:
            if verbose:
                print(f"BEGINNING {classification.upper()} | {statistic} ({unit})")
            try:
                download_timeseries_group(
                    group=group_name,
                    statistic=statistic,
                    unit=unit,
                    base_query=base_query,
                    year_range=year_range,
                    verbose=verbose
                )
                if verbose:
                    print(f"[SUCCESS] Finished: {statistic} ({unit})\n")
            except Exception as e:
                print(f"[FAILURE] {statistic} ({unit}) - {e}\n")


if __name__ == '__main__':
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
            print(f'Processing  key: {key}')
            param_list = get_available_parameters(param=key)
            api_tools.save_parameter_values(key, param_list, format="json")