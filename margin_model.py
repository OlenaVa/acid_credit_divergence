"""
margin_model.py
================
Core "representative smelter" margin engine for the Acid-Credit Divergence
project (zinc vs copper).

Implements, per the research note:

    SM_m,t = MetalRevenue + ByproductRevenue + TCBenefit + Premium
             - EnergyCost - ConversionCost

on a PER TONNE OF CONCENTRATE PROCESSED basis (this is the natural unit,
since TC/RC, acid yield and conversion cost are all quoted per tonne of
concentrate in industry disclosures such as Nexa's 20-F and Freeport's 10-K).

Nothing here is fit to secret data — every coefficient is a named,
overridable parameter so you can calibrate it yourself from public filings
(Nexa 20-F / 6-K, Freeport 10-K, USGS, ILZSG/ICSG) instead of trusting a
hard-coded number.

REVIEW NOTE (2026-09-15): threshold_gap()'s docstring previously described
the sign convention BACKWARDS ("positive => zinc curtails later" -- it's
the opposite; see the corrected docstring below and _selfcheck_threshold_
gap_sign() for a runnable proof). The underlying arithmetic
(`acid_star_zn - acid_star_cu`) was never wrong, and the +1441.98 figure
you may have seen out of demo.py's synthetic run is directionally
CONSISTENT with the original long-zinc/short-copper thesis once read
correctly -- only the prose explanation needed fixing, but it needed
fixing before it went into a written research note.

REVIEW NOTE (2026-09-16): this module now backs TWO analyses, not one:
  1. PRIMARY -- the copper acid-cushion thesis (model_a.py's
     run_model_a_copper_acid_cushion, model_c.py, acid_cushion_monitor.py),
     using acid_cushion_ratio() / cushion_loss() / residual_margin() /
     acid_stress_test() below, fed by copper_acid_data.py's real weekly
     SMM data.
  2. SECONDARY -- the original zinc-vs-copper cross-metal check
     (model_a.run_model_a / model_b / model_c's legacy paths, real_data_
     check.py), kept for cross-metal confirmation but no longer the
     central test -- see the earlier README's 2026-09-16 changelog entry for why.
Both share this same smelter_margin() engine; nothing about the core
formula changed, only which outputs are treated as the headline result.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional
import numpy as np
import pandas as pd
from scipy.optimize import brentq


@dataclass
class SmelterParams:
    """
    Representative smelter parameters for one metal.

    All "yield" parameters are expressed per tonne of concentrate processed.
    Defaults are ROUGH, ORDER-OF-MAGNITUDE placeholders inspired by the
    ranges discussed in Nexa / Freeport / IEA disclosures referenced in the
    research note -- treat them as a starting point to calibrate, not ground
    truth. Always override with numbers you can source and cite.
    """

    metal_grade: float            # tonnes payable metal per tonne concentrate (e.g. ~0.50 for zinc conc.)
    payable_fraction: float       # fraction of contained metal that is payable (e.g. 0.85)
    acid_yield: float             # tonnes of sulfuric acid produced per tonne concentrate
    silver_yield_oz: float = 0.0  # troy oz silver recovered per tonne concentrate
    gold_yield_oz: float = 0.0    # troy oz gold recovered per tonne concentrate (copper only, usually)
    conversion_cost: float = 0.0  # $/t concentrate, non-energy opex (labour, maintenance, consumables)
    energy_per_t: float = 0.0     # energy units (e.g. MWh-equivalent) consumed per tonne concentrate
    premium: float = 0.0          # $/t concentrate, metal premium (regional physical premium, payable basis)

    def metal_revenue(self, metal_price: pd.Series | float) -> pd.Series | float:
        return metal_price * self.metal_grade * self.payable_fraction

    def byproduct_revenue(
            self,
            acid_price: pd.Series | float,
            silver_price: pd.Series | float = 0.0,
            gold_price: pd.Series | float = 0.0,
    ) -> pd.Series | float:
        return (
                self.acid_yield * acid_price
                + self.silver_yield_oz * silver_price
                + self.gold_yield_oz * gold_price
        )

    def energy_cost(self, energy_price: pd.Series | float) -> pd.Series | float:
        return self.energy_per_t * energy_price


def smelter_margin(
        params: SmelterParams,
        metal_price,
        tc,                     # $/t concentrate, sign convention: POSITIVE = smelter is PAID (normal regime)
        acid_price,
        energy_price,
        silver_price=0.0,
        gold_price=0.0,
) -> pd.Series | float:
    """
    SM = MetalRevenue + ByproductRevenue + TCBenefit + Premium
         - EnergyCost - ConversionCost

    Note on TC sign convention: in this module TC is entered as the fee the
    SMELTER receives (i.e. a normal positive TC of +$80/t is a REVENUE of
    $80/t; the 2026 regime described in the note, where spot TCs go
    negative, is simply tc < 0, which correctly turns TCBenefit into a cost).
    """
    metal_rev = params.metal_revenue(metal_price)
    byprod_rev = params.byproduct_revenue(acid_price, silver_price, gold_price)
    tc_benefit = tc
    energy_cost = params.energy_cost(energy_price)

    return (
            metal_rev
            + byprod_rev
            + tc_benefit
            + params.premium
            - energy_cost
            - params.conversion_cost
    )


def acid_sensitivity(params: SmelterParams) -> float:
    """
    dSM/dAcidPrice. In this linear specification it is simply the acid
    yield coefficient -- but exposed as a function (rather than inlined)
    so Model B can swap in a numerically-estimated (regression) sensitivity
    when the relationship is not assumed linear.

    IMPORTANT (2026-09-15 review): because this returns `params.acid_yield`
    and NOTHING else, it is entirely independent of any price/TC/acid data
    series. Sweeping regional acid-price series or TC variants (as
    model_b.run_model_b does) will NEVER change this number -- it is fixed
    the moment SmelterParams is constructed. Do not report a "range" of
    this value across data variants as if it were a robustness check; use
    `empirical_acid_sensitivity()` below for that instead (model_b.py now
    does both, clearly labelled).
    """
    return params.acid_yield


def relative_acid_sensitivity(params_zn: SmelterParams, params_cu: SmelterParams) -> float:
    """RelativeAcidSensitivity = AcidSensitivity_Zn - AcidSensitivity_Cu.
    Structural number only -- see acid_sensitivity()'s note above."""
    return acid_sensitivity(params_zn) - acid_sensitivity(params_cu)


def empirical_acid_sensitivity(sm_series: pd.Series, acid_price_series: pd.Series) -> float:
    """
    Numerically-estimated dSM/dAcidPrice via simple OLS slope, for use when
    you have an actual observed margin & acid-price history (Model B / C)
    rather than trusting the linear-by-construction analytical figure.

    This is the function that actually tests something about the DATA --
    unlike acid_sensitivity() above, its result depends on whatever
    sm_series/acid_price_series you pass in, so it genuinely can (and, per
    the 2026-09-15 review of model_b.py, now does) vary across regions and
    TC variants.
    """
    df = pd.concat([sm_series, acid_price_series], axis=1).dropna()
    if len(df) < 3:
        return float("nan")
    x = df.iloc[:, 1].values
    y = df.iloc[:, 0].values
    slope = np.polyfit(x, y, 1)[0]
    return float(slope)


def curtailment_threshold(
        params: SmelterParams,
        metal_price,
        tc,
        energy_price,
        silver_price=0.0,
        gold_price=0.0,
        acid_bounds=(-6000.0, 6000.0),
) -> Optional[float]:
    """
    Solve SM(acid_price) = 0 for acid_price, holding everything else fixed
    at a single point-in-time snapshot. Returns Acid* -- the estimated
    sulfuric-acid price at which the representative smelter hits zero
    margin, or None if no root exists in `acid_bounds` (i.e. the smelter is
    already underwater / always profitable within the bracket, given the
    other inputs).

    Root-finding (rather than the closed-form linear solution) is used
    deliberately: it keeps this function correct even if you later replace
    SmelterParams' cost functions with something non-linear (e.g. a
    stepped energy-tariff schedule).

    CALIBRATION SANITY CHECK (2026-09-15 review): with the current
    DEFAULT_ZN_PARAMS/DEFAULT_CU_PARAMS, Acid* tends to come out far
    outside any realistic observed acid price (demo.py's synthetic run
    produces roughly -1000 to -2600 $/t, versus a real observed range of
    roughly $40-205/t per the earlier strategy note). That does not make the
    function wrong -- it is an honest signal that condition_2's "acid
    price has crossed Acid*" branch in thesis_monitor.py is close to
    unreachable until SmelterParams' still-uncalibrated fields
    (payable_fraction, conversion_cost, energy_per_t, premium) are
    tightened from real filings. Treat a deeply-out-of-range Acid* as a
    calibration flag, not a finding.
    """

    def f(acid_price):
        return smelter_margin(
            params, metal_price, tc, acid_price, energy_price, silver_price, gold_price
        )

    lo, hi = acid_bounds
    f_lo, f_hi = f(lo), f(hi)
    if np.sign(f_lo) == np.sign(f_hi):
        return None
    return float(brentq(f, lo, hi))


def threshold_gap(acid_star_zn: Optional[float], acid_star_cu: Optional[float]) -> Optional[float]:
    """ThresholdGap = Acid*_Zn - Acid*_Cu.

    SIGN CONVENTION (corrected 2026-09-15 -- the previous version of this
    docstring had this backwards; see _selfcheck_threshold_gap_sign()
    below for a runnable proof, and the earlier README's changelog for the full
    account):

    Acid* is the acid price at which SM(acid_price) = 0, holding
    everything else fixed. A HIGHER (less negative) Acid* means the
    smelter needs only a SMALL decline in the acid price to hit zero
    margin -- i.e. it is MORE exposed to the acid channel and curtails
    SOONER. A LOWER (more negative) Acid* means the smelter could absorb a
    much larger acid-price decline before curtailing -- i.e. it is MORE
    resilient and curtails LATER (in practice, often effectively never via
    the acid channel alone, since a deeply negative Acid* sits far outside
    any realistic acid price).

    So: POSITIVE threshold_gap (Acid*_Zn > Acid*_Cu) => zinc's curtailment
    trigger sits at a HIGHER acid price than copper's => ZINC is the MORE
    exposed / EARLIER-curtailing metal via the acid channel, all else
    equal. NEGATIVE => the reverse.

    Do not paraphrase this as "[metal] can tolerate a lower acid price"
    without re-deriving which metal that phrase actually describes -- it
    is easy to invert by accident (this function's own docstring did,
    until this correction). State the conclusion in terms of "which
    Acid* is higher", not in terms of "tolerating low prices", in any
    research-note prose.
    """
    if acid_star_zn is None or acid_star_cu is None:
        return None
    return acid_star_zn - acid_star_cu


def _selfcheck_threshold_gap_sign() -> None:
    """Runnable proof of the sign convention documented above, so it's
    locked in by execution rather than by prose alone. Builds two smelters
    that differ ONLY in their non-acid margin (same acid_yield for both,
    to isolate the effect), confirms the one with the THINNER non-acid
    margin ('fragile') gets the HIGHER (less negative) Acid*, and confirms
    threshold_gap correctly reports a POSITIVE gap when the fragile one is
    passed first. Run directly: `python margin_model.py`."""
    resilient = SmelterParams(metal_grade=0.5, payable_fraction=0.85, acid_yield=0.5,
                              conversion_cost=200.0, premium=0.0)
    fragile = SmelterParams(metal_grade=0.5, payable_fraction=0.85, acid_yield=0.5,
                            conversion_cost=200.0, premium=0.0)
    # 'resilient' gets a high metal price and a positive TC (big non-acid
    # margin); 'fragile' gets a much lower metal price and a negative TC
    # (thin non-acid margin) -- acid_yield is identical for both, so any
    # difference in Acid* below is attributable purely to the non-acid
    # margin gap, not to acid exposure itself.
    acid_star_resilient = curtailment_threshold(resilient, metal_price=3000, tc=50, energy_price=70)
    acid_star_fragile = curtailment_threshold(fragile, metal_price=1200, tc=-50, energy_price=70)
    assert acid_star_resilient is not None and acid_star_fragile is not None, \
        "selfcheck setup produced no root -- widen acid_bounds or adjust the example"
    assert acid_star_fragile > acid_star_resilient, (
        f"expected the fragile smelter's Acid* ({acid_star_fragile}) to be HIGHER "
        f"(less negative) than the resilient one's ({acid_star_resilient}) -- "
        f"sign convention is broken, do not trust threshold_gap's interpretation."
    )
    gap = threshold_gap(acid_star_fragile, acid_star_resilient)
    assert gap is not None and gap > 0, f"expected a positive gap for (fragile, resilient), got {gap}"
    print(
        "threshold_gap sign-convention selfcheck: PASS "
        f"(Acid*_fragile={acid_star_fragile:.1f} > Acid*_resilient={acid_star_resilient:.1f}, "
        f"gap={gap:.1f} > 0 -- a positive gap correctly means the FIRST argument passed "
        f"to threshold_gap is the MORE exposed / earlier-curtailing metal)."
    )


def bridge_rows_from_df(df: pd.DataFrame, metal_prefix: str, date_start, date_end) -> tuple:
    """
    Convenience helper: pulls two rows out of a df built with the
    zn_price/cu_price, zn_tc/cu_tc naming convention used elsewhere in this
    project, and relabels them to the generic metal_price/tc keys
    `margin_bridge` expects. metal_prefix is "zn" or "cu".
    """
    cols = {f"{metal_prefix}_price": "metal_price", f"{metal_prefix}_tc": "tc"}
    passthrough = ["acid_price", "energy_price", "silver_price", "gold_price"]
    r0 = df.loc[date_start].rename(cols)
    r1 = df.loc[date_end].rename(cols)
    keep = ["metal_price", "tc"] + [c for c in passthrough if c in df.columns]
    return r0[keep], r1[keep]


def margin_bridge(
        params: SmelterParams,
        row_start: pd.Series,
        row_end: pd.Series,
) -> dict:
    """
    Exact additive decomposition of the CHANGE in smelter margin between
    two points in time into its components. This answers the strategist
    question "is the acid channel material, or marginal noise next to the
    TC move?" with a number instead of an impression.

    Because `smelter_margin` is linear and purely additive in metal_price,
    acid_price, silver_price, gold_price, tc and energy_price (no cross
    terms), the bridge below is EXACT -- it is not a linearised
    approximation, and the five contributions sum to the total margin
    change to floating-point precision. row_start / row_end must each
    contain zn_price/cu_price (whichever metal `params` is for -- pass the
    right price column), tc, acid_price, energy_price and, optionally,
    silver_price / gold_price.

    Note: this decomposes CHANGE ONLY -- premium and conversion_cost are
    held fixed in `params` and so contribute exactly 0 to the delta by
    construction, not because they don't matter to the LEVEL of the margin.
    """
    def get(row, key):
        return row[key] if key in row else 0.0

    d_metal_price = row_end["metal_price"] - row_start["metal_price"]
    d_acid_price = row_end["acid_price"] - row_start["acid_price"]
    d_silver_price = get(row_end, "silver_price") - get(row_start, "silver_price")
    d_gold_price = get(row_end, "gold_price") - get(row_start, "gold_price")
    d_tc = row_end["tc"] - row_start["tc"]
    d_energy_price = row_end["energy_price"] - row_start["energy_price"]

    contributions = {
        "metal_price": params.metal_grade * params.payable_fraction * d_metal_price,
        "acid_price": params.acid_yield * d_acid_price,
        "silver_price": params.silver_yield_oz * d_silver_price,
        "gold_price": params.gold_yield_oz * d_gold_price,
        "tc": d_tc,
        "energy_price": -params.energy_per_t * d_energy_price,
    }
    contributions["total"] = sum(contributions.values())

    # cross-check against directly recomputing the margin at both points
    sm_start = smelter_margin(params, row_start["metal_price"], row_start["tc"], row_start["acid_price"],
                              row_start["energy_price"], get(row_start, "silver_price"), get(row_start, "gold_price"))
    sm_end = smelter_margin(params, row_end["metal_price"], row_end["tc"], row_end["acid_price"],
                            row_end["energy_price"], get(row_end, "silver_price"), get(row_end, "gold_price"))
    contributions["_check_direct_delta"] = sm_end - sm_start
    return contributions


def relative_acid_contribution_share(bridge_zn: dict, bridge_cu: dict) -> dict:
    """
    Compares, as a share of each metal's OWN total margin change, how much
    came from the acid channel vs the TC channel. This is the direct
    answer to "does acid economics dominate or is it marginal noise next
    to TC" -- computed separately for zinc and copper, since the whole
    thesis rests on that share being structurally different between them,
    not on the absolute size of either number alone.

    CAUTION: if `bridge["total"]` is small (the two channels roughly
    cancelled out), these shares can blow up or flip sign even though the
    underlying dollar contributions are unremarkable -- always read this
    next to the dollar figures in the bridge dict, not in isolation.
    """
    def share(bridge, key):
        total = bridge["total"]
        return bridge[key] / total if total != 0 else float("nan")

    return {
        "zn_acid_share_of_total_change": share(bridge_zn, "acid_price"),
        "zn_tc_share_of_total_change": share(bridge_zn, "tc"),
        "cu_acid_share_of_total_change": share(bridge_cu, "acid_price"),
        "cu_tc_share_of_total_change": share(bridge_cu, "tc"),
    }


def free_metal_revenue(params: SmelterParams, metal_price: pd.Series | float) -> pd.Series | float:
    """
    The smelter's OWN retained metal revenue -- what CRU and industry
    commentary call "free metal," a distinct smelter-income component
    separate from TC/RC and byproduct credits: the fraction of contained
    metal the smelter is NOT contractually required to pay the concentrate
    supplier for (1 - payable_fraction), valued at the metal price.

    This is DIFFERENT from SmelterParams.metal_revenue() (used by
    smelter_margin() above), which values the smelter's FULL payable
    metal recovery -- the right concept for an INTEGRATED mine+smelter
    (Kamoa-Kakula) that owns the metal outright, but an overstatement by
    roughly 30-60x for a CUSTOM/TOLLING smelter (Freeport Miami, typical
    Chinese import smelters), whose own margin the industry actually
    prices as TC + free metal + byproducts - costs -- this is exactly the
    source article's own CRU citation: "TC revenue accounted for 39% of
    smelter income in 2018; by 2025, free metal represented roughly
    50-53%, and by-product credits ... another 25-27%." A custom smelter
    does not keep the full value of the metal it processes; it keeps the
    treatment charge, the byproducts, and this "free" sliver.
    """
    return metal_price * params.metal_grade * (1 - params.payable_fraction)


def treatment_margin(
        params: SmelterParams,
        metal_price, tc, acid_price, energy_price,
        silver_price=0.0, gold_price=0.0,
) -> pd.Series | float:
    """
    The CUSTOM-SMELTER (tolling) reading of smelter economics -- TC + free
    metal + byproduct credits + premium - energy - conversion, ALL on a
    treatment-charge scale ($ tens-to-hundreds per tonne concentrate, the
    same scale as TC itself). This is the concept the source article's CRU
    citation and this project's Residual Margin metrics (residual_margin,
    acid_stress_test, acid_cushion_ratio below) are actually about.

    NOT the same number as smelter_margin() above, which folds in the
    smelter's FULL payable-metal revenue (metal-price scale, thousands of
    $/t) -- appropriate only for an integrated mine+smelter like Kamoa,
    where implied_acid_yield_and_buffer() (further below) is used instead,
    on Kamoa's own disclosed per-lb-copper basis. Using smelter_margin()
    where this project means "is the treatment side of the business under
    pressure" would have swamped the TC/acid signal in copper-price
    noise -- copper's own price moves dwarf a $200/t TC swing by roughly
    two orders of magnitude at 2026 price levels. treatment_margin() is
    the function that avoids that, and is what residual_margin() /
    acid_stress_test() / the Copper Acid Cushion Monitor's "Total margin"
    line are actually built on.
    """
    byprod_rev = params.byproduct_revenue(acid_price, silver_price, gold_price)
    free_metal = free_metal_revenue(params, metal_price)
    energy_cost = energy_price * params.energy_per_t
    return free_metal + byprod_rev + tc + params.premium - energy_cost - params.conversion_cost


def acid_revenue_only(params: SmelterParams, acid_price: pd.Series | float) -> pd.Series | float:
    """The acid-by-product slice of ByproductRevenue ALONE (excludes silver/
    gold) -- i.e. `params.acid_yield * acid_price`. Separated out from
    `SmelterParams.byproduct_revenue` so the acid-cushion metrics below
    (which are specifically about sulphuric acid, not by-products in
    general) don't silently fold silver/gold credits into "acid cushion"."""
    return params.acid_yield * acid_price


def acid_cushion_ratio(acid_revenue: pd.Series | float, tc: pd.Series | float) -> pd.Series | float:
    """
    Acid Cushion Ratio = Acid Revenue / |TC|, defined ONLY where TC < 0
    (i.e. TC is a net cost the acid channel might be offsetting). Returns
    NaN where TC >= 0 -- "cushion" is meaningless when TC is still paying
    the smelter; forcing a ratio there would silently misrepresent a
    normal-regime TC as if it were something acid needed to rescue.

    Reading:
        > 100%  -> acid revenue more than offsets the TC drag
        = 100%  -> acid revenue exactly offsets it
        0-100%  -> acid covers PART of the TC drag (this is the "cushion")
        < 0%    -> acid revenue is itself negative (not observed in this
                   project's data, but not special-cased away either)

    This is the direct, single-number answer to the source article's
    central question: "how much of the negative TC is currently being
    absorbed by acid revenue?"
    """
    if isinstance(tc, pd.Series):
        out = acid_revenue / tc.abs()
        out = out.where(tc < 0, other=float("nan"))
        return out
    if tc >= 0:
        return float("nan")
    return acid_revenue / abs(tc)


def cushion_loss(cushion_ratio_series: pd.Series, periods: int = 1) -> pd.Series:
    """Change in the Acid Cushion Ratio over `periods` steps of whatever
    index `cushion_ratio_series` uses (weeks, quarters, ...). A negative
    number means the cushion is SHRINKING -- less of the TC drag is being
    absorbed by acid than `periods` steps ago. This is the direct
    quantitative version of the source article's "cushion is shrinking"
    claim, not just a qualitative read of the acid price chart."""
    return cushion_ratio_series.diff(periods)


def residual_margin(
        params: SmelterParams,
        metal_price, tc, acid_price, energy_price,
        silver_price=0.0, gold_price=0.0,
) -> dict:
    """
    Splits TREATMENT margin (see treatment_margin() above -- TC + free
    metal + byproducts - costs, the treatment-charge-scale reading, NOT
    smelter_margin()'s full-metal-inclusive figure) into:
        margin_ex_acid    -- everything EXCEPT the sulphuric-acid credit
                              (free metal + TC + silver/gold byproducts
                              - energy - conversion + premium)
        acid_contribution -- the sulphuric-acid credit alone
        total_margin      -- treatment_margin(), unchanged, for a
                              cross-check (kept as "total_margin" for
                              backward compatibility with existing callers/
                              output columns, even though it is now the
                              TREATMENT total, not the smelter_margin()
                              total -- see this function's history: prior
                              to the 2026-09-16 fix this used smelter_
                              margin(), which put margin_ex_acid on a
                              metal-price-dominated scale ($3,000+/t) that
                              could never plausibly show "underwater
                              without acid," contradicting the whole point
                              of the metric)

    This is the "is the smelter already underwater without acid?" question
    from the source article/review, made explicit: if margin_ex_acid is
    negative while total_margin is still positive, the smelter's survival
    currently depends ENTIRELY on the acid credit -- a materially
    different (and more fragile) statement than "margin is positive."

    Exact by construction (treatment_margin is additive/linear in these
    inputs) -- margin_ex_acid + acid_contribution == total_margin to
    floating-point precision; see _selfcheck_residual_margin_additivity()
    for a runnable proof (run `python margin_model.py`).
    """
    acid_contribution = acid_revenue_only(params, acid_price)
    total = treatment_margin(params, metal_price, tc, acid_price, energy_price, silver_price, gold_price)
    margin_ex_acid = total - acid_contribution
    return {
        "margin_ex_acid": margin_ex_acid,
        "acid_contribution": acid_contribution,
        "total_margin": total,
    }


def acid_stress_test(
        params: SmelterParams,
        metal_price, tc, acid_price, energy_price,
        shocks=(0.0, -0.10, -0.20, -0.30),
        silver_price=0.0, gold_price=0.0,
) -> pd.DataFrame:
    """
    Recompute total margin, margin_ex_acid and the Acid Cushion Ratio under
    acid-price shocks (default: flat, -10%, -20%, -30% -- the exact stress
    bands the source article's central question calls for: "what happens
    if acid falls 10/20/30% while TC stays where it is?"). Holds TC, metal
    price and everything else fixed at the single snapshot passed in --
    this is a stress test, not a forecast; it does not model TC and acid
    ever moving together even though in practice they may.
    """
    rows = []
    for s in shocks:
        shocked_acid = acid_price * (1 + s)
        res = residual_margin(params, metal_price, tc, shocked_acid, energy_price, silver_price, gold_price)
        acid_rev = acid_revenue_only(params, shocked_acid)
        rows.append({
            "acid_shock_pct": s,
            "acid_price": shocked_acid,
            "acid_contribution": res["acid_contribution"],
            "margin_ex_acid": res["margin_ex_acid"],
            "total_margin": res["total_margin"],
            "acid_cushion_ratio": acid_cushion_ratio(acid_rev, tc),
        })
    return pd.DataFrame(rows)


def acid_yield_sensitivity(
        params: SmelterParams,
        metal_price, tc, acid_price, energy_price,
        acid_yields: Optional[tuple] = None,
        silver_price=0.0, gold_price=0.0,
) -> pd.DataFrame:
    """
    Recompute total margin, margin_ex_acid and the Acid Cushion Ratio
    across a range of `acid_yield` values, holding TC/acid price/metal
    price/everything else fixed at the single snapshot passed in -- same
    "flex one input, hold the rest" convention as `acid_stress_test()` and
    `energy_stress_test()` just above/below this function.

    Added 2026-09-26 (external review point 4). The headline Acid Cushion
    Ratio and acid-credit dollar figure are DIRECTLY proportional to
    `params.acid_yield` (acid_contribution = acid_yield * acid_price), and
    `DEFAULT_CU_PARAMS.acid_yield = 0.83` is itself a single point
    estimate, not a settled constant. It sits close to, but not exactly
    at, the Freeport-implied figure (~0.828, from 680kt acid / 821kt
    concentrate processed, FY2025 10-K -- see `data/
    freeport_copper_byproducts.csv`) and inside the wider "3.0-3.5 t
    acid / t copper metal" industry range this project also cites
    (`model_a.py`'s `DEFAULT_CU_PARAMS` comment), which at
    `metal_grade=0.255` implies a per-concentrate-tonne range of roughly
    0.765 to 0.8925. This function exists to answer directly: how much of
    the "68.2% cushion ratio, down from 94.3%" finding depends on exactly
    where in that range the true figure sits, rather than leaving that as
    an unquantified caveat.

    Default range, if `acid_yields` is not given: the low end, the
    current default, and the high end of that cited industry range --
    (0.765, 0.83, 0.8925).
    """
    if acid_yields is None:
        acid_yields = (0.765, 0.83, 0.8925)
    rows = []
    for y in acid_yields:
        shocked_params = replace(params, acid_yield=y)
        res = residual_margin(shocked_params, metal_price, tc, acid_price, energy_price,
                              silver_price, gold_price)
        acid_rev = acid_revenue_only(shocked_params, acid_price)
        rows.append({
            "acid_yield": y,
            "acid_contribution": res["acid_contribution"],
            "margin_ex_acid": res["margin_ex_acid"],
            "total_margin": res["total_margin"],
            "acid_cushion_ratio": acid_cushion_ratio(acid_rev, tc),
        })
    return pd.DataFrame(rows)


def implied_acid_yield_and_buffer(
        acid_credit_per_unit: float,
        opex_per_unit: float,
        realized_acid_price_per_t: float,
        at_price: Optional[float] = None,
) -> dict:
    """
    Dimension-GENERAL version of the Acid* / curtailment-threshold idea,
    for use with a disclosure like Kamoa-Kakula's that reports acid credit
    and smelter opex per unit of PAYABLE METAL (e.g. $/lb copper) rather
    than per tonne of concentrate processed -- SmelterParams/
    curtailment_threshold's basis elsewhere in this project. DO NOT pass
    Nexa/Freeport-style per-concentrate-tonne figures through this
    function, and do not pass Kamoa-style per-metal-unit figures through
    curtailment_threshold() -- the two conventions are not interchangeable
    without a concentrate-grade conversion this project does not have for
    Kamoa. See model_c.py for exactly how this is used and why keeping the
    two separate, rather than forcing one calibration to serve both, is
    the more honest choice here.

    Given:
        acid_credit_per_unit    -- e.g. Kamoa's disclosed $0.39/lb (Q2 2026)
        opex_per_unit           -- e.g. Kamoa's disclosed $0.41/lb (Q2 2026)
        realized_acid_price_per_t -- e.g. Kamoa's disclosed $465/t (Q2 2026)

    Backs out:
        implied_acid_yield  = acid_credit_per_unit / realized_acid_price_per_t
                               (tonnes of acid "earned" per unit of metal --
                               NOT the same figure as SmelterParams.acid_yield,
                               which is per tonne of CONCENTRATE, not per
                               unit of metal; don't compare the two directly)
        breakeven_acid_price = opex_per_unit / implied_acid_yield
                               (the realized acid price at which the acid
                               credit alone would have exactly covered
                               smelter opex that quarter)
        implied_buffer      = (at_price or realized_acid_price_per_t) - breakeven_acid_price
                               (positive => acid credit more than covered
                               opex at that price; negative => it did not)

    Returns NaNs (not a crash) if realized_acid_price_per_t or the implied
    yield is zero/None. Ivanhoe's Q1 and Q2 2026 releases both disclose a
    realized average ($467/t and $465/t); an earlier version of this
    docstring said Q1 had no realized figure -- that was wrong.
    """
    if not realized_acid_price_per_t or pd.isna(realized_acid_price_per_t):
        return {"implied_acid_yield": float("nan"), "breakeven_acid_price": float("nan"),
                "implied_buffer": float("nan")}
    implied_yield = acid_credit_per_unit / realized_acid_price_per_t
    if not implied_yield:
        return {"implied_acid_yield": float("nan"), "breakeven_acid_price": float("nan"),
                "implied_buffer": float("nan")}
    breakeven = opex_per_unit / implied_yield
    ref_price = at_price if at_price is not None else realized_acid_price_per_t
    return {
        "implied_acid_yield": implied_yield,
        "breakeven_acid_price": breakeven,
        "implied_buffer": ref_price - breakeven,
    }


def energy_stress_test(
        params: SmelterParams,
        metal_price, tc, acid_price, energy_price,
        shocks=(0.0, 0.05, 0.10, 0.20),
        silver_price=0.0, gold_price=0.0,
) -> pd.DataFrame:
    """
    Recompute the margin under +5% / +10% / +20% conversion-cost & energy
    shocks. This is the "sensitivity analysis instead of fake precision"
    step described in the note (section 19) -- use it instead of pretending
    you know the exact Chinese industrial electricity tariff.
    """
    rows = []
    for s in shocks:
        p = SmelterParams(**{**params.__dict__, "conversion_cost": params.conversion_cost * (1 + s),
                             "energy_per_t": params.energy_per_t * (1 + s)})
        sm = smelter_margin(p, metal_price, tc, acid_price, energy_price, silver_price, gold_price)
        rows.append({"cost_shock": s, "margin": sm})
    return pd.DataFrame(rows)


def _selfcheck_residual_margin_additivity() -> None:
    """Runnable proof that residual_margin()'s split is exact:
    margin_ex_acid + acid_contribution == total_margin, and that
    acid_stress_test()'s per-row split satisfies the same identity at
    every shock level. Run directly: `python margin_model.py`."""
    p = SmelterParams(metal_grade=0.255, payable_fraction=0.96, acid_yield=0.83,
                      silver_yield_oz=0.05, gold_yield_oz=0.002, conversion_cost=260.0,
                      energy_per_t=0.40, premium=20.0)
    res = residual_margin(p, metal_price=9500, tc=-200, acid_price=227.7, energy_price=70)
    diff = abs(res["margin_ex_acid"] + res["acid_contribution"] - res["total_margin"])
    assert diff < 1e-9, f"residual_margin additivity broken: off by {diff}"
    stress = acid_stress_test(p, metal_price=9500, tc=-200, acid_price=227.7, energy_price=70)
    for _, row in stress.iterrows():
        d2 = abs(row["margin_ex_acid"] + row["acid_contribution"] - row["total_margin"])
        assert d2 < 1e-9, f"acid_stress_test additivity broken at shock {row['acid_shock_pct']}: off by {d2}"
    print("residual_margin/acid_stress_test additivity selfcheck: PASS "
          f"(margin_ex_acid={res['margin_ex_acid']:.2f} + acid_contribution="
          f"{res['acid_contribution']:.2f} == total_margin={res['total_margin']:.2f})")


if __name__ == "__main__":
    _selfcheck_threshold_gap_sign()
    _selfcheck_residual_margin_additivity()