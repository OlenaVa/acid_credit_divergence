"""
Calibrate SmelterParams from hand-built company filing CSVs and sanity-check
Acid* against a realistic observed acid-price band.
"""

from __future__ import annotations

import os
from dataclasses import replace
from typing import Optional

import pandas as pd

from margin_model import SmelterParams, curtailment_threshold

# Observed China/global smelter-grade acid band used in STRATEGY_NOTE (USD/t).
ACID_PRICE_OBSERVED_MIN = 40.0
ACID_PRICE_OBSERVED_MAX = 250.0


def params_from_filing_row(row: pd.Series, metal: str) -> SmelterParams:
    """
    Build SmelterParams from one row of load_company_filing_byproducts schema.
    acid_yield = sulfuric_acid_production_kt / concentrate_processed_kt
    silver_yield_oz = (silver_sales_koz * 1000) / (concentrate_processed_kt * 1000)
    """
    conc = float(row["concentrate_processed_kt"])
    if conc <= 0:
        raise ValueError("concentrate_processed_kt must be positive")
    acid_yield = float(row["sulfuric_acid_production_kt"]) / conc
    silver_yield_oz = float(row.get("silver_sales_koz", 0) or 0) * 1000.0 / (conc * 1000.0)

    if metal == "zn":
        return SmelterParams(
            metal_grade=0.50,
            payable_fraction=0.85,
            acid_yield=round(acid_yield, 3),
            silver_yield_oz=round(silver_yield_oz, 4),
            conversion_cost=float(row.get("conversion_cost_usd_t", 195.0)),
            energy_per_t=float(row.get("energy_mwh_per_t", 0.42)),
            premium=float(row.get("premium_usd_t", 12.0)),
        )
    if metal == "cu":
        metal_grade = float(row.get("refined_metal_kt", 0)) / conc if row.get("refined_metal_kt") else 0.255
        return SmelterParams(
            metal_grade=round(metal_grade, 4),
            payable_fraction=0.96,
            acid_yield=round(acid_yield, 3),
            silver_yield_oz=round(silver_yield_oz, 4),
            gold_yield_oz=float(row.get("gold_yield_oz_per_t_conc", 0.0)),
            conversion_cost=float(row.get("conversion_cost_usd_t", 245.0)),
            energy_per_t=float(row.get("energy_mwh_per_t", 0.38)),
            premium=float(row.get("premium_usd_t", 18.0)),
        )
    raise ValueError(f"unknown metal: {metal}")


def load_calibrated_params(data_dir: str) -> tuple[SmelterParams, SmelterParams]:
    """
    Load Nexa / Freeport filing CSVs from data_dir if present; otherwise fall
    back to filing-derived defaults shipped in those CSV files.

    PROVENANCE FLAG (added 2026-09-25, nothing computed here changed): the
    Freeport CSV's figures (data/freeport_copper_byproducts.csv) look like
    genuine transcribed 10-K figures -- not round, differ year to year. The
    Nexa CSV (data/nexa_zinc_byproducts.csv) does NOT clear that bar: in
    BOTH years it carries, `sulfuric_acid_production_kt` is set EXACTLY
    equal to `concentrate_processed_kt` (4,200 = 4,200 in 2024; 4,100 =
    4,100 in 2025), which forces acid_yield = 1.000 t acid/t concentrate --
    precisely equal to the independent, differently-sourced AusIMM-based
    rule-of-thumb already used elsewhere for DEFAULT_ZN_PARAMS.acid_yield
    (see model_a.py). Two independently-derived company-specific figures
    landing on the exact same round number is the signature of a filler
    fixture that never got replaced with Nexa's real 20-F/6-K figures, not
    of independent confirmation. The zinc half of this function's return
    value is UNVERIFIED for that reason -- it is not currently used to
    inform any headline output (model_c.py only reads the copper half),
    but do not start using it for zinc without first replacing this CSV
    with real transcribed Nexa filing figures.
    """
    from data_loaders import load_company_filing_byproducts

    zn_path = os.path.join(data_dir, "nexa_zinc_byproducts.csv")
    cu_path = os.path.join(data_dir, "freeport_copper_byproducts.csv")
    zn_df = load_company_filing_byproducts(zn_path, "Nexa")
    cu_df = load_company_filing_byproducts(cu_path, "Freeport")
    zn_row = zn_df.sort_values("period").iloc[-1]
    cu_row = cu_df.sort_values("period").iloc[-1]
    if float(zn_row["sulfuric_acid_production_kt"]) == float(zn_row["concentrate_processed_kt"]):
        print(
            "WARNING: nexa_zinc_byproducts.csv gives acid_yield == 1.000 exactly "
            "(sulfuric_acid_production_kt == concentrate_processed_kt) -- this is "
            "the known-unverified placeholder flagged in this function's "
            "docstring, not confirmed Nexa filing data."
        )
    return params_from_filing_row(zn_row, "zn"), params_from_filing_row(cu_row, "cu")


def acid_star_sanity(
        params: SmelterParams,
        metal_price: float,
        tc: float,
        energy_price: float,
        silver_price: float = 0.0,
        gold_price: float = 0.0,
        acid_bounds=(-6000.0, 6000.0),
) -> dict:
    """Report whether Acid* sits inside the observed acid band (calibration flag)."""
    acid_star = curtailment_threshold(
        params, metal_price, tc, energy_price, silver_price, gold_price, acid_bounds=acid_bounds
    )
    if acid_star is None:
        flag = "no_root_in_bounds"
        in_band = False
    else:
        in_band = ACID_PRICE_OBSERVED_MIN <= acid_star <= ACID_PRICE_OBSERVED_MAX
        flag = "ok" if in_band else "out_of_observed_band"
    return {
        "acid_star": acid_star,
        "in_observed_band": in_band,
        "flag": flag,
        "observed_band": (ACID_PRICE_OBSERVED_MIN, ACID_PRICE_OBSERVED_MAX),
    }


def sanity_table_for_df(
        params: SmelterParams,
        df: pd.DataFrame,
        metal_prefix: str,
) -> pd.DataFrame:
    """One row per quarter: Acid* and calibration flag."""
    rows = []
    price_col = f"{metal_prefix}_price"
    tc_col = f"{metal_prefix}_tc"
    for idx, r in df.iterrows():
        if pd.isna(r.get(price_col)) or pd.isna(r.get(tc_col)):
            continue
        rep = acid_star_sanity(
            params,
            float(r[price_col]),
            float(r[tc_col]),
            float(r.get("energy_price", 0)),
            float(r.get("silver_price", 0)),
            float(r.get("gold_price", 0)),
        )
        rows.append({"quarter": idx, "metal": metal_prefix, **rep})
    return pd.DataFrame(rows)