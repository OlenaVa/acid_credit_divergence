"""
model_c.py
==========
Model C -- "Realized Acid Economics". Two analyses live here now (see
model_a.py's module docstring for the same PRIMARY/SECONDARY split and why
it happened on 2026-09-16):

  PRIMARY:   run_model_c_realized_acid_economics() -- validates a narrower,
             sharper sub-hypothesis than "the thesis": does Kamoa-Kakula's
             OWN disclosed, integrated mine+smelter economics show the same
             acid-cushion narrowing the SMM index-level data shows -- and
             does its realized acid contract price actually earn a
             premium/discount to the regional benchmark ("integration
             equals a pricing edge" -- the source article calls this a
             "reasonable hypothesis... not a demonstrated one," and this
             function's own output agrees, it does not). Freeport is a
             CONTEXT cross-check here (via smelter_calibration.
             load_calibrated_params), not the primary anchor -- see the
             2026-09-16 review for why (Freeport's Miami smelter is a
             different business model from Kamoa's integrated mine-to-
             blister operation, and the source article's central empirical
             anchor is Kamoa, not Freeport).

  SECONDARY: run_model_c() / compare_a_b_c() -- the ORIGINAL "industry
             benchmark / validation layer" for the zinc-vs-copper
             cross-metal analysis: optionally overlays a PROPRIETARY data
             series (Fastmarkets, Platts, Wood Mackenzie -- supplied by the
             caller, never fetched here) on top of Model A's public-data
             run, per the original research note's A/B/C validation
             ladder (A public-only -> B robustness -> C w/ proprietary
             data). Unchanged from the prior version of this project.

IMPORTANT UNIT-BASIS WARNING (carried from copper_acid_data.py and
margin_model.py, repeated here because this is where the mistake would
actually get made): Kamoa-Kakula discloses acid credit and smelter opex
per POUND OF PAYABLE COPPER (an integrated mine+smelter basis). Freeport/
Nexa-style SmelterParams elsewhere in this project are per TONNE OF
CONCENTRATE PROCESSED (a custom-smelter basis). run_model_c_realized_acid_
economics() below never feeds Kamoa's $/lb figures through SmelterParams/
smelter_margin() -- it uses margin_model.implied_acid_yield_and_buffer(),
which is unit-agnostic by construction, precisely to avoid silently
blending the two conventions.
"""

from __future__ import annotations

from typing import Optional
import numpy as np
import pandas as pd

import copper_acid_data as cad
from margin_model import SmelterParams, implied_acid_yield_and_buffer
from model_a import run_model_a, DEFAULT_ZN_PARAMS, DEFAULT_CU_PARAMS
from thesis_monitor import MonitorConfig


def run_model_c_realized_acid_economics() -> dict:
    """
    PRIMARY. Three pieces, all built directly from copper_acid_data.py's
    cited constants (no re-fetching here):

    (1) kamoa_quarterly -- Q1/Q2 2026 cushion ratio (acid_credit_usd_lb /
        smelter_opex_usd_lb, as DISCLOSED by Ivanhoe -- not derived) and,
        where a clean realized acid price exists (Q2 only -- Q1 discloses
        only a new-contract price, not a realized weighted average, and
        this function does not paper over that gap by assuming they're
        equal), the implied acid yield / breakeven acid price / implied
        buffer via margin_model.implied_acid_yield_and_buffer().

    (2) realized_vs_benchmark -- Kamoa's Jul/Aug $840/t contract price
        against the SMM EXW DRC regional benchmark (~$935/t as of
        2026-09-04): a REAL discount (-$95/t), despite Kamoa's integrated
        mine-gate structure that should, in principle, help realize a
        premium. This directly tests, and does NOT support, the
        "integration = pricing edge" hypothesis on this one data point --
        reported exactly that way, not spun as either confirming or
        refuting the broader thesis (the source article's own framing).

    (3) freeport_cross_check -- Freeport Miami's disclosed acid_yield (via
        smelter_calibration.load_calibrated_params, concentrate-tonne
        basis) reported alongside Kamoa's implied per-lb-copper yield
        PURELY for context (they are NOT the same unit and are not
        compared numerically here -- see module docstring).
    """
    kamoa = cad.KAMOA_KAKULA_QUARTERLY
    kamoa_rows = []
    for period in ("2026-Q1", "2026-Q2", "2026-Q3"):
        d = kamoa[period]
        row = {
            "period": period,
            "smelter_opex_usd_lb": d.get("smelter_opex_usd_lb"),
            "acid_credit_usd_lb": d.get("acid_credit_usd_lb"),
            "acid_cushion_ratio": d.get("acid_cushion_ratio"),
            "realized_acid_price_usd_t": d.get("realized_acid_price_usd_t"),
            "contract_price_usd_t": d.get("contract_price_usd_t"),
        }
        if d.get("smelter_opex_usd_lb") and d.get("acid_credit_usd_lb") and d.get("realized_acid_price_usd_t"):
            buf = implied_acid_yield_and_buffer(
                acid_credit_per_unit=d["acid_credit_usd_lb"],
                opex_per_unit=d["smelter_opex_usd_lb"],
                realized_acid_price_per_t=d["realized_acid_price_usd_t"],
            )
            row.update(buf)
        else:
            row.update({"implied_acid_yield": float("nan"), "breakeven_acid_price": float("nan"),
                        "implied_buffer": float("nan")})
        kamoa_rows.append(row)
    kamoa_quarterly = pd.DataFrame(kamoa_rows).set_index("period")

    q1_to_q2_cushion_change = (
        kamoa["2026-Q2"]["acid_cushion_ratio"] - kamoa["2026-Q1"]["acid_cushion_ratio"]
    )

    drc_price = cad.REGIONAL_ACID_BENCHMARK["weekly"][-1][1]
    realized_vs_benchmark = {
        "kamoa_contract_usd_t": kamoa["2026-Q2"]["contract_price_usd_t"],
        "smm_exw_drc_benchmark_usd_t": drc_price,
        "spread_usd_t": cad.KAMOA_VS_DRC_BENCHMARK_SPREAD_USD_T,
        "reading": (
            "Kamoa's own Jul/Aug contract price sits BELOW the independent "
            "DRC benchmark despite Kamoa's integrated mine+smelter structure "
            "-- 'integration equals a pricing edge' is NOT supported by this "
            "data point. Plausible explanations (contract timing vs spot, "
            "offtake terms lagging the benchmark, internal group pricing) "
            "are not distinguishable from the data available here -- this is "
            "the source article's own caveat, carried through unchanged."
        ),
    }

    freeport_yield = None
    try:
        from smelter_calibration import load_calibrated_params
        _, cu_calibrated = load_calibrated_params("data")
        freeport_yield = cu_calibrated.acid_yield
    except Exception as e:
        print(f"NOTE: Freeport cross-check unavailable ({e}); continuing without it.")

    kamoa_q2_implied_yield = kamoa_quarterly.loc["2026-Q2", "implied_acid_yield"]
    freeport_cross_check = {
        "freeport_acid_yield_t_per_t_concentrate": freeport_yield,
        "kamoa_q2_implied_acid_yield_t_per_lb_cu": kamoa_q2_implied_yield,
        "note": (
            "Different units, different business models (custom smelter "
            "buying 3rd-party concentrate vs integrated mine-to-blister) -- "
            "reported side by side for context, never combined or compared "
            "numerically. See module docstring."
        ),
    }

    return {
        "kamoa_quarterly": kamoa_quarterly,
        "q1_to_q2_cushion_change_ppt": q1_to_q2_cushion_change,
        "realized_vs_benchmark": realized_vs_benchmark,
        "freeport_cross_check": freeport_cross_check,
    }


def run_model_c(
    df_public: pd.DataFrame,
    proprietary_acid_price: Optional[pd.Series] = None,
    proprietary_zn_tc: Optional[pd.Series] = None,
    proprietary_cu_tc: Optional[pd.Series] = None,
    zn_params: SmelterParams = DEFAULT_ZN_PARAMS,
    cu_params: SmelterParams = DEFAULT_CU_PARAMS,
    monitor_cfg: MonitorConfig = MonitorConfig(),
) -> dict:
    """SECONDARY / cross-metal. INDUSTRY BENCHMARK / VALIDATION LAYER.
    Optional by design: this only does something useful if you actually
    have access to a proprietary series (Fastmarkets zinc TC assessments,
    S&P Platts FOB China sulfuric acid, Wood Mackenzie TC/RC). It never
    REQUIRES them.

    Per the original research note's validation ladder:
        A ~ B ~ C  -> thesis is strong, doesn't depend on proprietary data
        only C works -> thesis depends on proprietary data (still a valid,
                        useful finding -- it just changes what you can claim
                        about the "public data only" version of the project)

    This module does not fetch or store any proprietary data itself -- you
    supply it as a DataFrame/Series you already have a licence to use.

    If none of the proprietary series are supplied, this is just Model A
    again (clearly labelled as such) -- it will not silently invent
    proprietary-looking numbers.
    """
    df = df_public.copy()
    used_proprietary = []

    if proprietary_acid_price is not None:
        df["acid_price"] = proprietary_acid_price.reindex(df.index).fillna(df["acid_price"])
        used_proprietary.append("acid_price")
    if proprietary_zn_tc is not None:
        df["zn_tc"] = proprietary_zn_tc.reindex(df.index).fillna(df["zn_tc"])
        used_proprietary.append("zn_tc")
    if proprietary_cu_tc is not None:
        df["cu_tc"] = proprietary_cu_tc.reindex(df.index).fillna(df["cu_tc"])
        used_proprietary.append("cu_tc")

    result = run_model_a(df, zn_params, cu_params, monitor_cfg)
    result["used_proprietary_series"] = used_proprietary
    return result


def _r(x, nd=4):
    """Round for display only -- keeps raw floats out of research-note-
    facing tables (2026-09-15 review: the un-rounded figures, e.g.
    0.17000000000000004, were showing up verbatim in printed/CSV output)."""
    return round(x, nd) if isinstance(x, (int, float)) and not isinstance(x, bool) else x


def compare_a_b_c(result_a: dict, result_b_stability: dict, result_c: dict) -> pd.DataFrame:
    """
    Builds the "does the conclusion survive A -> B -> C" summary table
    from the original research note: relative acid sensitivity and mean
    threshold gap, side by side, plus whether the thesis was ever fully
    confirmed. SECONDARY / cross-metal -- for the copper acid-cushion
    thesis's own A/B/C summary, see acid_cushion_monitor.py instead.

    IMPORTANT: the numbers in this table (and, if you're looking at
    `output/model_abc_comparison.csv`, generated by demo.py) come from
    whatever `df` was passed to run_model_a/b/c -- if that was
    demo.make_synthetic_data(), every figure here is a SYNTHETIC-fixture
    smoke-test result, not evidence about real markets. The "public data"
    in "A (core, public data)" describes the model's DATA-SOURCE
    METHODOLOGY (public vs proprietary), not whether this particular run
    used real prices. Check what `df` was before quoting any number from
    this table externally -- see real_data_check.py for the real-data path.
    """
    frac = result_b_stability.get("fraction_combinations_thesis_ever_confirmed")
    structural = result_b_stability.get("relative_acid_sensitivity_structural")
    emp_min = result_b_stability.get("relative_acid_sensitivity_empirical_min")
    emp_max = result_b_stability.get("relative_acid_sensitivity_empirical_max")
    n_combo = result_b_stability.get("n_combinations")

    rows = [
        {
            "model": "A (core, public data)",
            "relative_acid_sensitivity": _r(result_a["relative_acid_sensitivity"]),
            "threshold_gap_mean": _r(result_a["threshold_gap"].mean(), 1),
            "thesis_ever_confirmed": bool(result_a["monitor"]["thesis_confirmed"].any()),
            "note": None,
        },
        {
            "model": "B (robustness range)",
            "relative_acid_sensitivity": np.nan,  # B is a RANGE, see note
            "threshold_gap_mean": np.nan,
            "thesis_ever_confirmed": frac not in (None, 0.0),
            "note": (
                f"structural (fixed by SmelterParams.acid_yield, identical in all "
                f"{n_combo} combinations by construction -- NOT a robustness "
                f"result): {_r(structural)}. Empirical (OLS-fit per combination "
                f"on its own realized SM/acid_price series -- this IS the "
                f"robustness check): range [{_r(emp_min)}, {_r(emp_max)}]. "
                f"{(frac or 0) * 100:.0f}% of combinations ever fully confirmed the thesis."
                if frac is not None else "no combinations run"
            ),
        },
        {
            "model": f"C (industry benchmark; used: {result_c.get('used_proprietary_series') or 'none -> same as A'})",
            "relative_acid_sensitivity": _r(result_c["relative_acid_sensitivity"]),
            "threshold_gap_mean": _r(result_c["threshold_gap"].mean(), 1),
            "thesis_ever_confirmed": bool(result_c["monitor"]["thesis_confirmed"].any()),
            "note": None,
        },
    ]
    return pd.DataFrame(rows)
