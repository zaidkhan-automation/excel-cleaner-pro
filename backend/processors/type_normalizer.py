# processors/type_normalizer.py
# Normalize common column types: emails, dates, phone numbers, currency, and basic trimming.

import re
from typing import Tuple
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

EMAIL_RE = re.compile(r"([^@\s]+)@([^@\s]+\.[^@\s]+)")
DIGITS_RE = re.compile(r"\d+")


def normalize_email(x: str) -> str:
    if not isinstance(x, str) or x.strip() == "":
        return ""
    s = x.strip()
    # Quick cleanup common mistakes
    s = s.replace(" ", "").replace("(at)", "@").replace("[at]", "@")
    m = EMAIL_RE.search(s)
    return m.group(0).lower() if m else s.lower()


def normalize_phone(x: str) -> str:
    if not isinstance(x, str):
        return ""
    s = re.sub(r"[^\d+]", "", x)
    # keep last 10 digits if length > 10 (India use-case)
    digits = re.sub(r"[^\d]", "", s)
    if len(digits) >= 10:
        return digits[-10:]
    return digits


def normalize_currency(x: str) -> Tuple[float, str]:
    """
    Strip currency signs and return float and original symbol (if any).
    """
    if x is None or x == "":
        return 0.0, ""
    s = str(x).strip()
    # capture currency symbol(s)
    sym = "".join(re.findall(r"[^\d\.,\-\s]", s))
    clean = re.sub(r"[^\d\.\-\,]", "", s)
    # remove commas
    clean = clean.replace(",", "")
    try:
        val = float(clean)
    except Exception:
        # fallback: extract digits
        digits = "".join(re.findall(r"[\d\.]", clean))
        val = float(digits) if digits != "" else 0.0
    return val, sym


def normalize_date_series(col: pd.Series) -> pd.Series:
    # Try to coerce with pandas
    out = pd.to_datetime(col, errors="coerce", dayfirst=False)
    # Fill with original if can't parse (keep blank)
    return out.dt.strftime("%Y-%m-%d").fillna("")


def normalize_types(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Heuristic normalization:
    - If column name looks like email -> normalize_email
    - If values look like phone -> normalize_phone
    - If many currency symbols -> normalize_currency
    - If column parses to datetime -> format YYYY-MM-DD
    Returns new df and issues log
    """
    issues = {}
    df_out = df.copy()

    for col in df_out.columns:
        sample = df_out[col].astype(str).dropna().astype(str).head(50).tolist()
        sample_join = " ".join(sample).lower()
        # Email detection
        if "@" in sample_join or "email" in col.lower():
            df_out[col] = df_out[col].apply(normalize_email)
            issues[col] = "normalized_emails"
            continue

        # Date detection via pandas
        series = df_out[col]
        parsed = pd.to_datetime(series.replace("", pd.NA), errors="coerce")
        parsed_frac = parsed.notna().sum() / max(1, len(series))
        if parsed_frac > 0.4:  # many parseable => treat as dates
            df_out[col] = normalize_date_series(series)
            issues[col] = "normalized_dates"
            continue

        # Currency detection
        if re.search(r"[₹$\€£]", sample_join) or "amount" in col.lower() or "salary" in col.lower() or "amt" in col.lower():
            vals = df_out[col].astype(str).apply(lambda x: normalize_currency(x)[0])
            df_out[col] = vals
            issues[col] = "normalized_currency_to_number"
            continue

        # Phone numbers (heuristic)
        digit_counts = [len(re.sub(r"\D", "", str(x))) for x in sample if str(x).strip() != ""]
        if digit_counts and max(digit_counts) >= 8:
            df_out[col] = df_out[col].apply(normalize_phone)
            issues[col] = "normalized_phone"
            continue

        # fallback trimming whitespace
        df_out[col] = df_out[col].astype(str).apply(lambda x: x.strip() if isinstance(x, str) else x)

    return df_out, issues
