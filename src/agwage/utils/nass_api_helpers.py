import json
import requests
from pathlib import Path

from agwage import config, directories
from agwage.utils import api_tools

def get_available_parameters(
    param: str,
    format: str = "JSON",
    api_url: str = "https://quickstats.nass.usda.gov/api/get_param_values/",
    **filters
) -> list:
    """
    Fetch valid values for a given NASS parameter, optionally conditioned on other parameters.

    Args:
        param (str): The parameter to retrieve values for (e.g., "commodity_desc").
        format (str): "JSON" or "CSV".
        api_url (str): NASS API endpoint.
        **filters: Additional query parameters to condition results (e.g., sector_desc="CROPS").

    Returns:
        list: Valid values for the requested parameter.
    """
    query = {
        "key": config.NASS_API_KEY,
        "param": param,
        "format": format
    }
    query.update(filters)

    response = requests.get(api_url, params=query)
    response.raise_for_status()

    data = response.json()
    values = data.get(param, [])
    print(f"Found {len(values)} values for '{param}' with filters: {filters or 'None'}")

    return values

def get_valid_units(commodity: str, stat: str, **base_filters) -> list:
    """
    Retrieve valid unit_desc values for a given commodity and statistic.

    Args:
        commodity (str): Commodity description (e.g., "CORN")
        stat (str): Statistic category (e.g., "YIELD")
        **base_filters: Other filters like sector_desc, group_desc

    Returns:
        list[str]: Available unit_desc values
    """
    return get_available_parameters(
        "unit_desc",
        commodity_desc=commodity,
        statisticcat_desc=stat,
        **base_filters
    )

def save_options_report(
    commodities: list[str],
    output_filename: str,
    output_path: Path = directories.METADATA_DIR,
    overwrite: bool = False,
    param_stats: str = "statisticcat_desc",
    param_units: str = "unit_desc",
    filters: dict = None,
) -> None:
    """
    For each commodity, find available stats (e.g., statisticcat_desc), and for each stat,
    find available units (e.g., unit_desc). Saves a nested JSON.

    Args:
        commodities (list): List of commodity_desc values
        output_filename (str): Output filename (e.g. "core_crops_unit_matrix.json")
        overwrite (bool): Whether to overwrite the file if it exists
        param_stats (str): Parameter for statistic categories (default: "statisticcat_desc")
        param_units (str): Parameter for units per stat (default: "unit_desc")
        filters (dict): Any additional filters like sector/group
    """
    filters = filters or {}
    report = {}

    for commodity in commodities:
        print(f"[{commodity}] Gathering {param_stats}...")
        stats = get_available_parameters(param_stats, commodity_desc=commodity, **filters)

        stat_map = {}
        for stat in stats:
            units = get_available_parameters(param_units, commodity_desc=commodity, **filters, statisticcat_desc=stat)
            stat_map[stat] = units

        report[commodity] = stat_map

    output_path = output_path / output_filename
    if output_path.exists() and not overwrite:
        print(f"File already exists: {output_path}")
        return

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[SUCCESS] Saved {param_stats} {param_units} matrix for {len(commodities)} commodities to {output_path}")

def explore_available_commidities(sector, group):
    filename = api_tools.format_param_filename("commodity_desc", sector_desc=sector, group_desc=group)
    # filename = api_tools.format_param_filename("commodity_desc", sector_desc="ANIMALS & PRODUCTS", group_desc="POULTRY")
    params = get_available_parameters("commodity_desc", sector_desc=sector, group_desc=group)
    # params = get_available_parameters("commodity_desc", sector_desc="ANIMALS & PRODUCTS", group_desc="POULTRY")
    api_tools.save_parameter_values(filename, params, format='json')