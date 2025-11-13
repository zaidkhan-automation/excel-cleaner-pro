# utils.py
# Helper utilities for reading/writing files and building responses.

import io
import tempfile
import pandas as pd
from typing import Tuple, Dict, Any
from fastapi import UploadFile

ALLOWED_EXT = {"csv", "xls", "xlsx"}


def _ext_from_filename(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def validate_file(upload: UploadFile) -> None:
    ext = _ext_from_filename(upload.filename)
    if ext not in ALLOWED_EXT:
        raise ValueError(f"Unsupported file extension: {ext}")


def read_upload_to_df(upload: UploadFile) -> pd.DataFrame:
    """
    Read UploadFile to pandas DataFrame. Supports CSV/XLS/XLSX.
    """
    validate_file(upload)
    ext = _ext_from_filename(upload.filename)
    content = upload.file.read()
    if ext == "csv":
        df = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False)
    else:
        # xls / xlsx
        df = pd.read_excel(io.BytesIO(content), dtype=str, keep_default_na=False)
    # Normalize column names as strings
    df.columns = [str(c).strip() for c in df.columns]
    return df


def df_to_bytes(df: pd.DataFrame, to_format: str = "xlsx") -> Tuple[bytes, str]:
    """
    Convert DataFrame to bytes for returning in response.
    Returns (bytes, mime_type_ext)
    to_format: 'xlsx' or 'csv'
    """
    to_format = to_format.lower()
    if to_format == "csv":
        b = df.to_csv(index=False).encode("utf-8")
        return b, "csv"
    else:
        # xlsx
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        return buf.getvalue(), "xlsx"


def save_tempfile_bytes(content: bytes, suffix: str = ".xlsx") -> str:
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tf.write(content)
    tf.flush()
    tf.close()
    return tf.name


def build_summary(df_before: pd.DataFrame, df_after: pd.DataFrame, issues: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "rows_before": len(df_before),
        "rows_after": len(df_after),
        "columns_before": list(df_before.columns),
        "columns_after": list(df_after.columns),
        "issues": issues,
    }
