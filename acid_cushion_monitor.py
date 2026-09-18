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
    Margin ex-acid         $X/t
    Total margin           $X/t

    Acid price:  1M -X%  3M -X%  9W -X%
    Cushion:     9W -X%  13W -X%
    Stress:      Acid -10/-20/-30% -> margin -$X

    Status: CUSHION {SHRINKING|EXPANDING|STABLE}

    Cross-check: Zinc / Kamoa / Regional acid / Sulphur / Demand / COMEX-LME

Ties together model_a.run_model_a_copper_acid_cushion() (core),
model_b.run_model_b_acid_robustness() (robustness), model_c.
run_model_c_realized_acid_economics() (Kamoa realized economics) and
thesis_dashboard.build_thesis_dashboard() (the 7-category qualitative
read) into one report. Run this file directly (`python
acid_cushion_monitor.py`) for the current read using real data through
this project's data-collection date; see README.md for exactly which
weeks are cited vs interpolated.
"""

from __future__ import annotations

import pandas as pd

import copper_acid_data as cad
import model_a as ma
import model_b as mb
import model_c as mc
import thesis_dashboard as td


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
    return {"model_a": out_a, "model_b": out_b, "model_c": out_c, "dashboard": dash}


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
    L(f"  Acid cushion       {latest['acid_cushion_ratio']*100:.1f}%")
    L(f"  Margin ex-acid     {_fmt_usd(latest['margin_ex_acid'])}/t  (treatment basis -- see README)")
    L(f"  Total margin       {_fmt_usd(latest['total_margin'])}/t  (treatment basis -- see README)")
    L("")
    L(f"  Acid price:   1M {_fmt_pct(trend['acid_price_1m_pct'])}   "
      f"3M {_fmt_pct(trend['acid_price_3m_pct'])}   9W {_fmt_pct(trend['acid_price_9w_pct'])}")
    L(f"  TC level chg: 1M {_fmt_usd(trend['tc_1m_usd_dmt_change'])}/dmt   "
      f"9W {_fmt_usd(trend['tc_9w_usd_dmt_change'])}/dmt")
    L(f"  Cushion:      9W {trend['cushion_9w_ppt']*100:+.1f}pp   "
      f"13W {trend['cushion_13w_ppt']*100:+.1f}pp")
    L("")
    L("  Stress test (acid price shock, TC/metal price held at latest snapshot):")
    for _, row in stress.iterrows():
        L(f"    Acid {row['acid_shock_pct']*100:+.0f}%  ->  total margin {_fmt_usd(row['total_margin'])}/t "
          f"(cushion {row['acid_cushion_ratio']*100:.1f}%)")
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
    L("dashboard above; see README.md for why zinc/PMI/COMEX are kept out)")
    L("-" * 72)
    zn = cad.MARKET_CONTEXT_SEPT_2026["zinc"]
    L(f"  Zinc:            spot TC {zn['smm_spot_zn_tc_aug2026_usd_dmt']:.0f}/dmt (ATL) vs "
      f"{zn['zn_tc_annual_benchmark_2026_usd_dmt']:.0f}/dmt annual benchmark -- same by-product-cushion")
    L("                   mechanism (silver + acid) at an even more extreme TC level.")
    kq = c["kamoa_quarterly"]
    L(f"  Kamoa-Kakula:    cushion ratio Q1 {kq.loc['2026-Q1','acid_cushion_ratio']*100:.1f}% -> "
      f"Q2 {kq.loc['2026-Q2','acid_cushion_ratio']*100:.1f}% "
      f"({c['q1_to_q2_cushion_change_ppt']*100:+.1f}pp) -- narrowing visible in its OWN")
    L("                   disclosed numbers, ahead of the SMM index-level shrinkage.")
    acid_src = b["acid_price_source"]
    L("  Regional acid:   " + "; ".join(
        f"{r.acid_price_source.replace('smm_', '').replace('_', ' ')} "
        f"cushion {r.acid_cushion_ratio*100:.0f}%" for r in acid_src.itertuples()
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
    L("  Acid price source (same TC, different acid market):")
    for r in acid_src.itertuples():
        L(f"    {r.acid_price_source:<22} ${r.acid_price_usd_t:>7.1f}/t  ->  cushion {r.acid_cushion_ratio*100:6.1f}%")
    L(f"  {b['caveat']}")
    L("  TC index provider (same acid price, different TC source, nearest-date snapshot):")
    for r in b["tc_index_provider"].itertuples():
        L(f"    {r.provider:<48} {r.date}  TC ${r.tc_usd_dmt:.2f}/dmt")
    L(f"    (agreement: ${b['tc_provider_agreement_usd_dmt']:.2f}/dmt apart)")
    L("=" * 72)
    return "\n".join(lines)


if __name__ == "__main__":
    result = build_monitor()
    print(render_monitor_text(result))

    import os
    os.makedirs("output", exist_ok=True)
    result["model_a"]["weekly"].to_csv("output/copper_acid_cushion_weekly.csv")
    result["model_a"]["stress"].to_csv("output/copper_acid_cushion_stress.csv", index=False)
    result["model_c"]["kamoa_quarterly"].to_csv("output/kamoa_kakula_quarterly.csv")
    print("\n[written: output/copper_acid_cushion_weekly.csv, "
          "output/copper_acid_cushion_stress.csv, output/kamoa_kakula_quarterly.csv]")
