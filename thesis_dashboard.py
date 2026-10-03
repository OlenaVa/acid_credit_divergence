"""
thesis_dashboard.py
====================
The "Thesis Dashboard" for the PRIMARY copper acid-cushion analysis --
REPLACES the binary "N of 5 conditions met" framework for this thesis.
thesis_monitor.py's original boolean-condition machinery is UNCHANGED and
still used for the SECONDARY zinc-vs-copper cross-metal check (see
model_a.py's module docstring); it was never wrong for that narrower,
genuinely binary-ish question ("is zinc curtailing before copper"). It was
the wrong shape for THIS thesis: a Thesis Dashboard of 7 categorical
states, each with 3 qualitative buckets, plus a narrative status block.
Forcing PMI/COMEX/zinc into pass/fail conditions ("the demand signal isn't
clean" -- the source article's own words) would misrepresent evidence that
is genuinely mixed as if it were decisive. Falsification conditions for the
thesis as a whole live in strategy_layer.falsification_checks().

Each `condition_*` function below returns (state: str, detail: str) --
the categorical label plus a one-line, cited reason, so the label is never
presented without its evidence attached. Thresholds are heuristic and
DOCUMENTED, not fitted or backtested -- this is a thesis-monitoring tool
for a written research note, not a signal generator (same philosophy
thesis_monitor.py's original module docstring stated for the boolean
version; it applies here too).
"""

from __future__ import annotations

from dataclasses import dataclass

import copper_acid_data as cad


@dataclass
class DashboardConfig:
    """All thresholds used by the condition_* functions below, collected
    in one place so they can be overridden and so nobody has to go
    hunting through function bodies to find a magic number."""
    tc_extreme_usd_dmt: float = -150.0          # at/below this level, TC regime = EXTREME
    tc_improving_9w_usd_dmt: float = 15.0        # 9-week level change more positive than this = IMPROVING
    cushion_shrink_9w_ppt: float = -0.05         # 9-week ratio-point change below this = SHRINKING
    cushion_expand_9w_ppt: float = 0.05          # above this = EXPANDING
    margin_deteriorate_9w_usd: float = -15.0     # 9-week treatment-margin change below this = DETERIORATING
    margin_improve_9w_usd: float = 15.0          # above this = IMPROVING
    pmi_gap_mixed_threshold: float = 1.0         # official-vs-independent PMI gap (points) above this = MIXED, not one clean read
    discount_threshold_usd_t: float = -20.0      # realized-vs-benchmark spread below this = DISCOUNT
    premium_threshold_usd_t: float = 20.0        # above this = PREMIUM


def condition_tc_regime(latest_tc: float, tc_9w_change: float, cfg: DashboardConfig = DashboardConfig()) -> tuple[str, str]:
    if latest_tc <= cfg.tc_extreme_usd_dmt:
        detail = (
            f"TC at ${latest_tc:.2f}/dmt, at/below the ${cfg.tc_extreme_usd_dmt:.0f}/dmt "
            f"extreme-regime threshold; 9-week change ${tc_9w_change:+.2f}/dmt "
            f"({'still deteriorating' if tc_9w_change < 0 else 'stabilising/improving within an extreme regime'})."
        )
        return "EXTREME", detail
    if tc_9w_change >= cfg.tc_improving_9w_usd_dmt:
        return "IMPROVING", f"TC at ${latest_tc:.2f}/dmt, up ${tc_9w_change:+.2f}/dmt over 9 weeks."
    return "STABLE", f"TC at ${latest_tc:.2f}/dmt, roughly flat over 9 weeks (${tc_9w_change:+.2f}/dmt)."


def condition_acid_cushion(cushion_ratio: float, cushion_9w_ppt: float, cfg: DashboardConfig = DashboardConfig()) -> tuple[str, str]:
    if cushion_9w_ppt <= cfg.cushion_shrink_9w_ppt:
        return "SHRINKING", (
            f"Acid Cushion Ratio at {cushion_ratio*100:.1f}%, down "
            f"{abs(cushion_9w_ppt)*100:.1f}pp over 9 weeks -- acid revenue "
            f"is covering a shrinking share of the TC drag."
        )
    if cushion_9w_ppt >= cfg.cushion_expand_9w_ppt:
        return "EXPANDING", (
            f"Acid Cushion Ratio at {cushion_ratio*100:.1f}%, up "
            f"{cushion_9w_ppt*100:.1f}pp over 9 weeks."
        )
    return "STABLE", f"Acid Cushion Ratio at {cushion_ratio*100:.1f}%, roughly flat over 9 weeks."


def condition_treatment_margin(margin_now: float, margin_9w_change: float, cfg: DashboardConfig = DashboardConfig()) -> tuple[str, str]:
    if margin_9w_change <= cfg.margin_deteriorate_9w_usd:
        return "DETERIORATING", (
            f"Treatment margin (TC + free metal + byproducts - costs) at "
            f"${margin_now:.0f}/t concentrate, down ${abs(margin_9w_change):.0f}/t "
            f"over 9 weeks."
        )
    if margin_9w_change >= cfg.margin_improve_9w_usd:
        return "IMPROVING", f"Treatment margin at ${margin_now:.0f}/t, up ${margin_9w_change:.0f}/t over 9 weeks."
    return "STABLE", f"Treatment margin at ${margin_now:.0f}/t, roughly flat over 9 weeks."


def condition_physical_response() -> tuple[str, str]:
    """Not derived from a threshold -- this is a qualitative read of
    copper_acid_data.PHYSICAL_RESPONSE_EVIDENCE, which is itself a small,
    explicitly-cited evidence dict, not a metric. See that dict for the
    two pieces of evidence behind this call."""
    return "EMERGING", cad.PHYSICAL_RESPONSE_EVIDENCE["reading"]


def condition_acid_market_regime() -> tuple[str, str]:
    """The source article itself concludes this is unclear ('the data
    available right now doesn't cleanly settle which is dominant -- that's
    the honest state of the evidence, not a gap to paper over') -- this
    function reports that conclusion rather than re-deriving a false
    precision from the same evidence the article already weighed."""
    return "UNCLEAR", cad.SULPHUR_TRADE_CONTEXT["note"]


def condition_demand(cfg: DashboardConfig = DashboardConfig()) -> tuple[str, str]:
    ctx = cad.MARKET_CONTEXT_SEPT_2026
    gap = abs(ctx["china_ratingdog_manufacturing_pmi_aug2026"] - ctx["china_nbs_manufacturing_pmi_aug2026"])
    if gap > cfg.pmi_gap_mixed_threshold:
        return "MIXED", (
            f"NBS official PMI {ctx['china_nbs_manufacturing_pmi_aug2026']} "
            f"(contractionary) vs RatingDog PMI "
            f"{ctx['china_ratingdog_manufacturing_pmi_aug2026']} (expansionary), "
            f"a {gap:.1f}pt gap -- 'Chinese demand is collapsing' is too "
            f"simple a read on this alone. COMEX inventories at a record "
            f"{ctx['comex_cu_inventory_record_t']:,}t partly reflect "
            f"tariff-driven trade-flow positioning, not pure scarcity or "
            f"surplus."
        )
    avg = (ctx["china_ratingdog_manufacturing_pmi_aug2026"] + ctx["china_nbs_manufacturing_pmi_aug2026"]) / 2
    return ("SUPPORTIVE" if avg >= 50 else "WEAK"), f"PMIs agree within {gap:.1f}pt, average {avg:.1f}."


def condition_regional_realization(spread_usd_t: float, cfg: DashboardConfig = DashboardConfig()) -> tuple[str, str]:
    if spread_usd_t <= cfg.discount_threshold_usd_t:
        return "DISCOUNT", (
            f"Kamoa-Kakula's realized contract price sits ${abs(spread_usd_t):.0f}/t "
            f"BELOW the SMM EXW DRC regional benchmark -- despite an "
            f"integrated mine-gate structure that should, in principle, "
            f"help. 'Integration equals a pricing edge' is not supported "
            f"by this data point (source article's own framing)."
        )
    if spread_usd_t >= cfg.premium_threshold_usd_t:
        return "PREMIUM", f"Realized price ${spread_usd_t:.0f}/t above the regional benchmark."
    return "PARITY", f"Realized price within ${cfg.premium_threshold_usd_t:.0f}/t of the regional benchmark."


def build_thesis_dashboard(model_a_out: dict, model_c_out: dict, cfg: DashboardConfig = DashboardConfig()) -> dict:
    """
    Assembles the full 7-category Thesis Dashboard plus the narrative
    "CURRENT THESIS STATUS" block, from model_a.run_model_a_copper_acid_
    cushion()'s output and model_c.run_model_c_realized_acid_economics()'s
    output. Deliberately returns NO single boolean/score -- see module
    docstring for why collapsing this into "N of 7 confirmed" would
    misrepresent evidence the source article itself calls mixed/unclear.
    """
    latest = model_a_out["latest"]
    trend = model_a_out["trend"]

    tc_state, tc_detail = condition_tc_regime(latest["tc_usd_dmt"], trend["tc_9w_usd_dmt_change"], cfg)
    cushion_state, cushion_detail = condition_acid_cushion(latest["acid_cushion_ratio"], trend["cushion_9w_ppt"], cfg)
    # 9-week treatment-margin change -- computed here rather than added to
    # model_a's trend dict, since it's dashboard-specific and keeps
    # model_a.py focused on the raw series rather than every downstream
    # consumer's derived thresholds.
    weekly = model_a_out["weekly"]
    margin_9w_change = (
        weekly["total_margin"].iloc[-1] - weekly["total_margin"].iloc[-1 - 9]
        if len(weekly) > 9 else float("nan")
    )
    margin_state, margin_detail = condition_treatment_margin(latest["total_margin"], margin_9w_change, cfg)
    physical_state, physical_detail = condition_physical_response()
    acid_regime_state, acid_regime_detail = condition_acid_market_regime()
    demand_state, demand_detail = condition_demand(cfg)
    spread = model_c_out["realized_vs_benchmark"]["spread_usd_t"]
    regional_state, regional_detail = condition_regional_realization(spread, cfg)

    dashboard = {
        "1_tc_regime": {"state": tc_state, "detail": tc_detail},
        "2_acid_cushion": {"state": cushion_state, "detail": cushion_detail},
        "3_treatment_margin": {"state": margin_state, "detail": margin_detail},
        "4_physical_response": {"state": physical_state, "detail": physical_detail},
        "5_acid_market_regime": {"state": acid_regime_state, "detail": acid_regime_detail},
        "6_demand": {"state": demand_state, "detail": demand_detail},
        "7_regional_realization": {"state": regional_state, "detail": regional_detail},
    }

    mechanism_consistent = tc_state == "EXTREME" and cushion_state == "SHRINKING"
    status = {
        "observed": f"TC {tc_state.lower()}, acid cushion {cushion_state.lower()}",
        "mechanism": "CONSISTENT" if mechanism_consistent else "NOT YET ALIGNED",
        "physical_response": f"{physical_state} (not yet CONFIRMED)" if physical_state != "CONFIRMED" else "CONFIRMED",
        "cause_of_acid_decline": acid_regime_state,
        "forward_catalyst": (
            "Acid continues lower while TC remains near its floor -- the "
            "gap between an acid-advantaged smelter and an exposed one "
            "widens on its own (source article's own closing framing)."
            if mechanism_consistent else
            "Mechanism not yet aligned -- re-check once both legs move the same direction."
        ),
    }

    return {"dashboard": dashboard, "status": status, "config": cfg}
