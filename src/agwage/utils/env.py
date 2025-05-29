# src/agwage/utils/env.py

import os
from dotenv import load_dotenv
from . import directories

def load_api_key(var_name: str) -> str:
    load_dotenv(dotenv_path=directories.PROJECT_ROOT/'.env')
    key = os.getenv(var_name)
    if not key:
        raise ValueError(f"{var_name} not found in .env or environment variables")
    return key
