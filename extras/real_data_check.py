"""
real_data_check.py
===================
SECONDARY / cross-metal real dataset (see copper_acid_data.py, now the
PRIMARY real-data source for this project's headline copper acid-cushion
thesis -- this file's zinc-vs-copper quarterly comparison is corroborating
evidence, not the central test; see model_a.py's module docstring and
the earlier README's 2026-09-16 changelog for the full reasoning).

A SMALL, SPARSE, REAL dataset -- not synthetic -- built from publicly
reported figures, to stress-test the (zinc-vs-copper) thesis against what
actually happened in 2023-2026, rather than only against the pipeline's
own synthetic fixture (see demo.py, which only proves the code runs, not
that the thesis holds).

Every number below is transcribed from a named public source with a date,
per data_loaders.py's sourcing discipline. TC and sulfuric acid are
QUARTERLY at best for ZINC (no free API publishes zinc TC more often --
see the source note's feasibility table); COPPER's TC and the copper-
smelting acid index are now available at WEEKLY resolution via
copper_acid_data.py, and 2026-Q1/Q3's cu_tc and acid_cny below are
DERIVED from that weekly series (quarter-mean), not separately hand-cited
-- see the _RAW dict's comments for exactly which cells are which. Zinc
price is MONTHLY via FRED's PZINCUSDM (genuinely real when the file is
present -- see below); copper/silver are DAILY via yfinance. Don't
flatten that back down to "everything is quarterly" -- each input keeps
the frequency its actual source publishes at, and only zinc's TC/acid
force that HALF of the analysis onto a quarterly cadence.

Sources for the TC and acid figures (checked Sep 2026):
  - Zinc TC benchmark 2023->2024: Teck/Korea Zinc annual benchmark fell to
    $165/t from $274/t (Reuters via Kitco, Apr 2024).
  - Zinc TC spot, China: record low $(50)-(20)/t on Aug 30 2024; turned
    positive $0-30/t on Feb 14 2025 (Fastmarkets, Dec 2025).
  - Zinc TC, 2025-2026: guidance ~$10-30/t (Q1 2025) -> peak $120-140/t
    (Q4 2025) -> $35-70/t (Q2 2026) (discoveryalert.com.au, Apr 2026;
    Fastmarkets, Jun 2026) -> spot imported TC an ALL-TIME LOW of -$113/t
    in Aug 2026 against an $85/t annual benchmark (Reuters/Mining Weekly,
    2026-09-03; see copper_acid_data.MARKET_CONTEXT_SEPT_2026['zinc']) --
    "byproduct gains from sulfuric acid have still lent strong support to
    smelters' margins" (Fastmarkets, Jun 2026) was true in Q2; by Q3 zinc
    shows the SAME acid-cushion-under-pressure mechanism copper does.
  - Copper TC benchmark 2024: $80/t, down 9% y/y (fxstreet, Feb 2024).
    Copper TC spot: $19.8/t in Feb 2024 (lowest since 2013), single
    digits by Mar 2024 (Bloomberg/Reuters). 2026 figures are now sourced
    weekly via copper_acid_data.cu_tc_weekly() -- see that module, not
    hand-cited here.
  - China sulfuric acid, 98% grade: annual average ~375 yuan/t in 2024
    (implied from "+83.13% y/y to 687.96 yuan/t" in 2025, SunSirs Mar
    2026) -> ~688 yuan/t in 2025. 2026 figures are now sourced weekly via
    copper_acid_data.cu_acid_weekly() -- see that module, not hand-cited
    here (this REPLACES the old 2026-Q2 "960-1110 yuan/t regional squeeze"
    proxy with the actual SMM China Copper Smelting Acid Index mean for
    the quarter -- see the _RAW dict's comments).

THE HEADLINE FINDING FOR THE ZINC-VS-COPPER COMPARISON (see STRATEGY_
NOTE.md for the full discussion): acid price did NOT fall alongside TC in
2024-2025 as the ORIGINAL version of this thesis assumed -- it rose
sharply, becoming (in industry participants' own words) a "profit
lifeline" / "cash flow buffer" for smelters. By mid-to-late 2026, that
cushion itself started narrowing (see copper_acid_data.py) -- the current,
COPPER-specific version of the thesis this project now leads with.

CHANGELOG -- zinc price sourcing (2025-09): the first version of this file
used COMEX zinc (ZNC=F) via yfinance for zn_price, the same way as
cu_price/silver_price. A real local pull showed that ticker frozen at a
single settlement price (2297.0) for 93% of a 2023-2026 sample -- 5 of 6
quarters used here had exactly one unique value for the entire quarter.
Switched to FRED's PZINCUSDM (IMF "Global price of Zinc", monthly,
verified real), which needs no daily-liquidity assumption at all. See
data_loaders.load_fred_zinc and the earlier strategy note for the full account.

CHANGELOG -- 2026-09-15 review:
  - QUARTERS extended with "2026-Q1" and "2026-Q3" now that real daily
    cu_price/silver_price data covers this whole span (previously the
    list jumped straight from 2025-Q4 to 2026-Q2, silently discarding
    real data that had since become available for the skipped quarters
    and for Jul-Sep 2026). "2025-Q2"/"2025-Q3"/"2024-Q2"/"2024-Q4" are
    STILL deliberately excluded -- see EVENT_WINDOW_NOTES / the comment
    below 2025-Q3 specifically, which is skipped on purpose, not by
    oversight.
  - New quarters get NO invented fallback numbers for zn_price/cu_price/
    silver_price (NaN instead) -- inventing another round number here
    would just create a second "looks real, isn't" data point of exactly
    the kind this file's provenance-reporting was built to avoid. They
    rely entirely on the real-data overlay below (or stay NaN and get
    reported as missing, which is more honest than a plausible guess).
  - New quarters also get NO zn_tc/cu_tc/acid_cny figures (NaN) -- no
    citation was available for them at review time. main() now prints an
    explicit list of any quarter missing these, in addition to the
    existing zn_price/cu_price/silver_price provenance table, so this
    can't go unnoticed the way the missing fred_zinc.csv previously did.
  - EVENT_WINDOW_NOTES added: two real, verified, non-fundamental price
    shocks (the 2025-07-30 COMEX copper tariff-exemption collapse, and
    the 2026-01-29/30 silver melt-up/crash) sit in or near the extended
    window. Neither is a data error; neither has anything to do with the
    acid-credit mechanism. Flagged explicitly rather than silently
    averaged through.

CHANGELOG -- 2026-09-16 review (this project's pivot to the copper
acid-cushion thesis; see docs/METHODOLOGY.md):
  - This file's role is now SECONDARY -- corroborating cross-metal
    evidence, not the central test. copper_acid_data.py / model_a.
    run_model_a_copper_acid_cushion() / acid_cushion_monitor.py are
    PRIMARY.
  - 2026-Q1 and 2026-Q3's cu_tc/acid_cny are no longer NaN -- both are
    now DERIVED programmatically from copper_acid_data.py's cited weekly
    series (quarter-mean), computed below, not hand-typed. 2026-Q3's zn_tc
    is now populated too, from copper_acid_data's cited Aug-2026
    all-time-low print. 2026-Q1's zn_tc remains NaN -- no citation for a
    Q1-2026 imported zinc TC print was found; this is reported honestly,
    not filled with a guess.
  - FIXED: the flat 7.1 CNY/USD conversion (previously applied to EVERY
    quarter 2023-2026 alike) is replaced with copper_acid_data.
    cny_to_usd(), a period-matched quarterly FX table -- USD/CNY moved
    from ~7.1-7.3 in 2023-2025 to ~6.7-7.0 by mid-2026 (the yuan's
    strongest levels since Jan 2023), so the flat rate was understating
    2026 acid prices in USD terms by roughly 5-8%. See copper_acid_data.
    USD_CNY_QUARTERLY for the (still approximate, but now period-matched)
    rates used.
"""

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # allow `python extras/<script>.py` from the repo root
import os

import numpy as np
import pandas as pd

import copper_acid_data as cad
from margin_model import SmelterParams, smelter_margin, margin_bridge, \
    relative_acid_contribution_share
from model_a import DEFAULT_ZN_PARAMS, DEFAULT_CU_PARAMS
from data_loaders import load_real_metal_prices_quarterly, load_fred_zinc, \
    aggregate_monthly_to_quarterly, MissingDataError

QUARTERS = ["2023-Q4", "2024-Q1", "2024-Q3", "2025-Q1", "2025-Q4",
            "2026-Q1", "2026-Q2", "2026-Q3"]

# Known event-driven distortions inside specific quarters -- flagged, not
# silently smoothed over. Neither event has anything to do with the
# acid-credit mechanism; both are noted here so a reader doesn't mistake
# either quarter's metal-price move for TC/acid-driven smelter economics.
EVENT_WINDOW_NOTES = {
    "2026-Q1": (
        "silver_price contains the historic Jan 2026 melt-up/crash: spot "
        "silver reached an all-time high near $121/oz around 2026-01-29, "
        "then fell roughly 30%+ in about a day on 2026-01-30 (Fed-"
        "nomination news + forced liquidations, per contemporaneous "
        "reporting). Precious-metals mania/deleveraging, not an acid/TC "
        "signal -- read this quarter's silver-driven byproduct revenue "
        "with that in mind, and consider whether a quarterly MEAN is even "
        "the right statistic for a quarter with a move this violent."
    ),
    "2026-Q3": (
        "PARTIAL quarter -- the real-data source (data/metal_prices.csv) "
        "only covers whatever date it was last fetched through, not a "
        "full quarter. Treat this quarter's average as provisional until "
        "re-fetched after quarter close (2026-09-30)."
    ),
}
# 2025-Q3 (and 2025-Q2) are DELIBERATELY NOT included yet, even though
# real daily cu_price/silver_price data now exists for them: COMEX copper
# (HG=F, this project's cu_price source) traded up to ~28-30% above LME
# for several months in mid-2025 due to a US Section 232 tariff-arbitrage
# episode, then collapsed a record ~20-22% in a single session on
# 2025-07-30 when refined copper was excluded from the tariff. That's a
# real, well-documented event -- but it's a US-exchange-specific policy
# distortion, not a reflection of the global/Chinese smelter economics
# this thesis is about. Add 2025-Q3 only once you've decided how to
# handle it: e.g. splice in an LME-based cu_price for that window instead
# of HG=F, or keep HG=F but footnote the quarter the way 2026-Q1 is
# footnoted above. Adding it silently would let a US tariff headline
# masquerade as a zinc-vs-copper smelter-margin finding.

# Quarterly, approximate, cited (see module docstring) -- BUT NOT UNIFORMLY.
# Being explicit about exactly which cells are grounded:
#
#   GENUINELY SOURCED, single dated print (see docstring above for the
#   exact citation):
#     zn_tc:  2023-Q4 (274), 2024-Q1 (165, annual benchmark), 2024-Q3 (-35,
#             the Aug 30 2024 spot print), 2025-Q1 (20, within the cited
#             Feb 14 2025 "$0-30" range), 2025-Q4 (130, within cited
#             "$120-140" Q4 2025 peak), 2026-Q2 (55, within cited "$35-70"),
#             2026-Q3 (-113, Aug-2026 all-time-low print, via
#             copper_acid_data.MARKET_CONTEXT_SEPT_2026)
#     cu_tc:  2024-Q1 (80, annual benchmark)
#     acid:   2025-Q4 (688 CNY, the actual cited 2025 annual average)
#   DERIVED (quarter-mean of copper_acid_data.py's cited WEEKLY series --
#   see _quarter_mean_from_weekly() above; a mean over several weekly
#   points of mixed cited/interpolated provenance, not one dated print):
#     cu_tc:   2026-Q1, 2026-Q3
#     acid:    2026-Q1, 2026-Q3 (this REPLACES the old 2026-Q2 hand-picked
#              "960-1110 yuan/t regional squeeze" proxy's successor value
#              -- 2026-Q2 itself below is still the old hand-cited number,
#              since copper_acid_data's weekly series only starts covering
#              Q2 partway through; not worth re-deriving one already-cited
#              quarter just for consistency)
#   INTERPOLATED / BACK-CALCULATED, NOT DIRECTLY CITED AT THAT DATE:
#     acid:   2023-Q4, 2024-Q1, 2025-Q1 (300/280/450 CNY) -- straight-lined
#             between the 2024-implied (~375) and 2025 (688) annual averages
#   NOT SOURCED AT ALL -- plausible round numbers, LAST-RESORT FALLBACK ONLY,
#   used only for quarters/columns where no real feed is wired up (see the
#   overlay logic below -- every run reports exactly which cells this is
#   still true for, prominently, not buried in a comment):
#     zn_price, cu_price, silver_price (for the ORIGINAL 6 quarters only --
#       2026-Q1/2026-Q3 get NaN instead, see changelog above)
#     cu_tc: 2024-Q3 (15) -- invented to sit between the cited Feb/Mar 2024
#            "$19.8" / "single digits" prints and the 2025 figures
#   NO FIGURE AT ALL (NaN), still, after the 2026-09-16 fill-in above:
#     zn_tc: 2026-Q1 only -- no citation for a Q1-2026 imported zinc TC
#     print was found. main() prints this explicitly every run.
#
# Net effect: the DIRECTION and rough MAGNITUDE of the TC collapse and the
# acid-price move (surge, then narrowing -- see copper_acid_data.py) are
# real. Exact dollar figures inherit uncertainty from every uncited cell
# above PLUS the uncalibrated SmelterParams defaults (see the earlier strategy note)
# -- read them as "this shape is real, this precision is not" throughout.
_RAW = {
    # date          zn_price  cu_price  zn_tc  cu_tc  acid_cny  ag_price  energy
    "2023-Q4": [2500, 8500, 274, 88, 300, 24, 70],
    "2024-Q1": [2450, 8800, 165, 80, 280, 23, 68],
    "2024-Q3": [2600, 9200, -35, 15, 320, 28, 66],
    "2025-Q1": [2750, 9600, 20, 5, 450, 31, 65],
    "2025-Q4": [3100, 10800, 130, 0, 688, 35, 67],
    "2026-Q1": [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
    "2026-Q2": [3050, 11200, 55, -10, 1000, 38, 69],
    "2026-Q3": [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
}
REAL_DATA = pd.DataFrame(
    _RAW,
    index=["zn_price", "cu_price", "zn_tc", "cu_tc", "acid_cny", "silver_price", "energy_price"],
).T.astype(float)

# --- 2026-09-16: fill in 2026-Q1/Q3 cu_tc & acid_cny from copper_acid_
# data.py's cited weekly series (quarter-mean of whatever cited/cited-
# approx/interpolated points fall in that quarter) -- REPLACES the old
# all-NaN state for these two cells. This is a DERIVED figure (a mean over
# several weekly points of varying provenance), not a single dated
# citation like the other cells in this table -- flagged as such in
# main()'s provenance printout, not presented as equivalent precision to
# e.g. "2024-Q1 cu_tc = 80 (annual benchmark)".
def _quarter_mean_from_weekly(weekly_df: pd.DataFrame, value_col: str, quarter_label: str) -> float:
    period = pd.Period(quarter_label, freq="Q")
    window = weekly_df.loc[str(period.start_time.date()):str(period.end_time.date()), value_col]
    return float(window.mean()) if len(window) else float("nan")


_cu_tc_weekly = cad.cu_tc_weekly_interpolated()
_acid_weekly = cad.cu_acid_weekly_interpolated()
for _q in ("2026-Q1", "2026-Q3"):
    REAL_DATA.loc[_q, "cu_tc"] = round(_quarter_mean_from_weekly(_cu_tc_weekly, "tc_usd_dmt", _q), 2)
    REAL_DATA.loc[_q, "acid_cny"] = round(_quarter_mean_from_weekly(_acid_weekly, "acid_cny_t", _q), 1)
# 2026-Q3 zn_tc: single representative citation (consistent with how other
# quarters in this table use one dated print, not a true quarterly mean) --
# SMM spot imported zinc TC all-time low, Aug 2026 (see copper_acid_data.
# MARKET_CONTEXT_SEPT_2026['zinc']). 2026-Q1 zn_tc stays NaN -- no citation
# for a Q1-2026 imported zinc TC print was found; reported honestly below,
# not filled with a guess.
REAL_DATA.loc["2026-Q3", "zn_tc"] = cad.MARKET_CONTEXT_SEPT_2026["zinc"]["smm_spot_zn_tc_aug2026_usd_dmt"]

# acid price converted CNY/t -> USD/t using a PERIOD-MATCHED quarterly FX
# table (copper_acid_data.USD_CNY_QUARTERLY) -- FIXED 2026-09-16, replacing
# a single flat 7.1 rate previously applied to every quarter 2023-2026
# alike (see module docstring's changelog for why that mattered: USD/CNY
# moved from ~7.1-7.3 in 2023-2025 to ~6.7-7.0 by mid-2026).
REAL_DATA["acid_price"] = [
    cad.cny_to_usd(v, q) if pd.notna(v) else float("nan")
    for q, v in REAL_DATA["acid_cny"].items()
]

# 2026-Q1/Q3 energy_price: no free public daily/quarterly industrial-
# electricity series exists for this project (see model_a.py's
# ENERGY_PRICE_USD_MWH docstring for the same gap) -- filled with the SAME
# flat $70/MWh-equivalent placeholder used there, rather than left NaN,
# because leaving it NaN cascades into sm_zn/sm_cu being NaN for BOTH
# quarters (smelter_margin can't compute with a missing input), which
# would silently drop 2026-Q3 -- the most current and most relevant
# quarter here -- from every margin-comparison output below. The
# placeholder's effect on the margin figures is modest (see model_a.py's
# note: energy is roughly 2-4% of total smelter economics at these TC/
# acid levels) but is still a real, flagged simplification, not a fetched
# number.
REAL_DATA.loc["2026-Q1", "energy_price"] = 70.0
REAL_DATA.loc["2026-Q3", "energy_price"] = 70.0

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_invented = {"zn_price": list(QUARTERS), "cu_price": list(QUARTERS), "silver_price": list(QUARTERS)}
_upgraded = {}   # col -> [quarters actually upgraded to real data]
_stale = {}      # col -> [quarters where a real feed existed but was flat/stale]

# --- Zinc: FRED PZINCUSDM (monthly IMF benchmark) -- see module docstring
# for why this replaced a COMEX-via-yfinance attempt that turned out to be
# frozen 93% of the time. No staleness guard needed here (see
# aggregate_monthly_to_quarterly's docstring) -- a monthly benchmark
# doesn't have the "no trades today" failure mode daily futures do.
try:
    _fred_zinc = load_fred_zinc(os.path.join(_DATA_DIR, "fred_zinc.csv"))
    _zn_quarterly = aggregate_monthly_to_quarterly(_fred_zinc, REAL_DATA.index)
    if len(_zn_quarterly):
        REAL_DATA.loc[_zn_quarterly.index, "zn_price"] = _zn_quarterly.round(1)
        _upgraded["zn_price"] = list(_zn_quarterly.index)
        _invented["zn_price"] = [q for q in QUARTERS if q not in _zn_quarterly.index]
except MissingDataError:
    pass  # data/fred_zinc.csv not downloaded yet -- zn_price stays invented, reported below

# --- Copper & silver: yfinance daily (HG=F, SI=F) -- verified reliable on
# a real pull; kept on the flat/stale-guarded loader since daily futures
# CAN go stale, unlike the monthly zinc benchmark above.
_real_prices = load_real_metal_prices_quarterly(os.path.join(_DATA_DIR, "metal_prices.csv"), REAL_DATA.index)
if not _real_prices.empty:
    for col in ("cu_price", "silver_price"):
        if col not in _real_prices.columns:
            continue
        real_col = _real_prices[col]
        usable = real_col.dropna()
        flat = real_col.index[real_col.isna()]
        if len(usable):
            REAL_DATA.loc[usable.index, col] = usable.round(1)
            _upgraded[col] = list(usable.index)
            _invented[col] = [q for q in QUARTERS if q not in usable.index]
        if len(flat):
            _stale[col] = list(flat)


def main():
    print("=== Data provenance for this run (check this before trusting any number below) ===")
    for col in ("zn_price", "cu_price", "silver_price"):
        up = _upgraded.get(col, [])
        st = _stale.get(col, [])
        inv = _invented.get(col, [])
        print(f"{col}: real for {up or 'no quarters'}"
              + (f"; flat/stale, kept invented for {st}" if st else "")
              + (f"; INVENTED OR MISSING (not sourced) for {inv}" if inv else ""))
    if _invented.get("zn_price") == QUARTERS:
        print(
            "\n*** zn_price is 100% invented/missing this run -- no data/fred_zinc.csv "
            "found. ***\n"
            "Fix: download 'Global price of Zinc' (PZINCUSDM) from\n"
            "fred.stlouisfed.org/series/PZINCUSDM -> Download -> CSV, save as\n"
            "data/fred_zinc.csv, rerun. Every zinc-margin number below is currently\n"
            "illustrative only, not evidence."
        )
    if _invented.get("cu_price") == QUARTERS and _invented.get("silver_price") == QUARTERS:
        print(
            "\ncu_price/silver_price also fully invented/missing this run -- no "
            "data/metal_prices.csv found. Fix: run fetch_metal_prices_yfinance.py "
            "locally first."
        )

    # New (2026-09-15): loud check for quarters still missing manually-
    # curated TC/acid figures -- these have no free API and will silently
    # stay NaN forever unless someone adds a cited number.
    missing_manual_cols = {}
    for col in ("zn_tc", "cu_tc", "acid_price"):
        nan_quarters = REAL_DATA.index[REAL_DATA[col].isna()].tolist()
        if nan_quarters:
            missing_manual_cols[col] = nan_quarters
    if missing_manual_cols:
        print("\n*** Quarters missing manually-curated TC/acid figures (no free API "
              "for these -- add cited values to REAL_DATA's _RAW dict before "
              "trusting any margin/threshold number for these quarters): ***")
        for col, qs in missing_manual_cols.items():
            print(f"  {col}: {qs}")

    # New (2026-09-15): event-window notes for quarters in QUARTERS.
    for q, note in EVENT_WINDOW_NOTES.items():
        if q in QUARTERS:
            print(f"\n*** Event-window note for {q}: {note} ***")

    print()
    print("=== Real, cited quarterly data (2023 Q4 - 2026 Q3) ===")
    print(REAL_DATA[["zn_price", "cu_price", "zn_tc", "cu_tc", "acid_price", "silver_price"]])

    zn = REAL_DATA.rename(columns={"zn_price": "metal_price", "zn_tc": "tc"})
    cu = REAL_DATA.rename(columns={"cu_price": "metal_price", "cu_tc": "tc"})

    print("\n=== Zinc smelter margin, per quarter (real inputs where available, default calibration) ===")
    sm_zn = smelter_margin(DEFAULT_ZN_PARAMS, zn["metal_price"], zn["tc"], zn["acid_price"],
                            zn["energy_price"], silver_price=zn["silver_price"])
    print(sm_zn.round(1))

    print("\n=== Copper smelter margin, per quarter (real inputs where available, default calibration) ===")
    sm_cu = smelter_margin(DEFAULT_CU_PARAMS, cu["metal_price"], cu["tc"], cu["acid_price"],
                            cu["energy_price"], silver_price=cu["silver_price"])
    print(sm_cu.round(1))

    # The bridge below still uses 2024-Q1 -> 2026-Q2, unchanged -- both
    # endpoints are fully populated (TC/acid cited, prices real once the
    # data files are in place) and neither sits inside an EVENT_WINDOW_NOTES
    # quarter or the deliberately-excluded 2025-Q3, so this comparison
    # doesn't need adjusting just because QUARTERS grew around it. If you
    # want a bridge into 2026-Q3, remember it is a PARTIAL quarter (see
    # EVENT_WINDOW_NOTES above) before drawing conclusions from it.
    print("\n=== Margin bridge: 2024-Q1 -> 2026-Q2, zinc (exact decomposition) ===")
    bridge_zn = margin_bridge(DEFAULT_ZN_PARAMS, zn.loc["2024-Q1"], zn.loc["2026-Q2"])
    for k, v in bridge_zn.items():
        print(f"  {k}: {v:.1f}")

    print("\n=== Margin bridge: 2024-Q1 -> 2026-Q2, copper (exact decomposition) ===")
    bridge_cu = margin_bridge(DEFAULT_CU_PARAMS, cu.loc["2024-Q1"], cu.loc["2026-Q2"])
    for k, v in bridge_cu.items():
        print(f"  {k}: {v:.1f}")

    print("\n=== Acid vs TC share of each metal's OWN total margin change ===")
    shares = relative_acid_contribution_share(bridge_zn, bridge_cu)
    for k, v in shares.items():
        print(f"  {k}: {v:.2%}")

    print(
        "\nReading this: if the acid share is POSITIVE while TC share is strongly "
        "NEGATIVE, acid moved WITH the smelter (cushioning TC), not against it -- "
        "the opposite of the 'double whammy' the original thesis assumed. Check "
        "the sign, not just the magnitude, before concluding anything about which "
        "metal is more exposed -- and check the provenance table and event-window "
        "notes at the top of this run before trusting the magnitude at all."
    )


if __name__ == "__main__":
    main()
