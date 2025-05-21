# src/agwage/utils/env.py

import os
from dotenv import load_dotenv

def load_api_key(var_name: str) -> str:
    load_dotenv()
    key = os.getenv(var_name)
    if not key:
        raise ValueError(f"{var_name} not found in .env or environment variables")
    return key
