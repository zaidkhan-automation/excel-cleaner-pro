# processors/dedupe_engine.py
# Simple fuzzy dedupe based on name-like fields and key columns.

from typing import List, Tuple
import pandas as pd
from difflib import SequenceMatcher


def similarity(a: str, b: str) -> float:
    if a is None or b is None:
        return 0.0
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()


def find_name_columns(columns: List[str]) -> List[str]:
    lower = [c.lower() for c in columns]
    res = []
    for name in ["name", "full name", "employee", "candidate", "person"]:
        for c in columns:
            if name in c.lower():
                res.append(c)
    # fallback try first column that looks like a name
    if not res and columns:
        res.append(columns[0])
    return res


def dedupe_dataframe(df: pd.DataFrame, threshold: float = 0.88) -> Tuple[pd.DataFrame, dict]:
    """
    Simple O(n^2) dedupe for demo: group rows where name similarity >= threshold.
    Keeps the first found row, aggregates indices of duplicates.
    Return new df (deduped) and issues mapping.
    """
    issues = {"duplicates_found": 0, "groups": []}
    if df.empty:
        return df, issues

    name_cols = find_name_columns(list(df.columns))
    # create a composite name key
    key_series = df[name_cols].astype(str).fillna("").agg(" ".join, axis=1).str.strip()
    used = set()
    groups = []
    keep_indices = []

    for i in range(len(df)):
        if i in used:
            continue
        group = [i]
        for j in range(i + 1, len(df)):
            if j in used:
                continue
            sim = similarity(key_series.iat[i], key_series.iat[j])
            if sim >= threshold:
                used.add(j)
                group.append(j)
        used.add(i)
        groups.append(group)
        keep_indices.append(group[0])

    deduped = df.iloc[keep_indices].reset_index(drop=True)
    issues["duplicates_found"] = sum(len(g) - 1 for g in groups)
    issues["groups"] = groups
    return deduped, issues
