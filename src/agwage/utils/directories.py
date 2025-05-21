from pathlib import Path

from pathlib import Path

# Root of the project (one level up from /src)
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"
# RAW_DIR = DATA_DIR / "raw"
# PROCESSED_DIR = DATA_DIR / "processed"
# TEMP_DIR = DATA_DIR / "temp"

# Outputs
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"

# Ensure directories exist
for path in [METADATA_DIR, FIGURES_DIR]:
    path.mkdir(parents=True, exist_ok=True)
