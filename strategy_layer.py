"""
strategy_layer.py
=================
The "so what" layer on top of the copper acid-cushion monitor.

The monitor answers *what is the cushion now*. This module answers the
questions a desk would actually ask next:

  1. ATTRIBUTION   -- how much of the fall in the cushion ratio is the ACID
                      leg and how much is the TC leg? (exact log decomposition)
  2. COUNTERFACTUAL-- what would the cushion / margin look like had acid
                      stayed at its July peak (or had TC stayed put)?
  3. REGIME MAP    -- cushion ratio across a (TC x acid price) grid, so the
                      current point and the 2026 path can be read as regimes,
                      not as a single number.
  4. DEFINITIONS   -- how fragile is the LEVEL of the headline ratio to the
                      things the SMM series do not settle (acid yield, refining
                      charge, VAT basis)? The direction survives; the level does not.
                      The headline is on an ex-VAT basis (SMM quotes the RMB index
                      VAT-inclusive by its own convention; VAT is not smelter revenue).
  5. REGIONAL      -- China-domestic acid vs ex-China acid, and what Kamoa's own
                      disclosure really says (a Q1-opex-accounting and volume story in Q2,
                      a WIDENING-coverage story in Q3 -- not a shrinking cushion).
  6. FALSIFICATION -- pre-registered, machine-checkable conditions under which
                      the thesis strengthens or weakens, with current status.

Nothing here forecasts a price or proposes a trade. No new data series are
introduced: every input comes from copper_acid_data.py / model_a.py. Where an
input is a convention rather than an observation (RC = 10% of TC), it is
labelled as such and only ever used as a sensitivity. The 13% VAT deduction IS
applied in the headline (SMM convention, inferred for the national index).

Thresholds marked "judgment" are declared up-front (2026-10-01) and are NOT
calibrated or backtested -- their job is to make the thesis falsifiable, not to
generate signals.
"""

from __future__ import annotations

from itertools import product

import numpy as np
import pandas as pd

import copper_acid_data as cad
from margin_model import SmelterParams

LB_PER_TONNE = 2204.62

# Regime labels for the cushion ratio (acid credit / |TC drag|).
# judgment levels, declared 2026-10-01, not calibrated.
CUSHION_ERODING_BELOW = 1.00     # acid no longer fully absorbs the TC drag
CUSHION_EXHAUSTED_BELOW = 0.50   # acid absorbs less than half of it


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def fx_for(date) -> float:
    """CNY per USD used by the project's weekly pipeline for `date` (quarterly
    average table -- a known limitation: FX steps at quarter boundaries)."""
    return cad.usd_cny_for_date(date)


def _ratio(acid_credit, drag):
    """acid_credit / |drag|, defined only where drag < 0 (TC is a net cost)."""
    out = acid_credit / np.abs(drag)
    if isinstance(out, pd.Series):
        return out.where(drag < 0)
    return float(out) if drag < 0 else float("nan")


def rc_usd_per_dmt(tc, params: SmelterParams, rc_to_tc: float | None = None):
    """Refining charge implied by the SMM convention RC(c/lb) = 10% x TC($/dmt),
    converted to USD per dmt of CONCENTRATE (payable copper x lb/t).
    A CONVENTION, not an observed series -- used only as a sensitivity."""
    k = cad.ACID_QUOTE_BASIS["rc_to_tc_convention"] if rc_to_tc is None else rc_to_tc
    rc_cents_per_lb = tc * k
    return rc_cents_per_lb / 100.0 * LB_PER_TONNE * params.metal_grade * params.payable_fraction


def cushion_ratio_variant(acid_usd_t, tc, params: SmelterParams, acid_yield=None,
                          include_rc=False, vat=0.0):
    """Acid cushion under an explicit definition. `acid_usd_t` must be the QUOTED
       (VAT-inclusive) USD price (weekly["acid_usd_t_quoted"]); vat = 0.13 strips VAT.
       credit = yield * acid_price / (1 + vat);  drag = TC (+ RC if include_rc).
       The project headline = (vat=0.13, include_rc=False)."""
    y = params.acid_yield if acid_yield is None else acid_yield
    credit = y * acid_usd_t / (1.0 + vat)
    drag = tc + (rc_usd_per_dmt(tc, params) if include_rc else 0.0)
    return _ratio(credit, drag)


def cushion_regime(ratio: float) -> str:
    if pd.isna(ratio):
        return "N/A (TC not negative)"
    if ratio >= CUSHION_ERODING_BELOW:
        return "ABSORBING"
    if ratio >= CUSHION_EXHAUSTED_BELOW:
        return "ERODING"
    return "EXHAUSTED"


def _first_sustained_below(series: pd.Series, level: float = 1.0):
    """First date from which the series stays below `level` until the end."""
    below = (series < level).to_numpy()
    for i in range(len(below)):
        if below[i:].all():
            return series.index[i]
    return None


def _basis(weekly: pd.DataFrame, date) -> str:
    r = weekly.loc[pd.Timestamp(date)]
    ok = lambda s: s in ("cited", "cited-approx")
    if ok(r["tc_status"]) and ok(r["acid_status"]):
        return "both cited"
    if ok(r["tc_status"]) or ok(r["acid_status"]):
        return "partly interpolated"
    return "interpolated"


# ---------------------------------------------------------------------------
# 1. ATTRIBUTION
# ---------------------------------------------------------------------------
def attribute_ratio_change(weekly: pd.DataFrame, start, end=None) -> dict:
    """Exact decomposition of ln(R_end / R_start), R = yield*acid_usd/|TC|:

        ln(R_end/R_start) = ln(acid_end/acid_start)   [acid leg]
                          - ln(|TC_end|/|TC_start|)   [TC leg]

    (acid_yield cancels.) The acid leg is further split into local-currency
    price and FX. Shares are of the TOTAL log change; if the two legs have
    opposite signs a share can fall outside 0-100% -- that is reported, not
    hidden."""
    start, end = pd.Timestamp(start), (weekly.index[-1] if end is None else pd.Timestamp(end))
    a, b = weekly.loc[start], weekly.loc[end]
    acid_leg = float(np.log(b["acid_usd_t"] / a["acid_usd_t"]))
    tc_leg = float(-np.log(abs(b["tc_usd_dmt"]) / abs(a["tc_usd_dmt"])))
    fx_leg = float(-np.log(fx_for(end) / fx_for(start)))
    total = acid_leg + tc_leg
    return {
        "start": start.date(), "end": end.date(),
        "ratio_start": float(a["acid_cushion_ratio"]), "ratio_end": float(b["acid_cushion_ratio"]),
        "log_change_total": total,
        "acid_leg": acid_leg, "acid_leg_local_price": acid_leg - fx_leg, "acid_leg_fx": fx_leg,
        "tc_leg": tc_leg,
        "acid_share": acid_leg / total if total != 0 else float("nan"),
        "tc_share": tc_leg / total if total != 0 else float("nan"),
        "basis_start": _basis(weekly, start), "basis_end": _basis(weekly, end),
    }


def attribute_margin_change(weekly: pd.DataFrame, params: SmelterParams, start, end=None) -> dict:
    """Additive $/t-concentrate decomposition of the change in treatment margin
    (energy, conversion cost and premium are constants in the model, so they
    drop out). `residual` must be ~0 -- it is the additivity check."""
    start, end = pd.Timestamp(start), (weekly.index[-1] if end is None else pd.Timestamp(end))
    a, b = weekly.loc[start], weekly.loc[end]
    d_tc = float(b["tc_usd_dmt"] - a["tc_usd_dmt"])
    d_acid = float(params.acid_yield * (b["acid_usd_t"] - a["acid_usd_t"]))
    d_free = float(params.metal_grade * (1 - params.payable_fraction) * (b["cu_price"] - a["cu_price"]))
    d_silver = float(params.silver_yield_oz * (b["silver_price"] - a["silver_price"]))
    total = float(b["total_margin"] - a["total_margin"])
    return {
        "start": start.date(), "end": end.date(),
        "margin_start": float(a["total_margin"]), "margin_end": float(b["total_margin"]),
        "total_change": total, "tc": d_tc, "acid": d_acid, "free_metal": d_free, "silver": d_silver,
        "residual": total - (d_tc + d_acid + d_free + d_silver),
    }


# ---------------------------------------------------------------------------
# 2. COUNTERFACTUAL
# ---------------------------------------------------------------------------
def counterfactual_paths(weekly: pd.DataFrame, params: SmelterParams, ref_date) -> pd.DataFrame:
    """From `ref_date` onward, compare the ACTUAL cushion ratio with:
         cf_flat_acid -- acid price held at its ref-date LOCAL-currency level
                         (converted at actual FX), TC as actually observed;
         cf_flat_tc   -- TC held at its ref-date level, acid as observed.
    At ref_date all three coincide (checked in the self-check)."""
    ref_date = pd.Timestamp(ref_date)
    ref = weekly.loc[ref_date]
    post = weekly.loc[ref_date:]
    fx_ratio = pd.Series([fx_for(ref_date) / fx_for(d) for d in post.index], index=post.index)
    acid_cf = ref["acid_usd_t"] * fx_ratio          # constant local-currency price
    out = pd.DataFrame(index=post.index)
    out["actual"] = post["acid_cushion_ratio"]
    out["cf_flat_acid"] = params.acid_yield * acid_cf / post["tc_usd_dmt"].abs()
    out["cf_flat_tc"] = params.acid_yield * post["acid_usd_t"] / abs(ref["tc_usd_dmt"])
    out["margin_actual"] = post["total_margin"]
    out["margin_cf_flat_acid"] = post["total_margin"] + params.acid_yield * (acid_cf - post["acid_usd_t"])
    return out


# ---------------------------------------------------------------------------
# 3. REGIME MAP
# ---------------------------------------------------------------------------
def regime_matrix(params: SmelterParams, tc_levels, acid_cny_levels, fx: float,
                  cu_price: float, silver_price: float, energy_price: float,
                  vat: float | None = None) -> dict:
    """Cushion ratio and treatment margin on a (TC, acid RMB/t) grid. Uses the
    same formulas as the monitor, so the cell nearest the latest observation
    reproduces the headline (self-checked)."""
    from margin_model import treatment_margin
    vat = cad.ACID_QUOTE_BASIS["vat_rate_cn"] if vat is None else vat
    ratio = pd.DataFrame(index=list(tc_levels), columns=list(acid_cny_levels), dtype=float)
    margin = ratio.copy()
    for tc in tc_levels:
        for acid_cny in acid_cny_levels:
            acid_usd = acid_cny / (1.0 + vat) / fx          # RMB axis = as-quoted index; model credit is ex-VAT
            ratio.loc[tc, acid_cny] = _ratio(params.acid_yield * acid_usd, tc)
            margin.loc[tc, acid_cny] = treatment_margin(params, cu_price, tc, acid_usd,
                                                        energy_price, silver_price=silver_price)
    ratio.index.name, ratio.columns.name = "TC_usd_dmt", "acid_cny_t"
    margin.index.name, margin.columns.name = "TC_usd_dmt", "acid_cny_t"
    return {"ratio": ratio, "margin": margin}


def cushion_frontier_acid_cny(tc_usd_dmt: float, params: SmelterParams, fx: float,
                              level: float = 1.0, vat: float | None = None) -> float:
    """AS-QUOTED (VAT-inclusive) acid index level (RMB/t) at which the cushion ratio equals `level`."""
    vat = cad.ACID_QUOTE_BASIS["vat_rate_cn"] if vat is None else vat
    return level * abs(tc_usd_dmt) / params.acid_yield * fx * (1.0 + vat)


# ---------------------------------------------------------------------------
# 4. DEFINITION SENSITIVITY
# ---------------------------------------------------------------------------
def definition_sensitivity(weekly: pd.DataFrame, params: SmelterParams,
                           yields=(0.765, 0.83, 0.8925)) -> pd.DataFrame:
    """Latest-week cushion ratio under every combination of: acid yield (cited
    industry range) x refining charge (excluded / included at the SMM 10%-of-TC
    convention) x VAT basis (13% stripped = headline / quote taken as-is)."""
    last = weekly.iloc[-1]
    rows = []
    for y, rc, vat in product(yields, (False, True), (0.0, cad.ACID_QUOTE_BASIS["vat_rate_cn"])):
        rows.append({
            "acid_yield": y, "include_rc": rc, "vat_stripped": vat > 0,
            "cushion_ratio": cushion_ratio_variant(last["acid_usd_t_quoted"], last["tc_usd_dmt"], params, y, rc, vat),
        })
    return pd.DataFrame(rows)


def definition_paths(weekly: pd.DataFrame, params: SmelterParams) -> pd.DataFrame:
    """Full-history cushion ratio under the four (RC, VAT) definitions at the
    default acid yield, plus the date from which each stays below 100%."""
    cols = {}
    for rc, vat in product((False, True), (0.0, cad.ACID_QUOTE_BASIS["vat_rate_cn"])):
        label = f"{'TC+RC' if rc else 'TC only'} | {'ex-VAT' if vat else 'as quoted'}"
        cols[label] = cushion_ratio_variant(weekly["acid_usd_t_quoted"], weekly["tc_usd_dmt"], params,
                                            include_rc=rc, vat=vat)
    return pd.DataFrame(cols)


def implied_required_other_credit(weekly: pd.DataFrame) -> dict:
    """What would have to be true for the representative smelter to break even?
    The model's treatment margin is negative; this reports the gap in $/t
    concentrate (and its silver-equivalent) that other credits / cost savings
    (precious metals, scrap, own mines, premiums, lower cost) must cover. It
    turns an uncalibrated level ('-$186/t') into an explicit requirement."""
    last = weekly.iloc[-1]
    gap = max(0.0, -float(last["total_margin"]))
    gap_ex_acid = max(0.0, -float(last["margin_ex_acid"]))
    return {
        "gap_with_acid_usd_t_conc": gap,
        "gap_without_acid_usd_t_conc": gap_ex_acid,
        "silver_equivalent_oz_per_t_conc": gap / float(last["silver_price"]) if last["silver_price"] else float("nan"),
        "note": ("Not a forecast of losses: the representative-smelter cost inputs are uncalibrated and the model "
                 "carries only a token precious-metal credit (silver 0.05 oz/t; gold has no price series here -- immaterial: <$12/t even at $6,000/oz, and zero effect on the cushion ratio). "
                 "Read it as 'the size of everything else that must be true', not as observed smelter P&L."),
    }


# ---------------------------------------------------------------------------
# 5. REGIONAL DIVERGENCE + KAMOA
# ---------------------------------------------------------------------------
def regional_divergence() -> dict:
    """China-domestic acid vs the ex-China benchmarks, at the regional
    benchmark's own latest print date (the benchmark has not printed since)."""
    asof = pd.Timestamp(cad.REGIONAL_ACID_BENCHMARK["weekly"][-1][0])
    china_cny = float(cad.cu_acid_weekly_interpolated().loc[asof, "acid_cny_t"])
    quoted = china_cny / fx_for(asof)
    vat = cad.ACID_QUOTE_BASIS["vat_rate_cn"]
    drc, zambia = cad.REGIONAL_ACID_BENCHMARK["weekly"][-1][1:3]
    return {
        "as_of": asof.date(),
        "china_domestic_usd_t_as_quoted": quoted,
        "china_domestic_usd_t_ex_vat": quoted / (1 + vat),      # model basis
        "drc_over_china_ex_vat": float(drc) / (quoted / (1 + vat)),
        "exw_zambia_usd_t": float(zambia), "exw_drc_usd_t": float(drc),
        "kamoa_q2_realized_usd_t": cad.KAMOA_KAKULA_QUARTERLY["2026-Q2"]["realized_acid_price_usd_t"],
        "kamoa_jul_aug_contract_usd_t": cad.KAMOA_KAKULA_QUARTERLY["2026-Q2"]["contract_price_usd_t"],
        "drc_over_china_as_quoted": float(drc) / quoted,
        "spread_drc_minus_china_as_quoted_usd_t": float(drc) - quoted,
        "caveat": ("EXW DRC/Zambia are landlocked leach-demand markets, not an arbitrage leg for a Chinese "
                   "producer: the China acid export halt (in force through end-2026, per CRU reporting) blocks "
                   "the physical arbitrage, which is why the spread can persist. The regional benchmark launched "
                   "2026-06-05 and has printed flat for 5+ weeks -- genuine stability and a thin market are "
                   "indistinguishable on this data."),
    }


def kamoa_bridge() -> dict:
    """What Kamoa's disclosure actually shows (checked against Ivanhoe's Q1 and Q2 releases).
      * Q1->Q2 coverage (acid credit / smelter opex per lb) fell from 118.5% to 95.1%.
        Decomposition: the realised acid price was flat ($467 -> $465/t, -0.4%);
        credit per lb ROSE +22% (more acid sold per lb of copper produced); opex per
        lb rose +52% -- which the Q2 release attributes to the PARTIAL CAPITALISATION
        of smelter operating costs in Q1 (utilisation was ~60% in both quarters).
        So the dip is an accounting/volume effect; it carries no information about
        the acid price, and Q1's 118.5% was flattered.
      * Forward: management indicated a Q3 credit near $0.60/lb (secondary source:
        earnings-call summary); with Q2 opex that is ~146% coverage. Cross-check from
        the Q2 implied yield x $840/t contract: ~172%. Coverage is expected to WIDEN.
    Opex per lb is held at Q2 in the forward figures -- an assumption."""
    q1 = cad.KAMOA_KAKULA_QUARTERLY["2026-Q1"]
    q2 = cad.KAMOA_KAKULA_QUARTERLY["2026-Q2"]
    credit_leg = float(np.log(q2["acid_credit_usd_lb"] / q1["acid_credit_usd_lb"]))
    opex_leg = float(-np.log(q2["smelter_opex_usd_lb"] / q1["smelter_opex_usd_lb"]))
    price_leg = float(np.log(q2["realized_acid_price_usd_t"] / q1["realized_acid_price_usd_t"]))
    volume_per_lb_leg = credit_leg - price_leg      # acid sold per lb of copper produced
    implied_yield = q2["acid_credit_usd_lb"] / q2["realized_acid_price_usd_t"]        # t acid per lb Cu
    fwd_mgmt = cad.KAMOA_FORWARD_INDICATION["q3_acid_credit_usd_lb_mgmt"]
    fwd_yield = implied_yield * q2["contract_price_usd_t"]
    return {
        "coverage_q1": q1["acid_credit_usd_lb"] / q1["smelter_opex_usd_lb"],
        "coverage_q2": q2["acid_credit_usd_lb"] / q2["smelter_opex_usd_lb"],
        "credit_change_pct": q2["acid_credit_usd_lb"] / q1["acid_credit_usd_lb"] - 1,
        "opex_change_pct": q2["smelter_opex_usd_lb"] / q1["smelter_opex_usd_lb"] - 1,
        "acid_price_change_pct": q2["realized_acid_price_usd_t"] / q1["realized_acid_price_usd_t"] - 1,
        "log_credit_leg": credit_leg, "log_opex_leg": opex_leg,
        "log_price_leg": price_leg, "log_volume_per_lb_leg": volume_per_lb_leg,
        "implied_acid_t_per_t_cu": implied_yield * LB_PER_TONNE,
        "q3_credit_mgmt_usd_lb": fwd_mgmt,
        "q3_coverage_mgmt_at_q2_opex": fwd_mgmt / q2["smelter_opex_usd_lb"],
        "q3_credit_implied_yield_usd_lb": fwd_yield,
        "q3_coverage_implied_yield_at_q2_opex": fwd_yield / q2["smelter_opex_usd_lb"],
        "reading": ("Q1->Q2 dip = Q1 opex partly capitalised (company) + more acid sold per lb; realised acid price was "
                    "flat. It is NOT a falling-acid-price signal. Forward coverage is indicated to widen in Q3. "
                    "Kamoa is evidence of an EX-CHINA divergence from China's domestic cushion."),
    }


def sulphur_parity() -> dict:
    """Feedstock-only parity: acid price vs the sulphur cost of making the same
    acid by burning sulphur (0.32 t S per t of 98% acid). Dated -- sulphur has
    not been refreshed since 2026-07-31 and acid has fallen a further ~28% since.
    Context for 'who sets the floor', not an input to the cushion ratio."""
    s_date, s_price = cad.SULPHUR_EXW_SHANDONG_RMB_T[-1][0], cad.SULPHUR_EXW_SHANDONG_RMB_T[-1][1]
    acid = cad.cu_acid_weekly_interpolated()
    acid_then = float(acid.loc[pd.Timestamp(s_date), "acid_cny_t"])
    acid_now = float(acid["acid_cny_t"].iloc[-1])
    burner_feedstock = cad.T_SULPHUR_PER_T_98_ACID * s_price
    return {
        "sulphur_date": s_date, "sulphur_rmb_t": s_price,
        "burner_feedstock_rmb_per_t_acid": burner_feedstock,
        "acid_rmb_t_at_sulphur_date": acid_then,
        "acid_minus_feedstock_at_sulphur_date": acid_then - burner_feedstock,
        "acid_rmb_t_latest": acid_now,
        "stale": True,
        "note": ("By-product (smelter) acid has ~zero feedstock cost, so this does NOT net against the smelter's "
                 "credit. It says merchant acid traded far below sulphur-burner feedstock cost -- so the acid "
                 "price is not cost-floored, and burner curtailment / fertiliser restocking are live reversal "
                 "channels to monitor."),
    }


# ---------------------------------------------------------------------------
# 6. FALSIFICATION
# ---------------------------------------------------------------------------
def falsification_checks(weekly: pd.DataFrame, params: SmelterParams) -> list[dict]:
    """Pre-registered conditions. 'status' is one of NOT TRIGGERED / TRIGGERED /
    NOT TESTABLE (no fresh data) / PENDING (scheduled event) / MANUAL (event I
    cannot observe in code). Thresholds are judgment levels, not calibrated."""
    both_cited = weekly["tc_status"].isin(["cited", "cited-approx"]) & weekly["acid_status"].isin(
        ["cited", "cited-approx"]
    )
    r_cited = weekly.loc[both_cited, "acid_cushion_ratio"].dropna()
    r = weekly["acid_cushion_ratio"]
    tc = weekly["tc_usd_dmt"]
    asof = weekly.index[-1].date()
    checks = []

    # C1 is defined on consecutive PRINTS, not on interpolated grid weeks: using r.diff() on the full Friday grid
    # would let a grid-fill week start or stop "erosion" without a new SMM observation.
    if len(r_cited) >= 3:
        d1, d2 = float(r_cited.diff().iloc[-1]), float(r_cited.diff().iloc[-2])
        c1_current = (f"last two cited-print changes ({r_cited.index[-3].date()} -> {r_cited.index[-2].date()} -> "
                      f"{r_cited.index[-1].date()}): {d2*100:+.1f}pp, {d1*100:+.1f}pp")
        c1_status = "TRIGGERED" if (d1 > 0 and d2 > 0) else "NOT TRIGGERED"
    else:
        c1_current, c1_status = "not enough cited prints to evaluate", "NOT TESTABLE"
    checks.append({
        "id": "C1", "direction": "weakens", "leg": "mechanism",
        "condition": "Cushion ratio rises on two consecutive weekly prints (erosion stops)",
        "current": c1_current,
        "status": c1_status, "as_of": asof,
    })
    rec_low = tc.min()
    checks.append({
        "id": "C2", "direction": "weakens", "leg": "TC",
        "condition": "TC recovers >= $25/dmt from its record low (judgment; ~ the $20-28 index-minus discount SMM cites)",
        "current": f"TC {tc.iloc[-1]:.2f} vs record low {rec_low:.2f} (recovery {tc.iloc[-1]-rec_low:+.2f})",
        "status": "TRIGGERED" if (tc.iloc[-1] - rec_low) >= 25 else "NOT TRIGGERED", "as_of": asof,
    })
    last4 = r.iloc[-4:]
    below_half = int((last4 < CUSHION_EXHAUSTED_BELOW).sum())
    four_consecutive = len(last4) == 4 and bool((last4 < CUSHION_EXHAUSTED_BELOW).all())
    if four_consecutive:
        c3_status = "IN SCOPE -- check for documented dated curtailment"
    elif float(r.iloc[-1]) < CUSHION_EXHAUSTED_BELOW:
        c3_status = "WATCHING (below 50%, but not yet 4 consecutive weeks)"
    else:
        c3_status = "NOT YET IN SCOPE (cushion >= 50%)"
    checks.append({
        "id": "C3", "direction": "tests physical leg", "leg": "physical response",
        "condition": "Cushion < 50% for 4 consecutive weeks WITHOUT documented smelter curtailment => "
                     "acid is not binding in practice; the physical leg fails",
        "current": f"cushion {r.iloc[-1]*100:.1f}%; weeks below 50% in last 4: {below_half}; 4 consecutive: {four_consecutive}",
        "status": c3_status,
        "as_of": asof,
    })
    last_reg = cad.REGIONAL_ACID_BENCHMARK["weekly"][-1][0]
    checks.append({
        "id": "C4", "direction": "weakens", "leg": "regional divergence",
        "condition": "EXW DRC/Zambia benchmarks fall toward China-domestic levels (divergence closes)",
        "current": f"last regional print {last_reg} (flat 5+ weeks; thin-market ambiguity)",
        "status": "NOT TESTABLE (no print since " + last_reg + ")", "as_of": pd.Timestamp(last_reg).date(),
    })
    checks.append({
        "id": "C5", "direction": "strengthens / weakens", "leg": "company validation",
        "condition": "Kamoa Q3 results (late Oct/Nov): coverage > 100% and realised acid >> $465/t confirms the ex-China "
                     "side of the divergence; coverage < 100% contradicts it",
        "current": "management indication ~$0.60/lb credit vs $0.41 opex (~146%)",
        "status": "PENDING (Q3 release)", "as_of": asof,
    })
    checks.append({
        "id": "C6", "direction": "weakens", "leg": "acid-market regime",
        "condition": "China relaxes the acid export halt (reported in force through end-2026) and exports resume",
        "current": "China H2SO4 exports ~117kt (May) -> ~1kt (Jun), near zero into Jul",
        "status": "MANUAL (policy event)", "as_of": asof,
    })
    last_s = cad.SULPHUR_EXW_SHANDONG_RMB_T[-1][0]
    checks.append({
        "id": "C7", "direction": "weakens", "leg": "acid-market regime",
        "condition": "Sulphur-burner curtailments / fertiliser restocking lift China acid despite the halt",
        "current": f"sulphur series last refreshed {last_s} (stale vs the current acid print)",
        "status": "NOT TESTABLE (stale sulphur data)", "as_of": pd.Timestamp(last_s).date(),
    })
    return checks


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------
REFERENCE_WINDOWS = {
    # label -> (start date, why this start)
    "since April cushion peak": ("2026-04-24", "both TC and acid are cited prints"),
    "since July acid peak": ("2026-07-03", "acid index peak (cited); TC cited"),
    "last 4 weeks": (None, "start = 4 grid weeks before the latest week (set in reference_windows)"),
}


def reference_windows(weekly: pd.DataFrame) -> dict:
    """REFERENCE_WINDOWS with the rolling window resolved against the data, so the label
    "last 4 weeks" stays true after the grid is extended."""
    out = dict(REFERENCE_WINDOWS)
    out["last 4 weeks"] = (str(weekly.index[-5].date()), out["last 4 weeks"][1])
    return out


def run_strategy_layer(model_a_out: dict) -> dict:
    weekly = model_a_out["weekly"]
    params = model_a_out["params"]
    energy = model_a_out["energy_price_usd_mwh"]
    latest = weekly.iloc[-1]
    fx = fx_for(weekly.index[-1])

    windows = reference_windows(weekly)
    attribution = {k: attribute_ratio_change(weekly, v[0]) for k, v in windows.items()}
    margin_attr = {k: attribute_margin_change(weekly, params, v[0]) for k, v in windows.items()}
    cf = counterfactual_paths(weekly, params, "2026-07-03")

    tc_levels = [-75, -100, -125, -150, -175, -200, -225, -250, -300]
    acid_levels = [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800]
    matrix = regime_matrix(params, tc_levels, acid_levels, fx, float(latest["cu_price"]),
                           float(latest["silver_price"]), energy)

    dpaths = definition_paths(weekly, params)
    crossings = {c: _first_sustained_below(dpaths[c].dropna(), 1.0) for c in dpaths.columns}

    peak_date = weekly["acid_cny_t"].idxmax()
    snapshot = {
        "date": weekly.index[-1].date(),
        "tc_usd_dmt": float(latest["tc_usd_dmt"]),
        "acid_cny_t": float(latest["acid_cny_t"]),
        "acid_peak_cny_t": float(weekly["acid_cny_t"].max()),
        "acid_peak_date": peak_date.date(),
        "acid_change_from_peak_pct": float(latest["acid_cny_t"] / weekly["acid_cny_t"].max() - 1),
        "cushion_ratio": float(latest["acid_cushion_ratio"]),
    }
    return {
        "snapshot": snapshot,
        "latest_regime": cushion_regime(latest["acid_cushion_ratio"]),
        "attribution": attribution,
        "margin_attribution": margin_attr,
        "counterfactual": cf,
        "regime_matrix": matrix,
        "frontier_100_acid_cny": cushion_frontier_acid_cny(latest["tc_usd_dmt"], params, fx, 1.0),
        "definition_sensitivity": definition_sensitivity(weekly, params),
        "definition_paths": dpaths,
        "definition_crossings": crossings,
        "required_other_credit": implied_required_other_credit(weekly),
        "regional": regional_divergence(),
        "kamoa": kamoa_bridge(),
        "sulphur_parity": sulphur_parity(),
        "falsification": falsification_checks(weekly, params),
        "fx": fx,
    }


def render_strategy_text(s: dict) -> str:
    L = []
    w = L.append
    w("=" * 72)
    w("STRATEGY LAYER -- attribution, counterfactual, regimes, falsification")
    w("=" * 72)
    w(f"  Cushion regime now: {s['latest_regime']}   "
      f"(ABSORBING >=100% | ERODING 50-100% | EXHAUSTED <50%; judgment levels)")
    w("")
    w("  1. WHO IS DRIVING THE FALL IN THE CUSHION? (exact log decomposition)")
    for k, a in s["attribution"].items():
        w(f"     {k:<26} {a['start']} -> {a['end']}: ratio {a['ratio_start']*100:6.1f}% -> {a['ratio_end']*100:5.1f}%"
          f"   acid {a['acid_share']*100:5.1f}% | TC {a['tc_share']*100:5.1f}%   [{a['basis_start']}]")
    att = s["attribution"]
    since_apr, last4 = att["since April cushion peak"], att["last 4 weeks"]
    w(f"     Read: since the April peak the fall is {since_apr['tc_share']*100:.0f}% TC / {since_apr['acid_share']*100:.0f}% acid; "
      f"over the last 4 weeks it is {last4['acid_share']*100:.0f}% acid / {last4['tc_share']*100:.0f}% TC.")
    w("")
    w("  2. COUNTERFACTUAL -- acid held at its 2026-07-03 local-currency peak")
    e = s["counterfactual"].iloc[-1]
    w(f"     Cushion now: actual {e['actual']*100:.1f}% | flat-acid {e['cf_flat_acid']*100:.1f}% | "
      f"flat-TC {e['cf_flat_tc']*100:.1f}%")
    w(f"     Acid decline alone costs ${e['margin_cf_flat_acid']-e['margin_actual']:.0f}/t of concentrate in treatment margin "
      "(a CHANGE; the absolute margin level is uncalibrated and not reported)")
    m = s["margin_attribution"]["since July acid peak"]
    w(f"     Margin change since 2026-07-03 ({m['total_change']:.0f} $/t): TC {m['tc']:+.0f}, acid {m['acid']:+.0f}, "
      f"free metal {m['free_metal']:+.0f}, silver {m['silver']:+.0f}  (residual {m['residual']:+.2f})")
    w("")
    w("  3. HOW FRAGILE IS THE LEVEL? latest cushion under alternative definitions")
    ds = s["definition_sensitivity"]
    lo, hi = ds["cushion_ratio"].min(), ds["cushion_ratio"].max()
    w(f"     range across yield x RC x VAT basis: {lo*100:.0f}% - {hi*100:.0f}%  (headline definition TC only | ex-VAT: "
      f"{float(s['definition_paths']['TC only | ex-VAT'].iloc[-1])*100:.1f}%)")
    for c, d in s["definition_crossings"].items():
        w(f"     {c:<24} stays below 100% from {d.date() if d is not None else 'n/a'}")
    w("     Read: the DIRECTION is robust; the LEVEL (and the date 100% is lost) is definition-dependent.")
    w("")
    r = s["regional"]
    k = s["kamoa"]
    w("  4. REGIONAL DIVERGENCE")
    w(f"     As of {r['as_of']}: China domestic ${r['china_domestic_usd_t_as_quoted']:.0f}/t "
      f"(${r['china_domestic_usd_t_ex_vat']:.0f} ex-VAT, model basis) | Zambia ${r['exw_zambia_usd_t']:.0f} | "
      f"DRC ${r['exw_drc_usd_t']:.0f}  (DRC = {r['drc_over_china_ex_vat']:.1f}x China ex-VAT)")
    w(f"     Kamoa acid/opex coverage: Q1 {k['coverage_q1']*100:.0f}% -> Q2 {k['coverage_q2']*100:.0f}% "
      f"(acid price {k['acid_price_change_pct']*100:+.1f}%, credit/lb {k['credit_change_pct']*100:+.0f}%, opex/lb {k['opex_change_pct']*100:+.0f}% = Q1 partly capitalised)  "
      f"-> Q3 indicated {k['q3_coverage_mgmt_at_q2_opex']*100:.0f}%-{k['q3_coverage_implied_yield_at_q2_opex']*100:.0f}%")
    w("")
    w("  5. FALSIFICATION / MONITORING (pre-registered; thresholds are judgment levels)")
    for c in s["falsification"]:
        w(f"     {c['id']} [{c['direction']}] {c['status']}")
        w(f"         {c['condition']}")
        w(f"         now: {c['current']}")
    w("=" * 72)
    return "\n".join(L)


# ---------------------------------------------------------------------------
# self-checks (same runnable style as the rest of the project: python strategy_layer.py)
# ---------------------------------------------------------------------------
def _selfcheck_all():
    import model_a as ma
    out = ma.run_model_a_copper_acid_cushion()
    weekly, params = out["weekly"], out["params"]
    energy = out["energy_price_usd_mwh"]

    # (1) log decomposition is exact: acid leg + TC leg == ln(R_end/R_start)
    for start, _ in reference_windows(weekly).values():
        a = attribute_ratio_change(weekly, start)
        direct = float(np.log(a["ratio_end"] / a["ratio_start"]))
        assert abs(direct - a["log_change_total"]) < 1e-9, (start, direct, a["log_change_total"])
        assert abs(a["acid_share"] + a["tc_share"] - 1.0) < 1e-9

    # (2) margin attribution is additive (residual ~ 0)
    for start, _ in reference_windows(weekly).values():
        m = attribute_margin_change(weekly, params, start)
        assert abs(m["residual"]) < 1e-6, m

    # (3) counterfactuals coincide with actual at the reference date
    cf = counterfactual_paths(weekly, params, "2026-07-03")
    first = cf.iloc[0]
    assert abs(first["cf_flat_acid"] - first["actual"]) < 1e-9
    assert abs(first["cf_flat_tc"] - first["actual"]) < 1e-9
    assert abs(first["margin_cf_flat_acid"] - first["margin_actual"]) < 1e-9
    # holding acid flat can only raise the latest cushion vs actual when acid fell
    assert cf.iloc[-1]["cf_flat_acid"] > cf.iloc[-1]["actual"]

    # (4) regime-matrix cell at (latest TC, latest acid RMB) reproduces the monitor headline
    latest = weekly.iloc[-1]
    fx = fx_for(weekly.index[-1])
    mat = regime_matrix(params, [float(latest["tc_usd_dmt"])], [float(latest["acid_cny_t"])], fx,
                        float(latest["cu_price"]), float(latest["silver_price"]), energy)
    assert abs(mat["ratio"].iloc[0, 0] - latest["acid_cushion_ratio"]) < 1e-9
    assert abs(mat["margin"].iloc[0, 0] - latest["total_margin"]) < 1e-6

    # (5) frontier: at the frontier acid price the ratio is exactly 100%
    f = cushion_frontier_acid_cny(-200.0, params, fx)
    assert abs(_ratio(params.acid_yield * f / (1.0 + cad.ACID_QUOTE_BASIS["vat_rate_cn"]) / fx, -200.0) - 1.0) < 1e-9

    # (6) definition variant collapses to the headline when RC excluded, VAT stripped, default yield
    vat = cad.ACID_QUOTE_BASIS["vat_rate_cn"]
    v = cushion_ratio_variant(latest["acid_usd_t_quoted"], latest["tc_usd_dmt"], params, vat=vat)
    assert abs(v - latest["acid_cushion_ratio"]) < 1e-9
    # RC (negative) only ADDS to the drag, so including it can only lower the ratio
    assert cushion_ratio_variant(latest["acid_usd_t_quoted"], latest["tc_usd_dmt"], params, include_rc=True, vat=vat) < v
    # not stripping VAT can only raise the ratio
    assert cushion_ratio_variant(latest["acid_usd_t_quoted"], latest["tc_usd_dmt"], params, vat=0.0) > v

    # (7) Kamoa bridge: Q2 dip is NOT a price effect (price flat; credit rose; opex rose more)
    k = kamoa_bridge()
    assert abs(k["acid_price_change_pct"]) < 0.01
    assert k["credit_change_pct"] > 0 and k["opex_change_pct"] > k["credit_change_pct"]
    assert abs(k["log_price_leg"] + k["log_volume_per_lb_leg"] - k["log_credit_leg"]) < 1e-12
    assert k["q3_coverage_mgmt_at_q2_opex"] > 1.0 > k["coverage_q2"]

    # (7b) falsification rules behave as documented on synthetic frames
    def _frame(ratios, tc_status="cited", acid_status="cited"):
        idx = pd.date_range("2026-01-02", periods=len(ratios), freq="7D")
        return pd.DataFrame({"acid_cushion_ratio": ratios, "tc_usd_dmt": [-100.0] * len(ratios),
                             "tc_status": [tc_status] * len(ratios) if isinstance(tc_status, str) else tc_status,
                             "acid_status": [acid_status] * len(ratios) if isinstance(acid_status, str) else acid_status}, index=idx)
    byid = lambda df: {c["id"]: c for c in falsification_checks(df, params)}
    up2 = byid(_frame([0.9, 0.8, 0.85, 0.9]))                       # two consecutive rises on cited prints
    assert up2["C1"]["status"] == "TRIGGERED"
    flat_interp = _frame([0.9, 0.8, 0.85, 0.9], tc_status=["cited", "cited", "interpolated (grid-fill)", "cited"])
    assert byid(flat_interp)["C1"]["status"] != "TRIGGERED"        # a grid-fill week cannot start/stop 'erosion'
    assert byid(_frame([0.9, 0.8]))["C1"]["status"] == "NOT TESTABLE"
    assert byid(_frame([0.9, 0.7, 0.6, 0.55, 0.4]))["C3"]["status"].startswith("WATCHING")      # 1 week < 50%
    assert byid(_frame([0.9, 0.45, 0.44, 0.43, 0.42]))["C3"]["status"].startswith("IN SCOPE")   # 4 weeks < 50%
    assert byid(_frame([0.9, 0.8, 0.7, 0.6]))["C3"]["status"].startswith("NOT YET IN SCOPE")

    # (7c) a date in a quarter missing from the FX table must not crash (next data refresh lands in Q4-2026)
    assert fx_for("2026-10-02") == fx_for("2026-09-25")

    # (8) the whole layer runs
    s = run_strategy_layer(out)
    assert len(s["falsification"]) >= 6
    print("strategy_layer.py self-checks passed")


if __name__ == "__main__":
    _selfcheck_all()
    import model_a as ma
    print(render_strategy_text(run_strategy_layer(ma.run_model_a_copper_acid_cushion())))