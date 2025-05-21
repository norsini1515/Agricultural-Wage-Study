import json
import requests
from pathlib import Path

from agwage import config, directories

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

def save_unit_options_report(
    commodity: str,
    stats: list[str],
    filename: str = None,
    overwrite: bool = False,
    **filters
) -> None:
    """
    Save a single JSON file containing all available unit_desc values
    for each statisticcat_desc related to a given commodity.

    Args:
        commodity (str): e.g. "CORN"
        stats (list[str]): List of statisticcat_desc values to check
        filename (str): Optional custom file name (default auto-generated)
        overwrite (bool): If False, skip if file already exists
        **filters: Additional NASS parameters (sector_desc, group_desc, etc.)

    # Returns:
        # Path: Path to the saved JSON file
    """
    report = {}
    for stat in stats:
        units = get_available_parameters(
            "unit_desc",
            commodity_desc=commodity,
            statisticcat_desc=stat,
            **filters
        )
        report[stat] = units

    if filename is None:
        safe_name = commodity.replace(" ", "_").upper()
        filename = f"{safe_name}__unit_options.json"

    output_path = directories.METADATA_DIR / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not overwrite:
        print(f"File already exists: {output_path}")
        return output_path

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[✓] Saved unit options report for '{commodity}' to {output_path}")


