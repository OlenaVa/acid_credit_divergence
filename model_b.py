"""
model_b.py
==========
Model B -- "Acid Price Robustness". Two analyses live here now (see
model_a.py's module docstring for the same PRIMARY/SECONDARY split and why
it happened on 2026-09-16):

  PRIMARY:   run_model_b_acid_robustness() -- does the copper acid-cushion
             reading depend on which acid-price SOURCE or which TC-index
             PROVIDER you trust? Re-runs the snapshot using SMM China's
             domestic index (primary) against the SMM EXW DRC/Zambia
             regional benchmark, and separately checks SMM's TC print
             against an independent Platts assessment near the same date.
             This is real, but SPARSE data -- only snapshot comparisons at
             dates where an alternative source actually has a print, not a
             second full time series -- and it does not always confirm the
             thesis is source-independent; see the function's docstring
             and STRATEGY_NOTE.md for a real disagreement it surfaces.

  SECONDARY: run_model_b() / run_cost_stress() -- the ORIGINAL synthetic-
             regional / cost-shock robustness check built for the
             zinc-vs-copper cross-metal analysis (demo.py's synthetic
             fixture). Unchanged from the prior version of this project.
             Per the 2026-09-16 review: synthetic regional variants don't
             actually validate anything about real regional robustness --
             they're a pipeline smoke test, not evidence. Kept for that
             narrower purpose only.

REVIEW NOTE (2026-09-15, unchanged): the previous version of run_model_b
only ever reported `out["relative_acid_sensitivity"]` (the ANALYTICAL
figure, fixed by SmelterParams.acid_yield alone) as the "robustness range"
across combinations -- that was a restatement of the input parameters, not
a robustness result. See run_model_b's own docstring below for the fix
(an empirical OLS-fit sensitivity that actually varies across combinations).
"""

from __future__ import annotations

from typing import Dict
import pandas as pd

import copper_acid_data as cad
from margin_model import (
    SmelterParams, energy_stress_test, empirical_acid_sensitivity,
    residual_margin, acid_cushion_ratio, acid_stress_test,
)
from model_a import run_model_a, DEFAULT_ZN_PARAMS, DEFAULT_CU_PARAMS, ENERGY_PRICE_USD_MWH
from thesis_monitor import MonitorConfig


def run_model_b_acid_robustness(
    weekly: pd.DataFrame,
    cu_params: SmelterParams = DEFAULT_CU_PARAMS,
    energy_price_usd_mwh: float = ENERGY_PRICE_USD_MWH,
) -> dict:
    """
    `weekly` is model_a.run_model_a_copper_acid_cushion()['weekly'] -- this
    function does not refetch data, it re-reads copper_acid_data's
    regional/cross-check constants and re-runs the SAME margin engine
    against them.

    Two SEPARATE checks, each genuinely data-limited (documented inline,
    not glossed over):

    (1) acid_price_source -- SMM China domestic (primary) vs SMM EXW DRC
        vs SMM EXW Zambia, all evaluated at the latest date the regional
        benchmark actually has a print (2026-09-04). CAVEAT: DRC/Zambia
        are a different physical market (African mine-adjacent smelters
        selling acid regionally) from the Chinese domestic smelter this
        project's TC series describes -- this is NOT "the same smelter,
        priced two ways." It answers a narrower, still useful question:
        is the ~94% cushion-ratio READING peculiar to China's domestic
        price level, or does it hold up (roughly) at a materially
        different acid price too? Below $400/t (Zambia), it does not --
        see the result and STRATEGY_NOTE.md.

    (2) tc_index_provider -- SMM's TC print vs S&P Global Platts' CIF
        China TC assessment, compared at the nearest dates both actually
        published one (SMM 2026-04-24 vs Platts 2026-04-09, 15 days
        apart -- not the same day, the closest real overlap found). Checks
        whether "TC is in extreme-negative territory" is an SMM-specific
        read or holds across index providers. It does.
    """
    latest = weekly.iloc[-1]

    # --- (1) acid price source ---------------------------------------
    drc_price, zambia_price = None, None
    for date_str, drc, zambia, status in cad.REGIONAL_ACID_BENCHMARK["weekly"]:
        if date_str == "2026-09-04":
            drc_price, zambia_price = drc, zambia
    sources = {
        "smm_china_domestic": latest["acid_usd_t"],
        "smm_exw_drc": drc_price,
        "smm_exw_zambia": zambia_price,
    }
    acid_source_rows = []
    for name, price in sources.items():
        res = residual_margin(cu_params, latest["cu_price"], latest["tc_usd_dmt"], price,
                               energy_price_usd_mwh, silver_price=latest["silver_price"])
        acid_rev = res["acid_contribution"]
        acid_source_rows.append({
            "acid_price_source": name,
            "acid_price_usd_t": price,
            "acid_contribution": acid_rev,
            "margin_ex_acid": res["margin_ex_acid"],
            "total_margin": res["total_margin"],
            "acid_cushion_ratio": acid_cushion_ratio(acid_rev, latest["tc_usd_dmt"]),
        })
    acid_price_source_df = pd.DataFrame(acid_source_rows)

    # --- (2) TC index provider -----------------------------------------
    tc_provider_rows = [
        {"provider": "SMM Imported Copper Concentrate Index (weekly)",
         "date": "2026-04-24", "tc_usd_dmt": -81.44},
        {"provider": "S&P Global Platts, CIF China clean concentrate",
         "date": "2026-04-09", "tc_usd_dmt": -78.50},
    ]
    for row in tc_provider_rows:
        res = residual_margin(cu_params, latest["cu_price"], row["tc_usd_dmt"], latest["acid_usd_t"],
                               energy_price_usd_mwh, silver_price=latest["silver_price"])
        row["margin_ex_acid"] = res["margin_ex_acid"]
        row["total_margin"] = res["total_margin"]
        row["acid_cushion_ratio"] = acid_cushion_ratio(res["acid_contribution"], row["tc_usd_dmt"])
    tc_provider_df = pd.DataFrame(tc_provider_rows)
    tc_provider_agreement_usd = abs(tc_provider_rows[0]["tc_usd_dmt"] - tc_provider_rows[1]["tc_usd_dmt"])

    return {
        "acid_price_source": acid_price_source_df,
        "tc_index_provider": tc_provider_df,
        "tc_provider_agreement_usd_dmt": tc_provider_agreement_usd,
        "caveat": (
            "acid_price_source compares markets, not the same smelter under "
            "different price feeds -- DRC/Zambia are regional export "
            "benchmarks, not what a Chinese domestic smelter actually "
            "realizes. tc_index_provider compares dates 15 days apart, the "
            "closest real overlap available, not a same-day cross-check."
        ),
    }


def run_model_b(
    df_base: pd.DataFrame,
    regional_acid_prices: Dict[str, pd.Series],
    tc_variants: Dict[str, pd.DataFrame],
    zn_params: SmelterParams = DEFAULT_ZN_PARAMS,
    cu_params: SmelterParams = DEFAULT_CU_PARAMS,
    monitor_cfg: MonitorConfig = MonitorConfig(),
) -> dict:
    """SECONDARY / cross-metal, synthetic-regional-variant robustness check
    (see module docstring). Re-runs Model A's zinc-vs-copper logic across:
      (a) several regional Chinese sulfuric-acid price series instead of one
          national number,
      (b) benchmark-vs-spot TC proxies,
    to check whether the zinc-vs-copper reading is stable across reasonable
    variation in the inputs. Feed it demo.py's synthetic fixtures for a
    pipeline smoke test, or real regional CSVs via data_loaders.
    load_regional_acid_prices if you have them.

    regional_acid_prices: {"guangxi": series, "shandong": series, ...}
    tc_variants: {"benchmark": df_with_zn_tc/cu_tc_cols, "spot": df_with_zn_tc/cu_tc_cols}

    Returns per-region x per-TC-variant results, plus a stability summary
    with TWO distinct sensitivity figures -- see module docstring for why
    they must not be conflated:
      - relative_acid_sensitivity_structural: fixed by SmelterParams.acid_yield,
        identical across every combination by construction. Reported once,
        for transparency, NOT as a range.
      - relative_acid_sensitivity_empirical_min/max: OLS-fit per combination
        on its own realized SM/acid_price series. THIS is the number that
        actually tests robustness across regional/TC variation.
    Also reports threshold_gap's min/max mean across combinations, and the
    fraction of combinations where the thesis was ever fully confirmed.
    """
    results = {}
    structural_rel_sens_values = []
    empirical_rel_sens_values = []
    gap_means = []
    any_confirmed_flags = []

    for region_name, acid_series in regional_acid_prices.items():
        for tc_name, tc_df in tc_variants.items():
            df = df_base.copy()
            df["acid_price"] = acid_series.reindex(df.index)
            df["zn_tc"] = tc_df["zn_tc"].reindex(df.index)
            df["cu_tc"] = tc_df["cu_tc"].reindex(df.index)
            df = df.dropna(subset=["acid_price", "zn_tc", "cu_tc"])
            if df.empty:
                continue

            out = run_model_a(df, zn_params, cu_params, monitor_cfg)
            key = f"{region_name}__{tc_name}"
            results[key] = out

            structural_rel_sens_values.append(out["relative_acid_sensitivity"])
            gap_means.append(out["threshold_gap"].mean())
            any_confirmed_flags.append(bool(out["monitor"]["thesis_confirmed"].any()))

            # Empirical (OLS-fit) sensitivity on THIS combination's own
            # realized SM/acid_price series -- unlike the structural figure
            # above, this genuinely differs across regions/TC variants.
            emp_zn = empirical_acid_sensitivity(out["sm_zn"], df["acid_price"])
            emp_cu = empirical_acid_sensitivity(out["sm_cu"], df["acid_price"])
            empirical_rel_sens_values.append(emp_zn - emp_cu)

    if structural_rel_sens_values:
        distinct_structural = {round(v, 10) for v in structural_rel_sens_values}
        if len(distinct_structural) > 1:
            print(
                "WARNING: relative_acid_sensitivity (structural) is NOT constant "
                "across combinations -- this should be impossible if the same "
                "SmelterParams (fixed acid_yield) were used for every "
                "combination. Check whether params were accidentally varied "
                "per-region/per-TC-variant before trusting this run."
            )

    stability = {
        "n_combinations": len(results),
        "relative_acid_sensitivity_structural": (
            structural_rel_sens_values[0] if structural_rel_sens_values else None
        ),
        "relative_acid_sensitivity_empirical_min": (
            min(empirical_rel_sens_values) if empirical_rel_sens_values else None
        ),
        "relative_acid_sensitivity_empirical_max": (
            max(empirical_rel_sens_values) if empirical_rel_sens_values else None
        ),
        "threshold_gap_mean_min": min(gap_means) if gap_means else None,
        "threshold_gap_mean_max": max(gap_means) if gap_means else None,
        "fraction_combinations_thesis_ever_confirmed": (
            sum(any_confirmed_flags) / len(any_confirmed_flags) if any_confirmed_flags else None
        ),
    }

    return {"by_combination": results, "stability": stability}


def run_cost_stress(
    df: pd.DataFrame,
    zn_params: SmelterParams = DEFAULT_ZN_PARAMS,
    cu_params: SmelterParams = DEFAULT_CU_PARAMS,
    shocks=(0.0, 0.05, 0.10, 0.20),
) -> pd.DataFrame:
    """Section-19 style: what happens to zinc vs copper margin if
    conversion + energy cost rise 5/10/20%, holding prices/TC/acid fixed
    at their LAST observation? A sensitivity table, not a forecast -- this
    is the "stress test instead of fake precision" the source note asked
    for in place of a fabricated exact energy P&L."""
    last = df.iloc[-1]
    zn = energy_stress_test(zn_params, last["zn_price"], last["zn_tc"], last["acid_price"],
                             last["energy_price"], shocks=shocks,
                             silver_price=last.get("silver_price", 0.0))
    cu = energy_stress_test(cu_params, last["cu_price"], last["cu_tc"], last["acid_price"],
                             last["energy_price"], shocks=shocks,
                             silver_price=last.get("silver_price", 0.0))
    zn = zn.rename(columns={"margin": "zn_margin"})
    cu = cu.rename(columns={"margin": "cu_margin"})
    out = zn.merge(cu, on="cost_shock")
    out["margin_gap"] = out["zn_margin"] - out["cu_margin"]
    return out
