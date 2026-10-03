"""
model_a.py
==========
Model A -- "Acid Cushion". Two analyses live here now, per the 2026-09-16
review of the source article ("Copper's Hidden Margin: When the Acid
Cushion Starts Shrinking"):

  PRIMARY:   run_model_a_copper_acid_cushion() -- copper only, real weekly
             SMM TC + acid data (copper_acid_data.py), answering the
             article's actual question: how much of the negative TC is
             currently being absorbed by acid revenue, and what happens if
             acid keeps falling while TC stays where it is? This is now
             the project's headline output -- see acid_cushion_monitor.py.

  SECONDARY: run_model_a() -- the ORIGINAL zinc-vs-copper cross-metal
             check (unchanged from the prior version of this project).
             Kept as supporting/corroborating evidence ("zinc shows the
             same pressure," per the source article) -- it is deliberately
             NOT allowed to move `thesis_confirmed` for the copper
             acid-cushion thesis; see thesis_dashboard.py.

Both share the same smelter_margin() engine in margin_model.py. Public
data only; nothing here is fit to secret data.
"""

from __future__ import annotations

import pandas as pd

import copper_acid_data as cad
from data_loaders import load_daily_metal_prices
from margin_model import (
    SmelterParams, smelter_margin, acid_sensitivity,
    relative_acid_sensitivity, curtailment_threshold,
    acid_revenue_only, acid_cushion_ratio, cushion_loss,
    residual_margin, acid_stress_test, acid_yield_sensitivity,
)
from thesis_monitor import MonitorConfig, build_monitor

# Representative-smelter parameters. UPGRADED FROM PURE PLACEHOLDERS on
# review: acid_yield and copper's metal_grade are now grounded in cited
# figures, not invented -- everything else here is still a rule-of-thumb
# or unsourced, and is labelled as such. See the earlier strategy note for the full
# calibration-confidence breakdown.
#
#   acid_yield (t acid / t CONCENTRATE) -- derived, not invented:
#     zinc: ~2.0 t acid per t of zinc METAL is a standard industry figure
#       ("the production of sulfuric acid is a significant adjunct to zinc
#       smelting with around two tonnes of acid produced for each tonne of
#       metal" -- AusIMM, "A century of zinc production"). Converted to a
#       per-concentrate-tonne basis via metal_grade: 2.0 * 0.50 = 1.0.
#       This REPLACES an earlier invented placeholder of 0.60 -- the old
#       number understated zinc's acid channel by roughly 40%.
#     copper: 3.0-3.5 t acid per t of refined copper is a cited 2026
#       industry range (discoveryalert.com.au, Feb 2026; SunSirs
#       independently cites "3-4 tons per ton of copper" for context).
#       Midpoint 3.25 * metal_grade 0.255 = 0.83 -- close to the old
#       invented placeholder (0.85), so that one happened to be roughly
#       right, which is worth saying plainly rather than only reporting
#       the correction that changed something. NOTE this 3-4 t/t figure
#       is a CONCENTRATE-SMELTER (Freeport/Nexa-style) yield -- it is NOT
#       directly comparable to Kamoa-Kakula's disclosed per-lb-copper
#       figures in copper_acid_data.KAMOA_KAKULA_QUARTERLY, which come
#       from an integrated mine+smelter with a different acid/copper
#       ratio (implied ~1.8-1.9 t/t in Q2 2026 -- see model_c.py). Both
#       are kept as SEPARATE, differently-labelled numbers rather than
#       forced into one "the" acid yield.
#   metal_grade (t payable metal / t concentrate):
#     zinc: 0.50 is a standard textbook zinc-concentrate assay (~50-55%
#       Zn), not a specific company figure -- still a rule of thumb.
#     copper: 0.255 is REAL, not a rule of thumb -- Freeport's Miami
#       smelter processed 821.2 kt copper concentrate and produced 209.3
#       kt copper anode in 2025 (Freeport 10-K), 209.3/821.2 = 0.255.
#       Replaces an earlier invented 0.28.
#   payable_fraction, silver_yield_oz, gold_yield_oz, conversion_cost,
#   energy_per_t, premium: STILL uncalibrated rule-of-thumb or invented
#   placeholders -- calibrate from Nexa's 20-F/6-K and Freeport's 10-K via
#   data_loaders.load_company_filing_byproducts before trusting these.
#
# REVIEW NOTE (2026-09-15): because acid_sensitivity()/relative_acid_
# sensitivity() below depend ONLY on acid_yield (not on any price/TC/acid
# data), the 0.17 figure this produces is fixed by these two constants
# alone. That is fine as a *structural* number -- but it means it can
# never serve as a robustness check across Model B's regional/TC
# variants (they don't touch acid_yield at all). Model B now also reports
# an *empirical* (OLS-fit) version of this sensitivity, computed on each
# combination's own realized margin/acid-price series, which CAN vary --
# see model_b.py and the earlier README's changelog.
DEFAULT_ZN_PARAMS = SmelterParams(
    metal_grade=0.50, payable_fraction=0.85, acid_yield=1.00,
    silver_yield_oz=0.15, conversion_cost=220.0, energy_per_t=0.35, premium=15.0,
)
DEFAULT_CU_PARAMS = SmelterParams(
    metal_grade=0.255, payable_fraction=0.96, acid_yield=0.83,
    # gold_yield_oz is a placeholder: NO gold price is loaded, so gold contributes 0. Deliberately left that way --
    # 0.002 oz/t x any plausible gold price (<= $6,000/oz) is < $12/t of concentrate, it moves only the uncalibrated
    # margin LEVEL, never the cushion ratio (acid credit / |TC|), and over any window its change is ~$1/t.
    silver_yield_oz=0.05, gold_yield_oz=0.002, conversion_cost=260.0,
    energy_per_t=0.40, premium=20.0,
)

# Placeholder flat industrial-electricity price ($/MWh-equivalent unit
# matching SmelterParams.energy_per_t) -- STILL UNCALIBRATED. No free
# public daily/weekly industrial-electricity series for Chinese copper
# smelters was found for this project (see data_loaders.py's source
# table); this is a rule-of-thumb constant, not a fetched series. At the
# DEFAULT_CU_PARAMS energy intensity it is $28/t concentrate (0.40 MWh x
# $70). That is small next to the TC and acid legs that drive the cushion
# ratio (the ratio itself does not use energy at all). It is material next
# to the uncalibrated conversion-cost assumption ($260/t), which is why
# absolute treatment-margin levels are not reported.
ENERGY_PRICE_USD_MWH = 70.0


def _pct_change_over(series: pd.Series, weeks: int) -> float:
    """% change from `weeks` steps ago to the latest point in `series`
    (both assumed to be on the same weekly grid). NaN if there isn't
    enough history."""
    if len(series) <= weeks or series.iloc[-1 - weeks] == 0 or pd.isna(series.iloc[-1 - weeks]):
        return float("nan")
    return series.iloc[-1] / series.iloc[-1 - weeks] - 1


def _status_at(status_series: pd.Series, weeks: int) -> str:
    """Status ('cited' / 'cited-approx' / 'interpolated (grid-fill)') of
    the comparison point `weeks` steps back. The LATEST point in every
    trend metric is expected to be a cited print (enforced in
    copper_acid_data.py), but the other end of a %/level change is not
    guaranteed to be. Do not hard-code which week that is -- it moves as
    the grid extends."""
    if len(status_series) <= weeks:
        return "n/a"
    return status_series.iloc[-1 - weeks]


def _level_change_over(series: pd.Series, weeks: int) -> float:
    """Level (not %) change over `weeks` steps -- used for the Acid
    Cushion Ratio panel, which is already a ratio and reads more naturally
    as a percentage-point change than as a % change of a %."""
    if len(series) <= weeks:
        return float("nan")
    return series.iloc[-1] - series.iloc[-1 - weeks]


def run_model_a_copper_acid_cushion(
        cu_params: SmelterParams = DEFAULT_CU_PARAMS,
        energy_price_usd_mwh: float = ENERGY_PRICE_USD_MWH,
        metal_prices_path: str = "data/metal_prices.csv",
) -> dict:
    """
    THE core analysis, per the 2026-09-16 review: copper only, real weekly
    SMM TC + acid data, answering "how much of the negative TC is
    currently being absorbed by acid revenue, and what happens if acid
    keeps falling?"

    Builds a weekly DataFrame (Friday cadence, matching the SMM indices'
    own publication cadence) from:
        - copper_acid_data.cu_tc_weekly_interpolated()   (TC, USD/dmt)
        - copper_acid_data.cu_acid_weekly_interpolated() (acid, RMB/t,
          converted to USD via the period-matched FX table)
        - the real daily copper price in data/metal_prices.csv, reindexed
          to the same Friday grid (forward-filled from the nearest prior
          trading day -- copper trades most days; the SMM indices do not,
          so the SMM grid, not the price grid, sets the cadence here)

    then runs smelter_margin / residual_margin / acid_cushion_ratio /
    cushion_loss across the whole series, and acid_stress_test at the
    latest observation.

    Raises MissingDataError (via load_daily_metal_prices returning empty)
    with a clear message if data/metal_prices.csv hasn't been fetched
    locally yet -- this function does not fall back to a synthetic price,
    unlike demo.py, because a "real data" pipeline that silently runs on
    invented numbers is exactly the failure mode this project's provenance
    discipline exists to prevent.
    """
    tc = cad.cu_tc_weekly_interpolated()["tc_usd_dmt"]
    tc_status = cad.cu_tc_weekly_interpolated()["status"]
    acid_cny = cad.cu_acid_weekly_interpolated()["acid_cny_t"]
    acid_status = cad.cu_acid_weekly_interpolated()["status"]
    # The SMM national RMB acid index is (by SMM's convention) quoted INCLUDING 13% VAT; VAT is not smelter revenue,
    # so the model converts the ex-VAT price. `acid_usd_t_quoted` keeps the as-quoted conversion for sensitivities.
    _vat = cad.ACID_QUOTE_BASIS["vat_rate_cn"]
    acid_usd = pd.Series(
        [cad.cny_to_usd_by_date(v / (1.0 + _vat), d) for d, v in acid_cny.items()],
        index=acid_cny.index, name="acid_usd_t",
    )
    acid_usd_quoted = pd.Series(
        [cad.cny_to_usd_by_date(v, d) for d, v in acid_cny.items()],
        index=acid_cny.index, name="acid_usd_t_quoted",
    )

    prices = load_daily_metal_prices(metal_prices_path)
    if prices.empty or "cu_price" not in prices.columns:
        raise FileNotFoundError(
            f"'{metal_prices_path}' not found or missing 'cu_price' -- run "
            "fetch_metal_prices_yfinance.py locally first (see README.md). "
            "This pipeline does not fall back to a synthetic price."
        )
    cu_price = prices["cu_price"].reindex(
        prices["cu_price"].index.union(tc.index)
    ).ffill().reindex(tc.index)
    silver_price = prices.get("silver_price", pd.Series(0.0, index=tc.index)).reindex(
        prices.index.union(tc.index)
    ).ffill().reindex(tc.index) if "silver_price" in prices.columns else pd.Series(0.0, index=tc.index)

    weekly = pd.DataFrame({
        "tc_usd_dmt": tc,
        "tc_status": tc_status,
        "acid_cny_t": acid_cny,
        "acid_usd_t": acid_usd,
        "acid_usd_t_quoted": acid_usd_quoted,
        "acid_status": acid_status,
        "cu_price": cu_price,
        "silver_price": silver_price,
    })

    res = residual_margin(
        cu_params, weekly["cu_price"], weekly["tc_usd_dmt"], weekly["acid_usd_t"],
        energy_price_usd_mwh, silver_price=weekly["silver_price"],
    )
    weekly["margin_ex_acid"] = res["margin_ex_acid"]
    weekly["acid_contribution"] = res["acid_contribution"]
    weekly["total_margin"] = res["total_margin"]
    weekly["acid_cushion_ratio"] = acid_cushion_ratio(weekly["acid_contribution"], weekly["tc_usd_dmt"])
    weekly["cushion_loss_9w"] = cushion_loss(weekly["acid_cushion_ratio"], periods=9)
    weekly["cushion_loss_13w"] = cushion_loss(weekly["acid_cushion_ratio"], periods=13)

    latest = weekly.iloc[-1]
    stress = acid_stress_test(
        cu_params, latest["cu_price"], latest["tc_usd_dmt"], latest["acid_usd_t"],
        energy_price_usd_mwh, shocks=(0.0, -0.10, -0.20, -0.30),
        silver_price=latest["silver_price"],
    )
    yield_sensitivity = acid_yield_sensitivity(
        cu_params, latest["cu_price"], latest["tc_usd_dmt"], latest["acid_usd_t"],
        energy_price_usd_mwh, silver_price=latest["silver_price"],
    )

    trend = {
        "acid_price_1m_pct": _pct_change_over(weekly["acid_usd_t"], 4),
        "acid_price_3m_pct": _pct_change_over(weekly["acid_usd_t"], 13),
        "acid_price_9w_pct": _pct_change_over(weekly["acid_usd_t"], 9),
        "cushion_9w_ppt": _level_change_over(weekly["acid_cushion_ratio"], 9),
        "cushion_13w_ppt": _level_change_over(weekly["acid_cushion_ratio"], 13),
        # TC deliberately reported as a LEVEL change ($/dmt), not a %
        # change: TC is negative throughout this series, and "% change of
        # a negative number" flips sign in a way that reads backwards
        # (TC getting MORE negative would print as a misleading "+X%").
        "tc_1m_usd_dmt_change": _level_change_over(weekly["tc_usd_dmt"], 4),
        "tc_9w_usd_dmt_change": _level_change_over(weekly["tc_usd_dmt"], 9),
    }
    # Basis of the REFERENCE point ("weeks ago") for each trend figure
    # above -- see _status_at()'s docstring. The latest point is always
    # "cited" for every metric (that property is what copper_acid_data.py's
    # own self-check enforces), so only the older end needs disclosing.
    trend_basis = {
        "acid_price_1m_pct": _status_at(weekly["acid_status"], 4),
        "acid_price_3m_pct": _status_at(weekly["acid_status"], 13),
        "acid_price_9w_pct": _status_at(weekly["acid_status"], 9),
        "cushion_9w_ppt": (_status_at(weekly["acid_status"], 9), _status_at(weekly["tc_status"], 9)),
        "cushion_13w_ppt": (_status_at(weekly["acid_status"], 13), _status_at(weekly["tc_status"], 13)),
        "tc_1m_usd_dmt_change": _status_at(weekly["tc_status"], 4),
        "tc_9w_usd_dmt_change": _status_at(weekly["tc_status"], 9),
    }
    flagged = [k for k, v in trend_basis.items() if "interpolated" in str(v)]
    if flagged:
        provenance_note = (
            "Some trend figures compare the latest cited week against a reference week that is interpolated: "
            f"{', '.join(flagged)}. Direction and rough magnitude are meaningful; the last significant figure is not."
        )
    else:
        provenance_note = "All trend reference points currently land on cited or cited-approx SMM prints (no interpolated reference week)."

    return {
        "weekly": weekly,
        "latest": latest,
        "stress": stress,
        "yield_sensitivity": yield_sensitivity,
        "trend": trend,
        "trend_basis": trend_basis,
        "provenance_note": provenance_note,
        "params": cu_params,
        "energy_price_usd_mwh": energy_price_usd_mwh,
    }


def run_model_a(
        df: pd.DataFrame,
        zn_params: SmelterParams = DEFAULT_ZN_PARAMS,
        cu_params: SmelterParams = DEFAULT_CU_PARAMS,
        monitor_cfg: MonitorConfig = MonitorConfig(),
) -> dict:
    """SECONDARY / cross-metal confirmation only (see module docstring).
    Returns a dict with the full margin/threshold/monitoring time series
    plus summary sensitivity figures, so it can be printed, plotted, or
    handed straight to model_b/model_c for robustness/validation."""

    sm_zn = smelter_margin(zn_params, df["zn_price"], df["zn_tc"], df["acid_price"],
                           df["energy_price"], silver_price=df.get("silver_price", 0.0))
    sm_cu = smelter_margin(cu_params, df["cu_price"], df["cu_tc"], df["acid_price"],
                           df["energy_price"], silver_price=df.get("silver_price", 0.0))

    sens_zn = acid_sensitivity(zn_params)
    sens_cu = acid_sensitivity(cu_params)
    rel_sens = relative_acid_sensitivity(zn_params, cu_params)

    acid_star_zn = df.apply(
        lambda r: curtailment_threshold(zn_params, r["zn_price"], r["zn_tc"], r["energy_price"],
                                        silver_price=r.get("silver_price", 0.0)),
        axis=1,
    )
    acid_star_cu = df.apply(
        lambda r: curtailment_threshold(cu_params, r["cu_price"], r["cu_tc"], r["energy_price"],
                                        silver_price=r.get("silver_price", 0.0)),
        axis=1,
    )
    gap = acid_star_zn - acid_star_cu

    monitor = build_monitor(
        sm_zn, sm_cu, df["acid_price"], acid_star_zn,
        df["zn_production"], df["zn_stocks"], df["cu_stocks"],
        df["zn_price"], df["cu_price"], cfg=monitor_cfg,
    )

    return {
        "sm_zn": sm_zn, "sm_cu": sm_cu,
        "acid_sensitivity_zn": sens_zn, "acid_sensitivity_cu": sens_cu,
        "relative_acid_sensitivity": rel_sens,
        "acid_star_zn": acid_star_zn, "acid_star_cu": acid_star_cu,
        "threshold_gap": gap,
        "monitor": monitor,
    }