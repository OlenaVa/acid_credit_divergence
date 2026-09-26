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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
    trend_basis = a["trend_basis"]
    L(f"  Acid price:   1M {_fmt_pct(trend['acid_price_1m_pct'])}   "
      f"3M {_fmt_pct(trend['acid_price_3m_pct'])}   "
      f"9W {_fmt_pct(trend['acid_price_9w_pct'])}*")
    L(f"  TC level chg: 1M {_fmt_usd(trend['tc_1m_usd_dmt_change'])}/dmt   "
      f"9W {_fmt_usd(trend['tc_9w_usd_dmt_change'])}/dmt*")
    L(f"  Cushion:      9W {trend['cushion_9w_ppt']*100:+.1f}pp*   "
      f"13W {trend['cushion_13w_ppt']*100:+.1f}pp")
    L(f"  *9W figures' reference point ({a['weekly'].index[-1 - 9].date()}) has no direct SMM print "
      f"for TC/acid -- status: {trend_basis['tc_9w_usd_dmt_change']} / "
      f"{trend_basis['acid_price_9w_pct']}. 1M/3M/13W reference points are all real cited prints.")
    L("")
    L("  Stress test (acid price shock, TC/metal price held at latest snapshot):")
    for _, row in stress.iterrows():
        L(f"    Acid {row['acid_shock_pct']*100:+.0f}%  ->  total margin {_fmt_usd(row['total_margin'])}/t "
          f"(cushion {row['acid_cushion_ratio']*100:.1f}%)")
    L("")
    yield_sens = a["yield_sensitivity"]
    L(f"  Acid-yield sensitivity (TC/acid price/metal price held at latest snapshot; "
      f"default acid_yield={a['params'].acid_yield}):")
    for _, row in yield_sens.iterrows():
        tag = " <- default" if abs(row["acid_yield"] - a["params"].acid_yield) < 1e-9 else ""
        L(f"    acid_yield {row['acid_yield']:.4f}  ->  cushion {row['acid_cushion_ratio']*100:5.1f}%   "
          f"total margin {_fmt_usd(row['total_margin'])}/t{tag}")
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
    L(f"  Kamoa-Kakula:    acid/OPEX coverage* Q1 {kq.loc['2026-Q1','acid_cushion_ratio']*100:.1f}% -> "
      f"Q2 {kq.loc['2026-Q2','acid_cushion_ratio']*100:.1f}% "
      f"({c['q1_to_q2_cushion_change_ppt']*100:+.1f}pp) -- narrowing visible in its OWN")
    L("                   disclosed numbers, ahead of the SMM index-level shrinkage.")
    L("                   *Kamoa's own ratio is Acid Credit / TOTAL SMELTER OPEX (its disclosure has no TC")
    L("                   line) -- a different, broader denominator than the 'Acid cushion' % above, which")
    L("                   is Acid Credit / |TC| for the generic benchmark smelter. Not directly comparable")
    L("                   number-for-number; both point the same direction (narrowing), which is the read.")
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
    return "\n".join(lines)


def plot_monitor(result: dict, out_path: str = "output/copper_acid_cushion.png") -> str:
    """
    REAL-data chart, added 2026-09-26. Before this, the only chart output
    anywhere in this project was demo.py's SYNTHETIC pair
    (demo_margins.png / demo_monitor.png) -- a real-data run had tables
    and console text only. That's not a bug in demo.py (it's an
    intentional, clearly-labelled, zero-dependency pipeline smoke test --
    see its own docstring), but it meant every chart a reviewer could see
    was fake, which is confusing on its own even with correct labels.
    This is the fix: a real chart, built entirely from
    `copper_acid_data.py`'s cited weekly series, that regenerates
    automatically -- literally, just by running this file again -- every
    time a new week's SMM print is added there. No separate "refresh
    the chart" step exists or is needed.

    Two panels:
      1. TC (USD/dmt) and acid price (USD/t) over the full real weekly
         grid.
      2. Acid Cushion Ratio (%) over the same grid, with a 100% reference
         line (acid credit fully offsetting TC).
    In both, a THIN LINE runs through every grid point (cited AND
    interpolated alike, for visual continuity), while filled MARKERS are
    drawn only at points genuinely tagged "cited" / "cited-approx" --
    exactly the observed-vs-interpolated distinction from this project's
    2026-09-26 review pass (see model_a.py's `trend_basis`), made visible
    rather than only readable in a status column.
    """
    weekly = result["model_a"]["weekly"]
    latest_date = weekly.index[-1].date()
    is_observed = weekly["tc_status"].isin(["cited", "cited-approx"])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    fig.suptitle(
        f"Copper acid-cushion thesis -- REAL SMM weekly data through {latest_date}",
        fontsize=11, fontweight="bold",
    )

    ax1.plot(weekly.index, weekly["tc_usd_dmt"], color="tab:blue", lw=1.2, label="TC (USD/dmt)")
    ax1.scatter(weekly.index[is_observed], weekly["tc_usd_dmt"][is_observed],
                color="tab:blue", s=18, zorder=3, label="TC -- cited print")
    ax1.axhline(0, color="grey", lw=0.8)
    ax1.set_ylabel("TC, USD/dmt")
    ax1_r = ax1.twinx()
    ax1_r.plot(weekly.index, weekly["acid_usd_t"], color="tab:red", lw=1.2, label="Acid price (USD/t)")
    ax1_r.scatter(weekly.index[is_observed], weekly["acid_usd_t"][is_observed],
                  color="tab:red", s=18, zorder=3, marker="s", label="Acid -- cited print")
    ax1_r.set_ylabel("Acid price, USD/t")
    ax1.set_title("TC vs acid price (markers = real SMM print; line = incl. interpolated grid-fill weeks)")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines1r, labels1r = ax1_r.get_legend_handles_labels()
    # Attached to ax1_r (the twin axis), not ax1: twin axes stack ON TOP of
    # the axis they were created from, so a legend attached to ax1 render
    # BELOW ax1_r's own plotted lines and gets visually cut through by
    # them. Attaching it to ax1_r instead puts the legend on top, as
    # intended.
    ax1_r.legend(lines1 + lines1r, labels1 + labels1r, loc="lower left",
                 fontsize=7.5, framealpha=0.95, handlelength=1.5, labelspacing=0.4)

    ax2.plot(weekly.index, weekly["acid_cushion_ratio"] * 100, color="tab:green", lw=1.2)
    ax2.scatter(weekly.index[is_observed], weekly["acid_cushion_ratio"][is_observed] * 100,
                color="tab:green", s=18, zorder=3, label="Cited print")
    ax2.axhline(100, color="grey", lw=0.8, ls="--", label="100% (acid fully offsets TC)")
    ax2.set_ylabel("Acid Cushion Ratio, %")
    ax2.set_title("Acid Cushion Ratio = Acid Credit / |TC| over time")
    ax2.legend(loc="lower left", fontsize=8)

    plt.tight_layout(rect=(0, 0, 1, 0.96))
    plt.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


if __name__ == "__main__":
    result = build_monitor()
    print(render_monitor_text(result))

    import os
    os.makedirs("output", exist_ok=True)
    result["model_a"]["weekly"].to_csv("output/copper_acid_cushion_weekly.csv")
    result["model_a"]["stress"].to_csv("output/copper_acid_cushion_stress.csv", index=False)
    result["model_a"]["yield_sensitivity"].to_csv("output/copper_acid_cushion_yield_sensitivity.csv", index=False)
    result["model_c"]["kamoa_quarterly"].to_csv("output/kamoa_kakula_quarterly.csv")
    chart_path = plot_monitor(result)
    print("\n[written: output/copper_acid_cushion_weekly.csv, "
          "output/copper_acid_cushion_stress.csv, "
          "output/copper_acid_cushion_yield_sensitivity.csv, "
          f"output/kamoa_kakula_quarterly.csv, {chart_path}]")