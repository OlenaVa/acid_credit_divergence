"""
acid_cushion_monitor.py
========================
"Copper Acid Cushion Monitor" -- the project's new PRIMARY output, per the
2026-09-16 review (section 17): replaces the old "Zinc vs Copper / Acid* /
Threshold gap / 5 conditions" headline format with the format the review
actually asked for:

    Copper Acid Cushion Monitor
    TC                    -$200/t
    Acid credit           +$X/t
    Acid cushion           XX%

    Acid price:  1M -X%  3M -X%  9W -X%
    Cushion:     9W -X%  13W -X%
    Stress:      Acid -10/-20/-30% -> change in margin

    Status: CUSHION {SHRINKING|EXPANDING|STABLE}

    Cross-check: Zinc / Kamoa / Regional acid / Sulphur / Demand / COMEX-LME

Ties together model_a.run_model_a_copper_acid_cushion() (core),
model_b.run_model_b_acid_robustness() (robustness), model_c.
run_model_c_realized_acid_economics() (Kamoa realized economics) and
thesis_dashboard.build_thesis_dashboard() (the 7-category qualitative
read) into one report. Run this file directly (`python
acid_cushion_monitor.py`) for the current read using real data through
this project's data-collection date; see docs/METHODOLOGY.md for exactly which
weeks are cited vs interpolated.
"""

from __future__ import annotations

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import copper_acid_data as cad
import model_a as ma
import model_b as mb
import model_c as mc
import thesis_dashboard as td
import strategy_layer as sl
import strategy_charts as sc


def build_monitor() -> dict:
    """Runs the full real-data pipeline (A -> B -> C -> Dashboard) and
    returns everything as structured data; render_monitor_text() below
    turns this into the printable report. Split into two functions so a
    caller who wants the numbers (e.g. to write output/*.csv) doesn't have
    to parse them back out of a formatted string."""
    out_a = ma.run_model_a_copper_acid_cushion()
    out_b = mb.run_model_b_acid_robustness(out_a["weekly"], out_a["params"], out_a["energy_price_usd_mwh"])
    out_c = mc.run_model_c_realized_acid_economics()
    dash = td.build_thesis_dashboard(out_a, out_c)
    strategy = sl.run_strategy_layer(out_a)
    return {"model_a": out_a, "model_b": out_b, "model_c": out_c, "dashboard": dash, "strategy": strategy}


def _fmt_pct(x: float) -> str:
    return "n/a" if pd.isna(x) else f"{x*100:+.1f}%"


def _fmt_usd(x: float, decimals=0) -> str:
    return "n/a" if pd.isna(x) else f"${x:,.{decimals}f}"


def render_monitor_text(result: dict) -> str:
    a, b, c, dash = result["model_a"], result["model_b"], result["model_c"], result["dashboard"]
    latest = a["latest"]
    trend = a["trend"]
    stress = a["stress"]
    latest_date = a["weekly"].index[-1].date()

    lines = []
    L = lines.append
    L("=" * 72)
    L(f"COPPER ACID CUSHION MONITOR -- as of {latest_date} "
      f"(TC status: {latest['tc_status']}, acid status: {latest['acid_status']})")
    L("=" * 72)
    L(f"  TC                {_fmt_usd(latest['tc_usd_dmt'])}/dmt")
    L(f"  Acid credit       +{_fmt_usd(latest['acid_contribution'])}/t concentrate")
    L(f"  Acid cushion       {latest['acid_cushion_ratio']*100:.1f}%   (acid credit ex-VAT / |TC|; "
      f"regime: {sl.cushion_regime(latest['acid_cushion_ratio'])}; RC/VAT sensitivity in the Strategy Layer below)")
    L("")
    trend_basis = a["trend_basis"]
    star = lambda b: "*" if "interpolated" in str(b) else ""
    L(f"  Acid price:   1M {_fmt_pct(trend['acid_price_1m_pct'])}{star(trend_basis['acid_price_1m_pct'])}   "
      f"3M {_fmt_pct(trend['acid_price_3m_pct'])}{star(trend_basis['acid_price_3m_pct'])}   "
      f"9W {_fmt_pct(trend['acid_price_9w_pct'])}{star(trend_basis['acid_price_9w_pct'])}")
    L(f"  TC level chg: 1M {_fmt_usd(trend['tc_1m_usd_dmt_change'])}/dmt{star(trend_basis['tc_1m_usd_dmt_change'])}   "
      f"9W {_fmt_usd(trend['tc_9w_usd_dmt_change'])}/dmt{star(trend_basis['tc_9w_usd_dmt_change'])}")
    L(f"  Cushion:      9W {trend['cushion_9w_ppt']*100:+.1f}pp{star(trend_basis['cushion_9w_ppt'])}   "
      f"13W {trend['cushion_13w_ppt']*100:+.1f}pp{star(trend_basis['cushion_13w_ppt'])}")
    flagged = [k for k, v in trend_basis.items() if "interpolated" in str(v)]
    if flagged:
        L(f"  * reference point of {', '.join(flagged)} is an interpolated grid-fill week, not a cited print.")
    else:
        L("  All trend reference points are cited SMM prints (no interpolated reference week).")
    L("")
    L("  Stress test (acid price shock, TC/metal price held at latest snapshot):")
    stress0 = stress.loc[stress["acid_shock_pct"].abs().idxmin()]
    for _, row in stress.iterrows():
        L(f"    Acid {row['acid_shock_pct']*100:+.0f}%  ->  margin change {_fmt_usd(row['total_margin']-stress0['total_margin'])}/t "
          f"(cushion {row['acid_cushion_ratio']*100:.1f}%)")
    L("")
    yield_sens = a["yield_sensitivity"]
    L(f"  Acid-yield sensitivity (TC/acid price/metal price held at latest snapshot; "
      f"default acid_yield={a['params'].acid_yield}):")
    for _, row in yield_sens.iterrows():
        tag = " <- default" if abs(row["acid_yield"] - a["params"].acid_yield) < 1e-9 else ""
        L(f"    acid_yield {row['acid_yield']:.4f}  ->  cushion {row['acid_cushion_ratio']*100:5.1f}%{tag}")
    L("")
    cushion_state = dash["dashboard"]["2_acid_cushion"]["state"]
    L(f"  STATUS: CUSHION {cushion_state}")
    L(f"  {dash['status']['forward_catalyst']}")
    L("")
    L("-" * 72)
    L("THESIS DASHBOARD")
    L("-" * 72)
    for key, val in dash["dashboard"].items():
        label = key.split("_", 1)[1].replace("_", " ").title()
        L(f"  {label:<22} {val['state']}")
    L("")
    L(f"  Observed:              {dash['status']['observed']}")
    L(f"  Mechanism:             {dash['status']['mechanism']}")
    L(f"  Physical response:     {dash['status']['physical_response']}")
    L(f"  Cause of acid decline: {dash['status']['cause_of_acid_decline']}")
    L(f"  Forward catalyst:      {dash['status']['forward_catalyst']}")
    L("")
    L("-" * 72)
    L("CROSS-CHECK (secondary/corroborating evidence -- does not move the")
    L("dashboard above; see docs/METHODOLOGY.md; zinc/PMI/COMEX stay out of the dashboard because the evidence is mixed)")
    L("-" * 72)
    zn = cad.MARKET_CONTEXT_SEPT_2026["zinc"]
    L(f"  Zinc:            spot TC {zn['smm_spot_zn_tc_aug2026_usd_dmt']:.0f}/dmt (ATL) vs "
      f"{zn['zn_tc_annual_benchmark_2026_usd_dmt']:.0f}/dmt annual benchmark -- same by-product-cushion")
    L("                   mechanism (silver + acid) at an even more extreme TC level.")
    kq = c["kamoa_quarterly"]
    kb = sl.kamoa_bridge()
    L(f"  Kamoa-Kakula:    acid/opex coverage Q1 {kq.loc['2026-Q1','acid_cushion_ratio']*100:.1f}% -> "
      f"Q2 {kq.loc['2026-Q2','acid_cushion_ratio']*100:.1f}% ({c['q1_to_q2_cushion_change_ppt']*100:+.1f}pp) -- NOT an acid-price effect")
    L(f"                   (realised acid price {kb['acid_price_change_pct']*100:+.1f}%, credit/lb {kb['credit_change_pct']*100:+.0f}%, smelter opex/lb {kb['opex_change_pct']*100:+.0f}% --")
    L("                   Ivanhoe says Q1 opex was understated by partial capitalisation of smelter costs);")
    L(f"                   management indicates ~{kb['q3_coverage_mgmt_at_q2_opex']*100:.0f}% coverage in Q3 (implied-yield cross-check {kb['q3_coverage_implied_yield_at_q2_opex']*100:.0f}%).")
    L("                   Kamoa is evidence of an EX-CHINA divergence from China's domestic cushion, not of a global shrinking cushion.")
    L("                   (Different denominator from the China Acid/|TC| ratio: Acid Credit / TOTAL smelter opex -- not comparable number-for-number.)")
    acid_src = b["acid_price_source"]
    L(f"  Regional acid:   (as of {b['acid_price_source_reference_date']}, the regional benchmark's own "
      f"latest print -- domestic TC/acid series is newer, {b['domestic_series_latest_date']})")
    L("                   " + "; ".join(
        f"{r.acid_price_source.replace('smm_', '').replace('_', ' ')} "
        f"acid/|TC| {r.acid_cushion_ratio*100:.0f}%" for r in acid_src.itertuples()
    ))
    L(f"  Sulphur:         China H2SO4 exports collapsed "
      f"{cad.SULPHUR_TRADE_CONTEXT['china_h2so4_exports_may2026_kt']:.0f}kt (May) -> "
      f"{cad.SULPHUR_TRADE_CONTEXT['china_h2so4_exports_jun2026_t']:.0f}t (Jun), still near-zero in Jul.")
    L(f"  Demand:          NBS PMI {cad.MARKET_CONTEXT_SEPT_2026['china_nbs_manufacturing_pmi_aug2026']} vs "
      f"RatingDog {cad.MARKET_CONTEXT_SEPT_2026['china_ratingdog_manufacturing_pmi_aug2026']} -- MIXED, not resolved.")
    L(f"  COMEX/LME:       COMEX Cu inventory record "
      f"{cad.MARKET_CONTEXT_SEPT_2026['comex_cu_inventory_record_t']:,}t, partly tariff-driven positioning.")
    L("")
    L("-" * 72)
    L("ROBUSTNESS (Model B -- does the reading survive a different source?)")
    L("-" * 72)
    L(f"  Acid price source (same TC, different acid market, both snapshotted at "
      f"{b['acid_price_source_reference_date']}):")
    for r in acid_src.itertuples():
        L(f"    {r.acid_price_source:<22} ${r.acid_price_usd_t:>7.1f}/t  ->  acid/|TC| {r.acid_cushion_ratio*100:6.1f}%")
    L(f"  {b['caveat']}")
    L("  TC index provider (same acid price, different TC source, nearest-date snapshot):")
    for r in b["tc_index_provider"].itertuples():
        L(f"    {r.provider:<48} {r.date}  TC ${r.tc_usd_dmt:.2f}/dmt")
    L(f"    (agreement: ${b['tc_provider_agreement_usd_dmt']:.2f}/dmt apart)")
    L("=" * 72)
    L("")
    L(sl.render_strategy_text(result["strategy"]))
    return "\n".join(lines)


def plot_monitor(result: dict, out_path: str = "output/copper_acid_cushion.png") -> str:
    """Kept for backward compatibility; the implementation moved to strategy_charts.plot_monitor
    (per-series provenance markers -- the previous version drew acid/ratio markers at the TC
    series' cited dates)."""
    return sc.plot_monitor(result["model_a"]["weekly"], out_path)


if __name__ == "__main__":
    import os
    result = build_monitor()
    print(render_monitor_text(result))

    os.makedirs("output/tables", exist_ok=True)
    st = result["strategy"]
    _lvl = ["margin_ex_acid", "total_margin"]      # absolute margin levels are uncalibrated -> not exported
    result["model_a"]["weekly"].drop(columns=_lvl).to_csv("output/tables/copper_acid_cushion_weekly.csv", index_label="date")
    result["model_a"]["stress"].drop(columns=_lvl).to_csv("output/tables/copper_acid_cushion_stress.csv", index=False)
    result["model_a"]["yield_sensitivity"].drop(columns=["total_margin"], errors="ignore").to_csv("output/tables/copper_acid_cushion_yield_sensitivity.csv", index=False)
    result["model_c"]["kamoa_quarterly"].to_csv("output/tables/kamoa_kakula_quarterly.csv")
    st["counterfactual"].drop(columns=["margin_actual", "margin_cf_flat_acid"]).assign(
        acid_effect_on_margin_usd_t=st["counterfactual"]["margin_cf_flat_acid"] - st["counterfactual"]["margin_actual"]
    ).to_csv("output/tables/counterfactual_flat_acid.csv", index_label="date")
    pd.DataFrame(st["attribution"]).T.to_csv("output/tables/cushion_attribution.csv", index_label="window")
    pd.DataFrame(st["margin_attribution"]).T.to_csv("output/tables/margin_attribution.csv", index_label="window")
    st["regime_matrix"]["ratio"].to_csv("output/tables/regime_matrix_cushion_ratio.csv")
    st["definition_sensitivity"].to_csv("output/tables/definition_sensitivity.csv", index=False)
    pd.DataFrame(st["falsification"]).to_csv("output/tables/falsification_checks.csv", index=False)
    charts = sc.make_all(result)
    print("\n[written: output/tables/*.csv (weekly, stress, yield/definition sensitivity, attribution, counterfactual, "
          "regime matrix, falsification, Kamoa) and charts: " + ", ".join(charts) + "]")
