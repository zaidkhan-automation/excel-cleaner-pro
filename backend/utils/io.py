# backend/utils/io.py
import pandas as pd
from pathlib import Path

def read_table_from_file(path):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".xls", ".xlsx"}:
        df = pd.read_excel(path, engine="openpyxl")
    elif suffix == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError("Unsupported file format")
    return df

def write_table_to_file(df, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # always fallback to csv for download
    df.to_csv(out_path, index=False)
