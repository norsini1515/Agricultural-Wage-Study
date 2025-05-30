#src/agwage/scripts/field_crops_downloads.py

from agwage.data.query_presets import FIELD_CROPS_BASE, FIELD_CROPS_METRICS
from agwage.data.nass_loader import run_group_metric_downloads

if __name__ == '__main__':
    run_group_metric_downloads(
        base_query=FIELD_CROPS_BASE,
        metrics_dict=FIELD_CROPS_METRICS,
        skip_classifications=[],  # e.g., ["land_use"]
        group_name="FIELD CROPS"
    )