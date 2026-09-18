"""
thesis_monitor.py
==================
SECONDARY / cross-metal. Five-condition MONITORING FRAMEWORK for the
zinc-vs-copper acid-credit-divergence check -- UNCHANGED from the prior
version of this project. For the PRIMARY copper acid-cushion thesis, see
thesis_dashboard.py instead: a binary "N of 5 conditions" framework is the
wrong shape for that thesis (several of its inputs -- PMI, the zinc
cross-check, the acid-market-regime question -- are evidence the source
article itself calls mixed/unclear, not pass/fail; see thesis_dashboard.
py's module docstring for the full reasoning behind the 2026-09-16 split).
Nothing below needed to change for that split -- this module was never
wrong for the narrower zinc-vs-copper question it was built for.

This is deliberately NOT a systematic trading signal, and there is no
backtest, Sharpe ratio, or walk-forward evaluation anywhere in this project
-- on purpose. A market strategist's work product is a reasoned,
periodically-updated VIEW with an explicit, falsifiable list of what would
confirm or kill it, written up for a portfolio manager or trading desk --
not a daily-rebalanced algorithm competing on risk-adjusted return. Turning
this into a backtested "long zinc / short copper" trading system would be
solving a different problem (and a quant researcher's problem, not a
strategist's) with data (monthly ILZSG/ICSG releases, quarterly filings)
that isn't even at daily frequency in its most reliable public form.

Each of the five conditions below returns a boolean SERIES so you can see
how each leg of the thesis has evolved as more data arrived. Read it as
"as of this data point, does the evidence support this leg of the
thesis" -- a strategist's checklist to walk through by hand each time new
ILZSG/ICSG/company-filing data lands, not an instruction to a trading
algorithm. `narrative_summary()` turns the latest row into the kind of
sentence that belongs in a research note.

REVIEW NOTE (2026-09-15): a stale output artifact from BEFORE this module
was renamed away from "signal.py" (an old `output/demo_signal.png`,
re-labelled "Trade-activation conditions... trade active") was found still
sitting in the project's output folder, apparently mistaken at a glance for
this module's current, correctly-labelled output. demo.py now deletes that
stale file automatically on every run -- see its _clean_stale_outputs().
Nothing in THIS module needed to change; the risk was a leftover artifact,
not a logic bug. Worth restating anyway, because it's the exact failure
this module's name and this docstring were written to prevent: read
`conditions_met` as a checklist input to a written view, never as
"trade active" / "trade inactive".
"""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass
class MonitorConfig:
    margin_window: int = 90          # lookback for margin deterioration (roughly one quarter)
    threshold_buffer: float = 0.10   # fraction of rolling |margin| median for "thin margin"
    margin_near_zero_usd: float = 50.0  # |SM| below this ($/t conc) counts as near zero
    margin_vol_window: int = 252     # rolling window for thin-margin check (daily data)
    production_window: int = 180     # lookback for utilisation/production confirmation
    stock_window: int = 180          # lookback for physical-balance confirmation
    price_zscore_window: int = 252   # lookback for "already priced in" check
    price_zscore_cap: float = 1.5    # if |z| of Zn/Cu relative price > cap, treat as priced in
    acid_star_realistic_min: float = -50.0
    acid_star_realistic_max: float = 500.0


@dataclass
class MonitorConfigQuarterly:
    """Same five conditions on quarterly-indexed series (real_data_check cadence)."""
    margin_window_quarters: int = 1
    threshold_buffer: float = 0.10
    margin_near_zero_usd: float = 50.0
    production_window_quarters: int = 1
    stock_window_quarters: int = 2
    price_zscore_window_quarters: int = 4
    price_zscore_cap: float = 1.5
    acid_star_realistic_min: float = -50.0
    acid_star_realistic_max: float = 500.0


def condition_1_margin_asymmetry(sm_zn: pd.Series, sm_cu: pd.Series, cfg: MonitorConfig) -> pd.Series:
    """Zinc margin has deteriorated by more than copper's, over cfg.margin_window."""
    d_zn = sm_zn.diff(cfg.margin_window)
    d_cu = sm_cu.diff(cfg.margin_window)
    return d_zn < d_cu


def condition_2_threshold_proximity(sm_zn: pd.Series, acid_price: pd.Series,
                                     acid_star_zn: pd.Series, cfg: MonitorConfig) -> pd.Series:
    """Near-zero zinc margin OR acid price at/below Acid* when Acid* is calibrated
    inside a realistic band (avoids false triggers when Acid* is off-model)."""
    star_ok = (
        acid_star_zn.notna()
        & (acid_star_zn >= cfg.acid_star_realistic_min)
        & (acid_star_zn <= cfg.acid_star_realistic_max)
    )
    crossed = star_ok & (acid_price <= acid_star_zn)
    rolling_median = sm_zn.abs().rolling(cfg.margin_vol_window, min_periods=2).median()
    thin_relative = sm_zn.abs() <= (cfg.threshold_buffer * rolling_median)
    thin_absolute = sm_zn.abs() <= cfg.margin_near_zero_usd
    approaching = thin_absolute | thin_relative
    return crossed | approaching


def condition_2_threshold_proximity_quarterly(
    sm_zn: pd.Series,
    acid_price: pd.Series,
    acid_star_zn: pd.Series,
    cfg: MonitorConfigQuarterly,
) -> pd.Series:
    star_ok = (
        acid_star_zn.notna()
        & (acid_star_zn >= cfg.acid_star_realistic_min)
        & (acid_star_zn <= cfg.acid_star_realistic_max)
    )
    crossed = star_ok & (acid_price <= acid_star_zn)
    rolling_median = sm_zn.abs().rolling(cfg.margin_window_quarters + 2, min_periods=2).median()
    thin_relative = sm_zn.abs() <= (cfg.threshold_buffer * rolling_median)
    thin_absolute = sm_zn.abs() <= cfg.margin_near_zero_usd
    return crossed | thin_absolute | thin_relative


def condition_3_utilisation_confirms(zn_production: pd.Series, cfg: MonitorConfig) -> pd.Series:
    """Zinc refined production / utilisation trending down over production_window --
    this is the leg that ties the margin story to something ILZSG/company
    filings can actually confirm, rather than leaving it as a modelled
    margin number nobody has checked against physical output."""
    return zn_production.diff(cfg.production_window) < 0


def condition_4_physical_tightening(zn_stocks: pd.Series, cu_stocks: pd.Series, cfg: MonitorConfig) -> pd.Series:
    """Zinc stocks drawing down relative to copper stocks (both normalised
    to their own rolling z-score first, so the comparison is of shape, not units)."""
    def z(s, w):
        return (s - s.rolling(w, min_periods=10).mean()) / s.rolling(w, min_periods=10).std()
    zz = z(zn_stocks, cfg.stock_window)
    zc = z(cu_stocks, cfg.stock_window)
    return zz.diff(cfg.stock_window) < zc.diff(cfg.stock_window)


def condition_5_not_priced_in(zn_price: pd.Series, cu_price: pd.Series, cfg: MonitorConfig) -> pd.Series:
    """Zn/Cu relative price is not already at an extreme z-score -- i.e.
    the market hasn't already run this view for you."""
    ratio = zn_price / cu_price
    mu = ratio.rolling(cfg.price_zscore_window, min_periods=30).mean()
    sd = ratio.rolling(cfg.price_zscore_window, min_periods=30).std()
    z = (ratio - mu) / sd
    return z.abs() <= cfg.price_zscore_cap


CONDITION_LABELS = {
    "c1_margin_asymmetry": "Zinc smelter margin deteriorating faster than copper's",
    "c2_threshold_proximity": "Acid price at/near the estimated zinc curtailment threshold",
    "c3_utilisation_confirms": "Zinc refined production trending down (physical confirmation)",
    "c4_physical_tightening": "Zinc stocks drawing down relative to copper",
    "c5_not_priced_in": "Zn/Cu relative price not already at an extreme",
}


def build_monitor(
    sm_zn: pd.Series, sm_cu: pd.Series,
    acid_price: pd.Series, acid_star_zn: pd.Series,
    zn_production: pd.Series,
    zn_stocks: pd.Series, cu_stocks: pd.Series,
    zn_price: pd.Series, cu_price: pd.Series,
    cfg: MonitorConfig = MonitorConfig(),
) -> pd.DataFrame:
    """Combine all five conditions into a monitoring table. `thesis_confirmed`
    (all five true) is the strongest possible read of the evidence -- in
    practice, expect a strategist to act on "how many, and which" long
    before all five ever line up at once, which is exactly why
    `conditions_met` and the per-condition columns are kept, not just the
    all-five flag."""
    c1 = condition_1_margin_asymmetry(sm_zn, sm_cu, cfg).rename("c1_margin_asymmetry")
    c2 = condition_2_threshold_proximity(sm_zn, acid_price, acid_star_zn, cfg).rename("c2_threshold_proximity")
    c3 = condition_3_utilisation_confirms(zn_production, cfg).rename("c3_utilisation_confirms")
    c4 = condition_4_physical_tightening(zn_stocks, cu_stocks, cfg).rename("c4_physical_tightening")
    c5 = condition_5_not_priced_in(zn_price, cu_price, cfg).rename("c5_not_priced_in")

    out = pd.concat([c1, c2, c3, c4, c5], axis=1)
    out["conditions_met"] = out.sum(axis=1)
    out["thesis_confirmed"] = out[[c1.name, c2.name, c3.name, c4.name, c5.name]].all(axis=1)
    return out


def conditions_met_distribution(monitor_df: pd.DataFrame) -> pd.Series:
    """
    Empirical answer to "is the AND-of-5 filter too strict, such that we'd
    miss the whole move waiting for it?" -- the distribution of how many of
    the 5 conditions were met at each point in the sample. If the count of
    5/5 is rare or zero while 3/5 and 4/5 are common, that's direct
    evidence the strict `thesis_confirmed` flag is over-conjunctive for
    this framework's actual base rates, and `conditions_met` (not the
    all-five flag) should be the primary strategist-facing output -- e.g.
    treat >=4/5 as "high conviction" and >=3/5 as "worth a fresh look",
    calibrated against how the distribution actually looks in your data,
    not against an arbitrary "all must agree" bar chosen before seeing it.
    """
    counts = monitor_df["conditions_met"].value_counts().sort_index()
    pct = (counts / len(monitor_df) * 100).round(1)
    return pd.DataFrame({"days": counts, "pct_of_sample": pct})


def narrative_summary(monitor_df: pd.DataFrame, as_of=None) -> str:
    """Render the latest (or as_of) row as research-note prose instead of a
    boolean table -- this is the format a strategist actually hands to a
    PM or a desk, not a dataframe."""
    row = monitor_df.loc[as_of] if as_of is not None else monitor_df.iloc[-1]
    date_label = str(as_of) if as_of is not None else str(monitor_df.index[-1])
    lines = [f"As of {date_label}: {int(row['conditions_met'])} of 5 confirming conditions met."]
    for col, label in CONDITION_LABELS.items():
        mark = "Yes" if bool(row[col]) else "No"
        lines.append(f"  - {label}: {mark}")
    if row["thesis_confirmed"]:
        lines.append("All five conditions align -- this is the strongest reading the framework "
                      "can give, and still not a standalone instruction to trade; check it against "
                      "current desk positioning and physical-market colour before acting on it.")
    return "\n".join(lines)
