import json
import pandas as pd
from pathlib import Path
from typing import List, Union

from agwage import directories

def save_parameter_values(
    param: str,
    values: List[Union[str, int]],
    format: str = "csv",
    destination: Path = None,
    overwrite: bool = False
) -> Path:
    """
    Save a list of parameter values to CSV or JSON.

    Args:
        param (str): Name of the parameter (used as column name and filename).
        values (list): List of parameter values (strings or numbers).
        format (str): 'csv' or 'json'.
        destination (Path): Optional custom path to save the file.
        overwrite (bool): If True, overwrite existing file.

    Returns:
        Path: The path of the saved file.
    """
    if format not in {"csv", "json"}:
        raise ValueError("format must be 'csv' or 'json'")

    # Determine default path
    if destination is None:
        destination = directories.METADATA_DIR / f"{param}_values.{format}"

    if destination.exists() and not overwrite:
        print(f"File already exists: {destination}")
        return destination

    if format == "json":
        with open(destination, "w") as f:
            json.dump(values, f, indent=2)
    else:  # CSV
        df = pd.DataFrame(values, columns=[param])
        df.to_csv(destination, index=False)

    print(f"Saved {len(values)} '{param}' values to: {destination}")
    return destination

def build_query(base: dict, **overrides) -> dict:
    """
    Merge a base query dictionary with override values.

    Args:
        base (dict): Base parameter dictionary (e.g., from a preset).
        **overrides: Any values to override or extend the base.

    Returns:
        dict: Combined query.
    """
    return {**base, **overrides}

def format_param_filename(param: str, **filters) -> str:
    """
    Create a safe, informative filename for a saved parameter list.
    """
    parts = [param] + [f"{k}-{v.replace(' ', '_')}" for k, v in filters.items()]
    return "_".join(parts)