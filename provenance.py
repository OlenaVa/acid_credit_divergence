"""Build quarter x field provenance matrix for real_data_check."""

from __future__ import annotations

import pandas as pd


def build_provenance_matrix(
    quarters: list[str],
    field_meta: dict[str, dict[str, str]],
) -> pd.DataFrame:
    """
    field_meta: column -> quarter -> one of cited | interpolated | invented |
    real_feed | missing | stale
    """
    rows = []
    for q in quarters:
        for field, qmap in field_meta.items():
            rows.append({
                "quarter": q,
                "field": field,
                "status": qmap.get(q, "missing"),
            })
    return pd.DataFrame(rows)
