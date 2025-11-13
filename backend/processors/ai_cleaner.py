# processors/ai_cleaner.py
# Heuristic 'AI' cleaner — rules engine and column normalizer using fuzzy matching to canonical schema.

from typing import Dict, List, Tuple
import pandas as pd
from difflib import get_close_matches

CANONICAL_COLS = {
    "name": ["name", "full name", "employee name", "candidate"],
    "email": ["email", "e-mail", "email address"],
    "join_date": ["join date", "date joined", "date"],
    "salary": ["salary", "pay", "amount", "ctc"],
    "department": ["department", "dept", "team"],
    "phone": ["phone", "mobile", "contact"]
}


def map_columns_to_canonical(columns: List[str]) -> Tuple[Dict[str, str], List[str]]:
    """
    Returns mapping canonical_key -> original_column_name
    and list of remaining columns
    """
    mapping = {}
    remaining = columns.copy()
    for canon, variants in CANONICAL_COLS.items():
        # try close matches
        flat_variants = variants + [canon]
        # try best match from remaining
        matches = get_close_matches(canon, remaining, n=1, cutoff=0.6)
        if matches:
            mapping[canon] = matches[0]
            remaining.remove(matches[0])
            continue
        # try variants
        found = False
        for v in variants:
            m = get_close_matches(v, remaining, n=1, cutoff=0.6)
            if m:
                mapping[canon] = m[0]
                remaining.remove(m[0])
                found = True
                break
        if found:
            continue
    return mapping, remaining


def apply_business_rules(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Applies simple business rules:
    - Fill missing salary with 0
    - If join_date is empty but there's a 'date' or 'created' column try fill
    - Normalize department to title case
    - Create summary of corrections
    """
    issues = {}
    df2 = df.copy()

    # Salary
    salary_col = None
    for c in df2.columns:
        if "salary" in c.lower() or "amount" in c.lower() or "pay" in c.lower():
            salary_col = c
            break
    if salary_col:
        df2[salary_col] = pd.to_numeric(df2[salary_col], errors="coerce").fillna(0)
        issues["salary_filled_zero"] = int((df2[salary_col] == 0).sum())

    # Department normalization
    for c in df2.columns:
        if "dept" in c.lower() or "department" in c.lower():
            df2[c] = df2[c].astype(str).apply(lambda x: x.strip().title())
            issues["department_normalized"] = True
            break

    # Email common typo corrections
    for c in df2.columns:
        if "email" in c.lower():
            df2[c] = df2[c].astype(str).apply(lambda x: x.replace("gamil.com", "gmail.com").replace("gnail", "gmail") )
            issues["email_typos_fixed"] = True
            break

    return df2, issues
