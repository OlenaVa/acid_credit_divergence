"""
strategy_charts.py
==================
Charts for the portfolio note. All built from real, cited data via
strategy_layer.py / model_a.py -- nothing synthetic. Every chart carries its
own source/provenance line, because a PNG travels without its README.

  output/01_transmission_map.png      physical -> financial chain, China vs ex-China
  output/02_cushion_attribution.png   actual vs flat-acid vs flat-TC + who drives the fall
  output/03_regime_map.png            cushion ratio over (acid price x TC), 2026 path overlaid
  output/04_regional_divergence.png   China vs ex-China acid; Kamoa coverage Q1/Q2/Q3-indicated
  output/copper_acid_cushion.png      the monitor chart (markers now per-series -- see note below)

NOTE on copper_acid_cushion.png: before 2026-10-01 the acid and ratio markers were
drawn at the TC series' cited dates (one mask used for all panels), so interpolated
acid weeks were shown as if they were prints. Each series now uses its own status.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

import strategy_layer as sl

SRC = "Sources: SMM weekly TC & China copper-smelting acid indices (cited prints), Ivanhoe Mines Q2-2026 release, yfinance (Cu, Ag). Model: representative custom smelter, uncalibrated cost inputs."
GREEN, AMBER, BLUE, GREY, RED = "#2e8b57", "#d99a1e", "#3b6fb6", "#9aa0a6", "#c0392b"


def _observed(status: pd.Series) -> pd.Series:
    return status.isin(["cited", "cited-approx"])


def _foot(fig, text=SRC):
    fig.text(0.01, 0.005, text, fontsize=6.5, color="#555555", ha="left", va="bottom", wrap=True)


# ---------------------------------------------------------------------------
# 0. the monitor chart (fixed)
# ---------------------------------------------------------------------------
def plot_monitor(weekly: pd.DataFrame, out_path="output/copper_acid_cushion.png") -> str:
    latest = weekly.index[-1].date()
    obs_tc, obs_ac = _observed(weekly["tc_status"]), _observed(weekly["acid_status"])
    obs_ratio = obs_tc & obs_ac

    fig, axes = plt.subplots(3, 1, figsize=(10, 9.2), sharex=True)
    fig.suptitle(f"Copper acid cushion -- SMM weekly data through {latest}", fontsize=11, fontweight="bold")

    ax = axes[0]
    ax.plot(weekly.index, weekly["tc_usd_dmt"], color=BLUE, lw=1.1)
    ax.scatter(weekly.index[obs_tc], weekly["tc_usd_dmt"][obs_tc], color=BLUE, s=16, zorder=3)
    ax.axhline(0, color="grey", lw=0.7)
    ax.set_ylabel("TC, USD/dmt")
    ax.set_title("Treatment charge (SMM Imported Copper Concentrate Index)", fontsize=9.5)

    ax = axes[1]
    ax.plot(weekly.index, weekly["acid_usd_t"], color=RED, lw=1.1)
    ax.scatter(weekly.index[obs_ac], weekly["acid_usd_t"][obs_ac], color=RED, s=16, marker="s", zorder=3)
    ax.axvline(pd.Timestamp("2026-07-03"), color="grey", lw=0.8, ls=":")
    ax.text(pd.Timestamp("2026-07-05"), ax.get_ylim()[0] + 4, "acid peak\n3 Jul", fontsize=7, color="grey")
    ax.set_ylabel("Acid, USD/t (ex-VAT, model basis)")
    ax.set_title("China copper-smelting sulphuric acid index, VAT stripped then converted at quarterly-average FX", fontsize=9.5)

    ax = axes[2]
    r = weekly["acid_cushion_ratio"] * 100
    ax.axhspan(0, 50, color=RED, alpha=0.07)
    ax.axhspan(50, 100, color=AMBER, alpha=0.08)
    ax.axhspan(100, 270, color=GREEN, alpha=0.06)
    ax.plot(weekly.index, r, color="#444444", lw=1.1)
    ax.scatter(weekly.index[obs_ratio], r[obs_ratio], color="#444444", s=16, zorder=3)
    ax.axhline(100, color="grey", lw=0.8, ls="--")
    ax.axhline(50, color="grey", lw=0.8, ls="--")
    ax.set_ylim(0, 270)
    ax.text(weekly.index[1], 104, "ABSORBING (>=100%)", fontsize=7, color=GREEN)
    ax.text(weekly.index[1], 54, "ERODING (50-100%)", fontsize=7, color="#9a6b00")
    ax.text(weekly.index[1], 6, "EXHAUSTED (<50%)", fontsize=7, color=RED)
    ax.set_ylabel("Acid credit / |TC|, %")
    ax.set_title("Acid cushion ratio (markers: weeks where BOTH TC and acid are cited prints)", fontsize=9.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

    fig.text(0.01, 0.005, "Markers = cited SMM prints; the thin line includes linearly interpolated weeks. "
                          "Regime bands are judgment levels (not calibrated).", fontsize=6.5, color="#555555")
    plt.tight_layout(rect=(0, 0.015, 1, 0.97))
    plt.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# 1. transmission map
# ---------------------------------------------------------------------------
def plot_transmission_map(s: dict, out_path="output/01_transmission_map.png") -> str:
    k, a = s["kamoa"], s["attribution"]["since July acid peak"]
    fig, ax = plt.subplots(figsize=(12.5, 7.4))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 62)
    ax.axis("off")
    fig.suptitle("Physical -> financial transmission: one shock, two acid markets", fontsize=13, fontweight="bold", x=0.02, ha="left")
    ax.text(0, 61.5, "The acid credit is being REDISTRIBUTED by geography and policy, not simply falling everywhere.",
            fontsize=9.5, color="#333333", va="bottom")

    def box(x, y, w, h, text, color):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.8",
                                    fc="white", ec=color, lw=2.0))
        ax.text(x + w / 2, y + h / 2, text.replace("$", r"\$"), ha="center", va="center", fontsize=7.6)

    def arrow(x1, y1, x2, y2, color="#555555", style="-|>"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=12, color=color, lw=1.4))

    W, H = 17.5, 9.5
    xs = [1, 21, 41, 61, 81]
    # top: ex-China
    ty = 43
    ax.text(0, ty + H + 2.3, "EX-CHINA (DRC / Zambia): sulphur shortage -> higher acid -> wider smelter credit", fontsize=9, fontweight="bold", color=GREEN)
    top = [
        ("Hormuz disruption\n(28 Feb 2026)", GREEN),
        ("Global sulphur exports\n~ -45% from Feb (Kpler);\nSMM sulphur ~RMB 9.1k/t (Jul)", GREEN),
        (f"Ex-China acid price up\nEXW DRC ~${s['regional']['exw_drc_usd_t']:.0f}/t\nKamoa contract ~$840 (Q2: $465)", GREEN),
        (f"Integrated smelter credit up\nKamoa Q3 ~ ${k['q3_credit_mgmt_usd_lb']:.2f}/lb\n(mgmt) vs $0.39 in Q2", AMBER),
        (f"Coverage widens\n{k['q3_coverage_mgmt_at_q2_opex']*100:.0f}-{k['q3_coverage_implied_yield_at_q2_opex']*100:.0f}% of opex\n(Q2: {k['coverage_q2']*100:.0f}%)  -- pending Q3", AMBER),
    ]
    for x, (t, c) in zip(xs, top):
        box(x, ty, W, H, t, c)
    for i in range(4):
        arrow(xs[i] + W + 0.3, ty + H / 2, xs[i + 1] - 0.3, ty + H / 2)

    # middle: TC
    my = 26
    tc_now = s["snapshot"]["tc_usd_dmt"]
    box(45, my, 40, 8, f"Concentrate scarcity -> TC record low: -${abs(tc_now):.0f}/dmt\n(hits CUSTOM smelters; SMM, cited)", GREEN)
    ax.text(0, my + 4, "COMMON TC LEG", fontsize=8.5, fontweight="bold", color=GREEN)
    ax.text(0, my - 0.2, "Integrated smelters (Kamoa) have no TC line:\ninsulated from this leg; it bites custom smelters.",
            fontsize=7.4, color="#444444", va="top")
    arrow(72, my - 0.3, 72, 19.4, color=BLUE)

    # bottom: China
    by = 9
    ax.text(0, by + H + 2.3, "CHINA DOMESTIC: export halt traps acid at home -> lower acid credit against the same TC", fontsize=9, fontweight="bold", color=RED)
    bot = [
        ("China acid export halt\n(May -> end-2026,\nper CRU reporting)", GREEN),
        ("Exports ~117kt (May)\n-> ~1kt (Jun); domestic\nsurplus + fertiliser off-season", GREEN),
        (f"China acid index\nRMB {s['snapshot']['acid_peak_cny_t']:,.0f} ({s['snapshot']['acid_peak_date']:%d %b}) ->\n{s['snapshot']['acid_cny_t']:,.1f} (latest), {s['snapshot']['acid_change_from_peak_pct']*100:.0f}%", GREEN),
        (f"Custom-smelter cushion\n{a['ratio_start']*100:.0f}% -> {a['ratio_end']*100:.0f}%\n(acid {a['acid_share']*100:.0f}% / TC {a['tc_share']*100:.0f}% of the fall)", BLUE),
        ("Physical response?\nEMERGING, not confirmed\n(CSPT set no Q4 TC guidance)", AMBER),
    ]
    for x, (t, c) in zip(xs, bot):
        box(x, by, W, H, t, c)
    for i in range(4):
        arrow(xs[i] + W + 0.3, by + H / 2, xs[i + 1] - 0.3, by + H / 2)

    box(5, 0.3, 90, 4.5, "MARKET EXPRESSION (to monitor, not a trade): China cathode output, Yangshan premium, TC path, CSPT actions, "
                         "integrated vs custom smelter equities. No liquid exchange-traded acid hedge identified -- untested.", GREY)

    # legend
    lx = 1
    for c, lbl in [(GREEN, "observed (cited)"), (AMBER, "management indication / unconfirmed"), (BLUE, "model-derived"), (GREY, "untested")]:
        ax.add_patch(FancyBboxPatch((lx, 57.3), 1.6, 1.6, boxstyle="round,pad=0.1", fc="white", ec=c, lw=2))
        ax.text(lx + 2.3, 58.1, lbl, fontsize=7.5, va="center")
        lx += 24
    _foot(fig, "Sources: Kpler (sulphur exports), SMM (TC, acid, sulphur), CRU (acid export halt), Ivanhoe Mines Q2-2026 release & earnings call. "
               "Arrows show proposed causal direction; only 'observed' boxes are data.")
    plt.tight_layout(rect=(0, 0.02, 1, 0.94))
    plt.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# 2. attribution + counterfactual
# ---------------------------------------------------------------------------
def plot_attribution(s: dict, out_path="output/02_cushion_attribution.png") -> str:
    cf = s["counterfactual"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.4), gridspec_kw={"width_ratios": [1.45, 1]})
    fig.suptitle("How much of the cushion's fall is acid? -- actual vs counterfactual, and attribution by window",
                 fontsize=11.5, fontweight="bold", x=0.01, ha="left")

    ax1.fill_between(cf.index, cf["actual"] * 100, cf["cf_flat_acid"] * 100, color=RED, alpha=0.12,
                     label="gap attributable to the acid decline")
    ax1.plot(cf.index, cf["cf_flat_acid"] * 100, color=GREEN, lw=1.8, ls="--", label="if acid had stayed at its 3-Jul level (TC as observed)")
    ax1.plot(cf.index, cf["cf_flat_tc"] * 100, color=BLUE, lw=1.4, ls=":", label="if TC had stayed at its 3-Jul level (acid as observed)")
    ax1.plot(cf.index, cf["actual"] * 100, color="#222222", lw=2.4, label="actual")
    ax1.axhline(100, color="grey", lw=0.8, ls="--")
    ax1.axhline(50, color="grey", lw=0.8, ls="--")
    e = cf.iloc[-1]
    ax1.annotate(f"{e['actual']*100:.0f}%", (cf.index[-1], e["actual"] * 100), xytext=(6, -2), textcoords="offset points", fontsize=8.5, fontweight="bold")
    ax1.annotate(f"{e['cf_flat_acid']*100:.0f}%", (cf.index[-1], e["cf_flat_acid"] * 100), xytext=(6, -2), textcoords="offset points", fontsize=8.5, color=GREEN)
    ax1.annotate(f"{e['cf_flat_tc']*100:.0f}%", (cf.index[-1], e["cf_flat_tc"] * 100), xytext=(6, -2), textcoords="offset points", fontsize=8.5, color=BLUE)
    ax1.set_ylabel("Acid credit / |TC|, %")
    ax1.set_title(f"Cushion ratio from the 3-Jul acid peak  |  acid decline alone = ${e['margin_cf_flat_acid']-e['margin_actual']:.0f}/t margin (level uncalibrated)", fontsize=9)
    ax1.set_ylim(40, 180)
    ax1.set_xlim(cf.index[0], cf.index[-1] + pd.Timedelta(days=9))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax1.legend(fontsize=7.3, loc="lower left")

    labels, acid_sh, tc_sh = [], [], []
    for name, a in s["attribution"].items():
        labels.append(f"{name}\n{a['start']} -> {a['end']}")
        acid_sh.append(a["acid_share"] * 100)
        tc_sh.append(a["tc_share"] * 100)
    y = np.arange(len(labels))[::-1]
    ax2.barh(y, tc_sh, color=BLUE, label="TC leg (more negative TC)")
    ax2.barh(y, acid_sh, left=tc_sh, color=RED, label="acid leg (lower acid price)")
    for yi, t, ac in zip(y, tc_sh, acid_sh):
        ax2.text(t / 2, yi, f"{t:.0f}%", ha="center", va="center", color="white", fontsize=8.5, fontweight="bold")
        ax2.text(t + ac / 2, yi, f"{ac:.0f}%", ha="center", va="center", color="white", fontsize=8.5, fontweight="bold")
    ax2.set_yticks(y)
    ax2.set_yticklabels(labels, fontsize=7.6)
    ax2.set_xlim(0, 100)
    ax2.set_xlabel("share of the fall in ln(cushion ratio), %")
    ax2.set_title("Who drove the fall? (exact log decomposition)", fontsize=9.5)
    ax2.legend(fontsize=7.3, loc="lower center", bbox_to_anchor=(0.5, -0.27), ncol=2)
    _foot(fig, SRC + " FX: quarterly averages (steps at quarter boundaries).")
    plt.tight_layout(rect=(0, 0.03, 1, 0.94))
    plt.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# 3. regime map
# ---------------------------------------------------------------------------
def plot_regime_map(s: dict, weekly: pd.DataFrame, params, out_path="output/03_regime_map.png") -> str:
    fx = s["fx"]
    acid = np.linspace(880, 2120, 249)
    tc = np.linspace(-260, -35, 226)
    A, T = np.meshgrid(acid, tc)
    vat = sl.cad.ACID_QUOTE_BASIS["vat_rate_cn"]
    R = params.acid_yield * (A / (1.0 + vat) / fx) / np.abs(T)
    cmap = ListedColormap(["#e6b0aa", "#f5dfa8", "#cfe8d5", "#9fd3b0"])
    norm = BoundaryNorm([0, 0.5, 1.0, 2.0, 10.0], cmap.N)

    fig, ax = plt.subplots(figsize=(10.5, 7.2))
    ax.pcolormesh(A, T, R, cmap=cmap, norm=norm, shading="auto")
    cs1 = ax.contour(A, T, R, levels=[0.5, 1.0], colors=["#7b241c", "#1e6b3a"], linewidths=1.6)
    ax.clabel(cs1, fmt={0.5: "50%", 1.0: "100%"}, fontsize=8)
    # alternative definition: TC + RC (RC = 10% of TC convention) -> drag is (1 + k) x |TC|
    k = abs(sl.rc_usd_per_dmt(-1.0, params))
    ax.contour(A, T, R / (1 + k), levels=[1.0], colors=["#1e6b3a"], linestyles="--", linewidths=1.2)
    ax.text(2100, -252, "dashed = 100% line if the\nrefining charge is counted\n(RC = 10% of TC convention)", fontsize=7.2,
            color="#1e6b3a", ha="right", va="bottom")

    ok = weekly["tc_status"].isin(["cited", "cited-approx"]) & weekly["acid_status"].isin(["cited", "cited-approx"])
    ax.plot(weekly["acid_cny_t"], weekly["tc_usd_dmt"], color="#222222", lw=1.3, alpha=0.85)
    ax.scatter(weekly["acid_cny_t"][ok], weekly["tc_usd_dmt"][ok], color="#222222", s=18, zorder=4)
    for d, lbl, dx, dy in [("2026-01-02", "2 Jan", 6, 6), ("2026-04-24", "24 Apr", 6, 4), ("2026-07-03", "3 Jul\n(acid peak)", 6, 4),
                           ("2026-08-28", "28 Aug", 8, 2)]:
        r = weekly.loc[pd.Timestamp(d)]
        ax.annotate(lbl, (r["acid_cny_t"], r["tc_usd_dmt"]), xytext=(dx, dy), textcoords="offset points", fontsize=8, fontweight="bold")
    last = weekly.iloc[-1]
    ax.scatter([last["acid_cny_t"]], [last["tc_usd_dmt"]], s=110, facecolor="none", edgecolor=RED, lw=2.2, zorder=5)
    ax.annotate(f"24 Sep: cushion {last['acid_cushion_ratio']*100:.0f}%", (last["acid_cny_t"], last["tc_usd_dmt"]),
                xytext=(16, -22), textcoords="offset points", fontsize=8.5, fontweight="bold", color=RED, ha="left")
    ax.set_xlim(880, 2120)
    ax.set_ylim(-260, -35)
    ax.set_xlabel("China copper-smelting acid index, RMB/t as quoted by SMM, incl. VAT  (higher = better for smelters)")
    ax.set_ylabel("TC, USD/dmt  (lower = worse for smelters)")
    ax.set_title("Regime map: acid credit / |TC| across the (acid price, TC) plane -- with the 2026 path", fontsize=11, fontweight="bold", loc="left")
    handles = [plt.Rectangle((0, 0), 1, 1, fc=c) for c in ["#9fd3b0", "#cfe8d5", "#f5dfa8", "#e6b0aa"]]
    ax.legend(handles, ["ABSORBING, >200%", "ABSORBING, 100-200%", "ERODING, 50-100%", "EXHAUSTED, <50%"], fontsize=7.6, loc="upper right", title="cushion regime", title_fontsize=8, framealpha=0.95)
    _foot(fig, "Path: SMM weekly prints (dots = both series cited; line includes interpolated weeks). Cost-free metric: depends only on acid yield "
               f"({params.acid_yield}), FX ({fx}) and the VAT basis (13% deducted). Regime cut-offs are judgment levels.")
    plt.tight_layout(rect=(0, 0.03, 1, 1))
    plt.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# 4. regional divergence
# ---------------------------------------------------------------------------
def plot_regional(s: dict, out_path="output/04_regional_divergence.png") -> str:
    r, k = s["regional"], s["kamoa"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.3), gridspec_kw={"width_ratios": [1.25, 1]})
    fig.suptitle("Same sulphuric acid, two markets: China-domestic vs ex-China", fontsize=11.5, fontweight="bold", x=0.01, ha="left")

    names = ["China\nas quoted\n(incl. VAT)", "China\nex-VAT\n(model basis)", "EXW Zambia", "EXW DRC", "Kamoa Q2\nrealised", "Kamoa Jul/Aug\ncontract"]
    vals = [r["china_domestic_usd_t_as_quoted"], r["china_domestic_usd_t_ex_vat"], r["exw_zambia_usd_t"], r["exw_drc_usd_t"],
            r["kamoa_q2_realized_usd_t"], r["kamoa_jul_aug_contract_usd_t"]]
    cols = [RED, RED, GREEN, GREEN, AMBER, AMBER]
    bars = ax1.bar(range(len(vals)), vals, color=cols, alpha=0.85)
    bars[0].set_hatch("//")
    for i, v in enumerate(vals):
        ax1.text(i, v + 15, f"${v:,.0f}", ha="center", fontsize=8.5, fontweight="bold")
    ax1.set_xticks(range(len(vals)))
    ax1.set_xticklabels(names, fontsize=7.6)
    ax1.set_ylabel("USD / tonne")
    ax1.set_title(f"Acid prices, benchmark date {r['as_of']} (DRC = {r['drc_over_china_ex_vat']:.1f}x China ex-VAT)", fontsize=9.5)
    ax1.set_ylim(0, 1100)
    ax1.text(0.98, 0.97, "Export halt blocks the arbitrage;\nDRC/Zambia are inland leach markets.\nBenchmark flat 5+ weeks: stable OR thin.",
             transform=ax1.transAxes, fontsize=7.2, ha="right", va="top", color="#444444")

    qs = ["Q1 2026\n(reported)", "Q2 2026\n(reported)", "Q3 2026\n(mgmt indication)"]
    cov = [k["coverage_q1"] * 100, k["coverage_q2"] * 100, k["q3_coverage_mgmt_at_q2_opex"] * 100]
    ax2.bar([0, 1], cov[:2], color=AMBER, alpha=0.9)
    ax2.bar([2], [cov[2]], color="white", edgecolor=AMBER, hatch="//", lw=1.5)
    hi = k["q3_coverage_implied_yield_at_q2_opex"] * 100
    ax2.plot([2, 2], [cov[2], hi], color=AMBER, lw=3)
    for x, v in zip([0, 1, 2], cov):
        ax2.text(x, v + 4, f"{v:.0f}%", ha="center", fontsize=9, fontweight="bold")
    ax2.text(2.0, hi + 4, f"{hi:.0f}% (implied-yield cross-check)", ha="center", fontsize=7.2)
    ax2.axhline(100, color="grey", lw=0.8, ls="--")
    ax2.set_xticks([0, 1, 2])
    ax2.set_xticklabels(qs, fontsize=8)
    ax2.set_ylim(0, 235)
    ax2.set_ylabel("Kamoa acid credit / smelter opex, %")
    ax2.set_title("Kamoa-Kakula coverage: Q2 dip is not a price effect; Q3 widens", fontsize=9.5)
    ax2.text(0.02, 0.96, f"Q1->Q2: realised acid price {k['acid_price_change_pct']*100:+.1f}%, credit/lb {k['credit_change_pct']*100:+.0f}%,\n"
                         f"opex/lb {k['opex_change_pct']*100:+.0f}% (Q1 opex partly capitalised, per Ivanhoe). Q3 held at Q2 opex\n"
                         "(assumption). Different denominator from the China |TC| ratio -- not comparable.",
             transform=ax2.transAxes, fontsize=7.2, va="top", color="#444444")
    _foot(fig, "Sources: SMM (China acid index; EXW DRC/Zambia launched 2026-06-05), Ivanhoe Mines Q1/Q2-2026 releases (2026-05-06, 2026-07-29) and earnings call (2026-07-30, "
               "secondary). China ex-VAT = SMM RMB index / 1.13.")
    plt.tight_layout(rect=(0, 0.03, 1, 0.94))
    plt.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


def make_all(result: dict, out_dir="output") -> list[str]:
    import os
    os.makedirs(out_dir, exist_ok=True)
    s = result["strategy"]
    weekly = result["model_a"]["weekly"]
    params = result["model_a"]["params"]
    return [
        plot_monitor(weekly, f"{out_dir}/copper_acid_cushion.png"),
        plot_transmission_map(s, f"{out_dir}/01_transmission_map.png"),
        plot_attribution(s, f"{out_dir}/02_cushion_attribution.png"),
        plot_regime_map(s, weekly, params, f"{out_dir}/03_regime_map.png"),
        plot_regional(s, f"{out_dir}/04_regional_divergence.png"),
    ]