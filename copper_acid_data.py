"""
copper_acid_data.py
====================
CANONICAL REAL DATA for the copper acid-cushion thesis -- "Copper's Hidden
Margin: When the Acid Cushion Starts Shrinking" (source article, Olena
Vasiuta, Sep 7 2026, reporting SMM data through 2026-09-04).

This module is now the PRIMARY real-data source for this project. Before
2026-09-16, `real_data_check.py`'s quarterly zinc-vs-copper table was the
only real dataset here; the article and the review that produced this
module both concluded the sharper, better-evidenced version of the thesis
is COPPER-specific (TC vs acid-credit, both on the same smelter's income
statement), with zinc as a SECONDARY cross-metal confirmation, not the
main test. See README.md / STRATEGY_NOTE.md for the full reasoning.

Every series below is WEEKLY where the underlying SMM index actually
publishes weekly (TC and the China acid index both do); every point is
tagged 'cited' (a number that appears, with that date, in a named public
source), 'cited-approx' (the source gives a value tied to a date range or
a qualitative anchor -- e.g. "start of year", "briefly touched X in early
July" -- rather than a single dated print) or 'interpolated' (no citation
exists for that exact week; linearly interpolated between the two nearest
cited points, so trend/stress calculations have a full weekly grid to run
on). NOTHING here is invented outright -- where a real citation could not
be found for a given week, it is interpolated and marked as such, never
silently filled with a round number. This mirrors the provenance
discipline `real_data_check.py` already applies to the zinc/copper
quarterly table -- extended here to a weekly cadence and a single-metal
focus, because that is the actual cadence and focus of the thesis being
tested.

Sources checked 2026-09-16; TC and acid weekly series, physical-response
evidence, and the fertiliser/acid-export-policy note extended 2026-09-25
with three additional real, cited weekly prints (2026-09-11, 09-18, 09-24)
plus two new physical-response citations -- see README.md's changelog for
the full list of what changed in that pass. Full citation list at the
bottom of each constant's definition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import pandas as pd


# ---------------------------------------------------------------------------
# 1. SMM Imported Copper Concentrate Index (weekly), USD/dmt -- the TC series
#    the source article's headline figures are built from.
# ---------------------------------------------------------------------------
# Each tuple: (date, value, status, note)
CU_TC_WEEKLY_RAW = [
    ("2026-01-02", -45.0, "cited-approx",
     "SMM spot copper concentrate index ~-$45/dmt 'at the start of the "
     "year' (news.metal.com, 'Copper Smelting Industry Faces the Test of "
     "Extremely Low TCs', undated-but-Feb-2026-context); cross-checked "
     "against Mysteel's independently-run index at -$44.76/dmt for the "
     "same period, and SMM's own Dec 26 2025 print of -$44.9/dmt "
     "('Downstream Producers Cut Output to Cope with Record-high Copper "
     "Prices') -- three sources agree to within $0.30/dmt."),
    ("2026-02-27", -70.0, "cited-approx",
     "SMM spot copper concentrate index 'approaching -$70/dmt' as the "
     "Feb 28 2026 US/Israel strikes on Iran triggered the Hormuz "
     "disruption (news.metal.com, 'Copper Smelting Industry Faces the "
     "Test of Extremely Low TCs')."),
    ("2026-04-09", -78.50, "cited",
     "DIFFERENT INDEX, cross-check only: S&P Global Platts CIF China "
     "clean copper concentrate TC assessment, -$78.50/t on 2026-04-09 "
     "(S&P Global Commodity Insights, 'Chinese copper concs TC/RC to "
     "remain under pressure in Q2'). Not blended into the SMM series "
     "below -- kept separate because Platts and SMM use different panels "
     "and can print different absolute levels for the same week; see "
     "model_b.py's index-provider robustness check."),
    ("2026-04-17", -78.61, "cited",
     "SMM Imported Copper Concentrate Index (weekly), implied prior-week "
     "print from the 2026-04-24 SMM article's 'down $2.83/dmt from the "
     "previous reading of -$78.61/dmt' (news.metal.com)."),
    ("2026-04-24", -81.44, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$81.44/dmt "
     "(news.metal.com, 'Sulphuric Acid Prices Key to Copper Smelter "
     "Cutbacks'; also the source article's own citation)."),
    ("2026-05-15", -102.84, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$102.84/dmt, "
     "first time below -$100/dmt (news.metal.com, 'Copper Concentrate "
     "TCs Break Through Negative Triple Digits'). Cross-checked: "
     "Mysteel's own index printed -$103.62/dmt the same day."),
    ("2026-06-26", -124.50, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$124.5/dmt "
     "(news.metal.com, 'China's Copper Cathode Production Continued to "
     "Decline More Than Expected in July', which quotes this as the "
     "prior print ahead of the Jul-31 figure below)."),
    ("2026-07-31", -159.37, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$159.37/dmt, down "
     "$30.31/dmt from -$124.5/dmt on Jun 26 (news.metal.com; also the "
     "source article's own citation)."),
    ("2026-08-28", -199.84, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$199.84/dmt "
     "(source article, citing the print one week before its own "
     "2026-09-04 headline figure)."),
    ("2026-09-04", -200.31, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$200.31/dmt "
     "(source article's headline TC figure)."),
    ("2026-09-11", -209.70, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$209.70/dmt -- "
     "back-calculated from the 2026-09-18 print's own citation ('down "
     "$12.19/dmt from -$209.7/dmt in the previous period'); "
     "news.metal.com, 'Imported Copper Concentrate TCs Continue to Fall, "
     "with Some Smelters Beginning to Show Willingness to Cut "
     "Production' (SMM Copper Concentrate Spot Weekly Review, "
     "2026-09-18). Added 2026-09-25."),
    ("2026-09-18", -221.89, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$221.89/dmt, a "
     "new record low (news.metal.com, same 2026-09-18 SMM Copper "
     "Concentrate Spot Weekly Review as above). Added 2026-09-25."),
    ("2026-09-24", -224.53, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$224.53/dmt, down "
     "$2.64/dmt from -$221.89/dmt 'in the previous period' -- another new "
     "record low (news.metal.com, 'CSPT Meeting Decides Not to Set Q4 "
     "Copper Concentrate TC Guidance Price -- SMM Copper Concentrate "
     "Spot Weekly Review', 2026-09-24). Dated as SMM reports it: "
     "September 24, 2026 -- a Thursday, one day off the index's usual "
     "Friday publication day, plausibly to clear the desk ahead of "
     "China's Oct National Day holiday. This is the most recent print "
     "as of this project's 2026-09-25 data-extension pass; charted on "
     "the nearest Friday grid date (2026-09-25) for trend/stress-test "
     "consistency with the rest of the series -- see "
     "`_interpolate_to_grid()`'s docstring. The CSPT (China Smelters "
     "Purchase Team, the group that normally sets Chinese smelters' "
     "quarterly TC guidance) declining to set ANY Q4 guidance price at "
     "all is itself new information: it signals the smelter side and "
     "miners/traders could not agree on a floor, not that -$224.53 is "
     "necessarily durable."),
]

# ---------------------------------------------------------------------------
# 2. SMM China Copper-Smelting Sulphuric Acid Index (weekly), RMB/t -- the
#    acid series the source article's "cushion shrinking" claim is built on.
# ---------------------------------------------------------------------------
CU_ACID_WEEKLY_RAW = [
    ("2026-01-02", 919.5, "cited-approx",
     "SMM China Copper Smelting Acid Index, RMB 919.5/t 'at the start of "
     "the year' (news.metal.com, '[SMM Analysis] China's Sulphuric Acid "
     "Production and Sulphur/Sulphuric Acid Imports/Exports in H1 2026')."),
    ("2026-02-13", 930.0, "cited-approx",
     "Midpoint placeholder date within the source's stated 'Jan-Feb "
     "moved narrowly in the RMB 900-960/t range' (same H1-2026 SMM "
     "analysis as above) -- no single dated print exists for this week; "
     "930 is the midpoint of the cited range, not a specific print."),
    ("2026-03-27", 1235.5, "cited-approx",
     "SMM China Copper Smelting Acid Index 'climbed quickly to RMB "
     "1,235.5/t' in March, following sulphur's Hormuz-driven surge (same "
     "H1-2026 SMM analysis). Dated to end-of-March as the analysis "
     "reports it as the March figure; not a specific dated print."),
    ("2026-04-24", 1660.5, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,660.5/t, up RMB "
     "31.5/t WoW (news.metal.com, 'Sulphuric Acid Prices Key to Copper "
     "Smelter Cutbacks'; consistent with the H1-2026 analysis's separate "
     "'rose further to RMB 1,657/t in April')."),
    ("2026-05-15", 1665.0, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,665/t, up 83.7% from "
     "the start of the year (news.metal.com, 'Copper Concentrate TCs "
     "Break Through Negative Triple Digits')."),
    ("2026-06-26", 1700.0, "cited-approx",
     "Placeholder date (aligned to the TC series' Jun-26 point) within "
     "the source's stated 'May-June remained in a high range of RMB "
     "1,650-1,750/t' (H1-2026 SMM analysis) -- midpoint of the range, "
     "not a specific dated print."),
    ("2026-07-10", 1789.0, "cited-approx",
     "Peak: SMM index 'briefly touched RMB 1,789/t in early July' "
     "(H1-2026 SMM analysis; also the source article's own citation of "
     "the pre-decline peak level). Dated to Jul 10 as a representative "
     "'early July' Friday print -- the source does not give an exact date."),
    ("2026-07-17", 1763.0, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,763/t 'as of 17 July' "
     "(H1-2026 SMM analysis) -- the first confirmed print of the decline "
     "that reaches 'nine consecutive weeks' by 2026-09-04."),
    ("2026-07-24", 1743.0, "interpolated",
     "No citation found for this week; linearly interpolated between "
     "2026-07-17 (1,763) and 2026-08-07 (1,703, see below)."),
    ("2026-07-31", 1723.0, "interpolated",
     "No citation found for this week; linearly interpolated between "
     "2026-07-17 (1,763) and 2026-08-07 (1,703, see below)."),
    ("2026-08-07", 1703.0, "cited",
     "Back-calculated from the 2026-08-14 print's own citation ('down "
     "RMB 72/t WoW' from this week) -- see next row. Treated as cited, "
     "not interpolated, since it is implied directly by a dated source, "
     "not smoothed between two distant points."),
    ("2026-08-14", 1631.0, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,631/t, down RMB 72/t "
     "WoW, the SIXTH consecutive weekly pullback (news.metal.com, "
     "'China's Sulphuric Acid Market Continues to Hit Bottom')."),
    ("2026-08-21", 1607.0, "interpolated",
     "No citation found for this week; linearly interpolated between "
     "2026-08-14 (1,631) and 2026-08-28 (1,583.5, see below)."),
    ("2026-08-28", 1583.5, "cited",
     "Back-calculated from the source article's 2026-09-04 figure ('down "
     "44 yuan/t from the previous Friday') -- 1,539.5 + 44 = 1,583.5."),
    ("2026-09-04", 1539.5, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,539.5/t, the NINTH "
     "consecutive weekly decline (source article's headline acid "
     "figure)."),
    ("2026-09-11", 1418.0, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,418.0/t, the TENTH "
     "consecutive weekly decline, down RMB 121.5/t or 7.9% WoW -- "
     "back-calculated from the 2026-09-18 print's own citation of 'the "
     "previous week's drop of 121.5 yuan/mt or 7.9%' (news.metal.com, "
     "SMM China Sulphuric Acid Weekly Review, 2026-09-18). Added "
     "2026-09-25."),
    ("2026-09-18", 1351.0, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,351.0/t, down RMB 67/t "
     "or 4.7% from RMB 1,418/t -- the ELEVENTH consecutive weekly "
     "decline, a sharp narrowing from the prior week's 7.9% drop "
     "(news.metal.com, SMM China Sulphuric Acid Weekly Review, "
     "2026-09-18). Added 2026-09-25."),
    ("2026-09-24", 1247.5, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,247.5/t, down RMB "
     "103.5/t or 7.7% from RMB 1,351/t the previous Friday -- the "
     "TWELFTH consecutive weekly decline (news.metal.com, 'CSPT Meeting "
     "Decides Not to Set Q4 Copper Concentrate TC Guidance Price', "
     "2026-09-24 SMM Sulphuric Acid Weekly Review). Dated and "
     "grid-charted exactly as the 2026-09-24 TC print above -- see that "
     "row's note. Added 2026-09-25; most recent print as of this "
     "project's current data-extension pass."),
]


def _weekly_frame(raw: list[tuple], value_col: str) -> pd.DataFrame:
    df = pd.DataFrame(raw, columns=["date", value_col, "status", "note"])
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").sort_index()


def cu_tc_weekly() -> pd.DataFrame:
    """SMM Imported Copper Concentrate Index (weekly), USD/dmt, with
    provenance columns. Sparse -- only the dates actually cited/derived
    above are rows here. Use `cu_tc_weekly_interpolated()` for a full
    weekly grid."""
    return _weekly_frame(CU_TC_WEEKLY_RAW, "tc_usd_dmt")


def cu_acid_weekly() -> pd.DataFrame:
    """SMM China Copper Smelting Acid Index (weekly), RMB/t, with
    provenance columns."""
    return _weekly_frame(CU_ACID_WEEKLY_RAW, "acid_cny_t")


def _interpolate_to_grid(df: pd.DataFrame, value_col: str, freq="W-FRI") -> pd.DataFrame:
    """Resample sparse cited/derived points onto a regular weekly (Friday)
    grid via linear interpolation, carrying a provenance flag so a reader
    can always tell which numbers were actually published vs filled in for
    charting/stress-test convenience. Never used to overwrite a cited
    value -- cited dates are reindexed onto the nearest grid Friday only
    if they don't already land exactly on one; interpolation only fills
    grid weeks that had no citation at all.

    BUG FIX (found 2026-09-25, while adding the 2026-09-24 TC/acid prints --
    see README.md changelog): `full_index` used to be built as
    `pd.date_range(df.index.min(), df.index.max(), freq=freq)`. Because
    `date_range` with an anchored offset like "W-FRI" only ever lands ON
    that offset's dates, this silently CAPPED the grid at the last on-cycle
    Friday <= df.index.max() whenever the most recent cited point itself
    fell on an off-cycle date -- e.g. SMM published its 2026-09-24 print on
    a Thursday (a day early, plausibly to clear the desk before China's Oct
    National Day holiday) instead of the usual Friday. df.index.max() was
    then 2026-09-24, but the old `full_index` stopped at 2026-09-18: the
    newest cited point never got its own grid row, `weekly.iloc[-1]` (used
    throughout model_a.py / acid_cushion_monitor.py / model_b.py as "the
    latest reading") would have silently reported a THREE-WEEK-STALE value
    as current, and this directly contradicted README.md's own claim that
    "the interpolation grid updates automatically once new cited anchors
    are added." Fixed by rolling the grid's end up to the next on-cycle
    date whenever df.index.max() isn't already on-cycle, so any cited
    point -- on-cycle or not -- always gets a grid node. An off-cycle date
    still gets ASSIGNED to the nearest on-cycle grid label (e.g. 2026-09-24
    -> grid row 2026-09-25) via the existing nearest/3-day-tolerance
    reindex below, exactly like every other "cited-approx" date in this
    module already is -- but never silently dropped. The true reported
    date always stays visible in the raw (non-interpolated) `note` field
    and in `cu_tc_weekly()` / `cu_acid_weekly()`, which are untouched by
    this grid-snapping."""
    grid_end = pd.date_range(start=df.index.max(), periods=1, freq=freq)[0]
    full_index = pd.date_range(df.index.min(), grid_end, freq=freq)
    combined_index = df.index.union(full_index).sort_values()
    out = df[[value_col]].reindex(combined_index)
    out[value_col] = out[value_col].interpolate(method="time")
    out = out.reindex(full_index, method="nearest", tolerance=pd.Timedelta("3D")).ffill()

    # Status is computed SEPARATELY from the value, by snapping each raw
    # cited/derived date straight onto its nearest grid date (same 3-day
    # tolerance as the value's own snap above). This matters specifically
    # for an off-cycle raw date (e.g. the 2026-09-24 Thursday print, which
    # lands on grid date 2026-09-25): the OLD version of this line built
    # `status` off `combined_index` (raw dates UNION grid dates), so an
    # off-cycle raw date and its nearby grid date were two DIFFERENT rows
    # in that intermediate frame -- the raw date correctly got its own
    # "cited" status, but the grid date (which is what actually survives
    # into the final output) had no status of its own and fell through to
    # the "interpolated (grid-fill)" default, mislabeling a genuinely
    # cited value as merely interpolated. Reindexing `status` straight
    # from `df` onto `full_index` with the same nearest/3-day rule used
    # for the value avoids that: a value and the status describing it are
    # now guaranteed to come from the same source row.
    out["status"] = df["status"].reindex(
        full_index, method="nearest", tolerance=pd.Timedelta("3D")
    ).fillna("interpolated (grid-fill)")
    return out


def _selfcheck_grid_never_drops_latest_point():
    """Regression test for the bug fixed above: a cited point after the
    last on-cycle grid date, and not itself on-cycle, must still appear as
    the grid's own last row -- not be silently dropped."""
    raw = [
        ("2026-08-14", 100.0, "cited", "x"),
        ("2026-08-28", 90.0, "cited", "x"),
        ("2026-09-04", 80.0, "cited", "x"),
        ("2026-09-24", 50.0, "cited", "x"),  # off-cycle Thursday, like the real Sep-24 TC/acid prints
    ]
    df = _weekly_frame(raw, "v")
    grid = _interpolate_to_grid(df, "v")
    assert grid.index.max() >= pd.Timestamp("2026-09-24"), (
        f"grid dropped the latest cited point: last grid date is "
        f"{grid.index.max()}, expected >= 2026-09-24")
    assert grid["v"].iloc[-1] == 50.0, (
        f"grid's last row does not carry the latest cited value: got "
        f"{grid['v'].iloc[-1]}, expected 50.0")
    assert grid["status"].iloc[-1] == "cited", (
        f"grid's last row mislabels a genuinely cited, off-cycle-snapped "
        f"point as {grid['status'].iloc[-1]!r} instead of 'cited'")


def cu_tc_weekly_interpolated() -> pd.DataFrame:
    """Full Friday-cadence grid of the TC series for trend/%-change and
    stress-test use. Points not already 'cited'/'cited-approx' in
    CU_TC_WEEKLY_RAW are grid-fill interpolations -- check the `status`
    column before quoting any individual week from this externally."""
    return _interpolate_to_grid(cu_tc_weekly(), "tc_usd_dmt")


def cu_acid_weekly_interpolated() -> pd.DataFrame:
    """Full Friday-cadence grid of the acid series -- see
    cu_tc_weekly_interpolated()'s docstring for the same caveat."""
    return _interpolate_to_grid(cu_acid_weekly(), "acid_cny_t")


# ---------------------------------------------------------------------------
# 3. FX -- USD/CNY, period-matched (replaces the old flat 7.1 constant used
#    for every quarter 2023-2026 in real_data_check.py; see README.md's
#    changelog -- that was flagged as a known limitation and is fixed here).
#    2026 values are averages of daily closes reported by exchangerates.org
#    / exchange-rates.org / valutafx.com (checked 2026-09-16); 2023-2025
#    values are broad, rounded quarterly levels from general market
#    reporting for those periods, NOT a period-matched daily series --
#    still a real improvement over one constant spanning 3 years, but not
#    to be quoted as a precise FX print for any single day in 2023-2025.
# ---------------------------------------------------------------------------
USD_CNY_QUARTERLY = {
    "2023-Q4": 7.15,
    "2024-Q1": 7.10,
    "2024-Q3": 7.15,
    "2025-Q1": 7.25,
    "2025-Q4": 7.15,
    "2026-Q1": 6.95,   # avg of Jan ~6.99 -> Mar ~6.93 (valutafx.com, exchangerates.org)
    "2026-Q2": 6.84,   # avg of Apr ~6.89, May ~6.84, Jun ~6.80 (exchangerates.org monthly avgs)
    "2026-Q3": 6.76,   # avg of Jul ~6.78, Aug ~6.74, Sep-to-date(16th) ~6.71 (exchangerates.org, tradingeconomics.com)
}


def cny_to_usd(value_cny: float, quarter_label: str) -> float:
    """Period-matched CNY->USD conversion using USD_CNY_QUARTERLY. Pass a
    quarter label like '2026-Q3'; falls back to the nearest quarter (by
    calendar order) with a printed warning if the exact label isn't in the
    table, rather than silently defaulting to a flat rate."""
    if quarter_label in USD_CNY_QUARTERLY:
        rate = USD_CNY_QUARTERLY[quarter_label]
    else:
        keys = sorted(USD_CNY_QUARTERLY)
        target_ord = pd.Period(quarter_label, "Q").ordinal
        nearest = min(keys, key=lambda k: abs(pd.Period(k, "Q").ordinal - target_ord))
        rate = USD_CNY_QUARTERLY[nearest]
        print(f"WARNING: no USD/CNY rate for {quarter_label}; using nearest ({nearest} = {rate}).")
    return round(value_cny / rate, 1)


def cny_to_usd_by_date(value_cny: float, date) -> float:
    """Same as cny_to_usd but keyed by an actual date -- maps the date to
    its calendar quarter first. Convenience wrapper for the weekly series
    above, which are dated, not quarter-labelled."""
    p = pd.Period(pd.Timestamp(date), "Q")
    q = f"{p.year}-Q{p.quarter}"   # match USD_CNY_QUARTERLY's "YYYY-Qn" key format exactly
    return cny_to_usd(value_cny, q)


# ---------------------------------------------------------------------------
# 4. Kamoa-Kakula (Ivanhoe Mines) -- integrated mine+smelter, disclosed
#    per POUND OF PAYABLE COPPER, quarterly. THIS IS A DIFFERENT UNIT BASIS
#    from SmelterParams elsewhere in this project (which is per TONNE OF
#    CONCENTRATE PROCESSED, the Nexa/Freeport custom-smelter convention).
#    Do not feed these numbers into SmelterParams / smelter_margin()
#    directly -- see model_c.py's module docstring for why, and for the
#    dimension-safe way this project actually uses them
#    (margin_model.implied_acid_yield_and_buffer()).
# ---------------------------------------------------------------------------
KAMOA_KAKULA_QUARTERLY = {
    "2025-Q4": {
        "smelter_opex_usd_lb": None,       # not disclosed on a comparable basis -- smelter only produced first anodes late in the quarter
        "acid_credit_usd_lb": None,
        "logistics_usd_lb": 0.70,          # cited, pre-smelter-ramp logistics cost, for context only
        "acid_production_kt": None,
        "acid_realized_usd_t": None,
        "note": "Kamoa-Kakula's on-site smelter produced its first batch of anodes "
                "in late Q4 2025 and was not yet at meaningful utilisation -- no "
                "comparable opex/acid-credit split was disclosed for the full quarter.",
    },
    "2026-Q1": {
        "smelter_opex_usd_lb": 0.27,
        "acid_credit_usd_lb": 0.32,
        "logistics_usd_lb": 0.22,
        "acid_production_kt": 117.871,
        "acid_sold_kt": 107.700,
        "contract_price_usd_t": 725.0,     # "new contract prices up >50% year-to-date"
        "realized_acid_price_usd_t": None,  # Ivanhoe's release did not give a clean Q1 weighted-average REALIZED price (only the new contract level) -- left NaN rather than assumed equal to the contract price. See STRATEGY_NOTE.md.
        "acid_cushion_ratio": round(0.32 / 0.27, 4),   # 118.5% -- acid MORE than covered smelter opex in Q1
        "smelter_utilisation_pct": 60,
        "note": "Ivanhoe Mines Q1 2026 results (2026-05-06 release). Smelter ramped "
                "to ~60% capacity during the quarter, having produced first anodes "
                "in late Q4 2025.",
    },
    "2026-Q2": {
        "smelter_opex_usd_lb": 0.41,
        "acid_credit_usd_lb": 0.39,
        "logistics_usd_lb": 0.24,
        "acid_production_kt": 112.307,
        "realized_acid_price_usd_t": 465.0,
        "contract_price_usd_t": 840.0,     # July/August contracts, "~80% higher" than the Q2 realized average
        "acid_cushion_ratio": round(0.39 / 0.41, 4),   # 95.1% -- acid almost, not quite, covered smelter opex in Q2
        "note": "Ivanhoe Mines Q2 2026 results (2026-07-30 release); this is also "
                "the exact figure the source article cites for Kamoa-Kakula. "
                "Smelter opex rose from $0.27/lb to $0.41/lb in Q2 (higher "
                "utilisation ramp-up costs); acid credit rose only $0.27 -> $0.39, "
                "not enough to keep pace -- this is the quarter-over-quarter "
                "cushion-narrowing visible in Kamoa's OWN disclosed numbers, "
                "before the SMM index-level shrinkage becomes visible in Q3.",
    },
    "2026-Q3": {
        "smelter_opex_usd_lb": None,   # not yet reported -- Ivanhoe typically reports Q3 in late Oct/Nov
        "acid_credit_usd_lb": None,
        "contract_price_usd_t": 840.0,  # Jul/Aug contracts carried forward; no Sep print disclosed yet
        "note": "Ivanhoe has not yet reported Q3 2026 results as of this project's "
                "data-collection date (2026-09-16); typical reporting lag is "
                "late October/November. Do not fabricate a Q3 opex/acid-credit "
                "split -- use the Jul/Aug $840/t contract level and the SMM/DRC "
                "benchmark trend as the best available forward indicators "
                "instead (see REGIONAL_ACID_BENCHMARK below and "
                "acid_cushion_monitor.py).",
    },
}


# ---------------------------------------------------------------------------
# 5. SMM regional acid benchmark -- EXW DRC / EXW Zambia. Launched 2026-06-05
#    (SMM announcement); only ONE confirmed dated print exists in the
#    checked sources (2026-09-04), described there as "unchanged for five
#    consecutive weeks." Treated as flat back to ~2026-08-01 on that basis
#    -- explicitly flagged as possibly a thin-market non-print, not
#    necessarily five weeks of genuine price stability (this is the exact
#    ambiguity the source article itself calls out).
# ---------------------------------------------------------------------------
REGIONAL_ACID_BENCHMARK = {
    "launch_date": "2026-06-05",
    "weekly": [
        # date, drc_usd_t (midpoint of $910-960), zambia_usd_t (midpoint of $380-420), status
        ("2026-08-01", 935.0, 400.0, "cited-approx (flat, back-dated from the 5-week-unchanged note below)"),
        ("2026-08-07", 935.0, 400.0, "cited-approx (flat, back-dated)"),
        ("2026-08-14", 935.0, 400.0, "cited-approx (flat, back-dated)"),
        ("2026-08-21", 935.0, 400.0, "cited-approx (flat, back-dated)"),
        ("2026-08-28", 935.0, 400.0, "cited-approx (flat, back-dated)"),
        ("2026-09-04", 935.0, 400.0,
         "cited: EXW DRC $910-960/t (~$935), EXW Zambia $380-420/t (~$400), "
         "'unchanged for five consecutive weeks' (source article, citing SMM). "
         "SMM itself has since announced discontinuation of some related FOB "
         "acid price points (see MARKET_CONTEXT_SEPT_2026['smm_fob_discontinued'))."),
    ],
    "no_data_before": "2026-08-01",
    "caveat": (
        "A flat 5-week print on a benchmark that only launched ~9 weeks earlier "
        "(2026-06-05) is consistent with genuine regional price stability, but "
        "equally consistent with a thin market that simply had no new "
        "transaction to move the assessment. The source article makes exactly "
        "this point -- both readings should be held at once, not resolved in "
        "favour of the more flattering one. Do not treat 'unchanged for 5 "
        "weeks' as a stronger claim than 'no fresh print for 5 weeks'."
    ),
}

# Kamoa-Kakula's own realized contract price sits BELOW the DRC benchmark
# despite Kamoa's integrated (mine + smelter) structure that should, in
# principle, help realize a premium -- the article's "integration is a
# hypothesis, not a demonstrated edge" point:
KAMOA_VS_DRC_BENCHMARK_SPREAD_USD_T = round(840.0 - REGIONAL_ACID_BENCHMARK["weekly"][-1][1], 1)  # -95.0


# ---------------------------------------------------------------------------
# 6. Sulphur / sulphuric-acid trade flow context (China customs, Kpler) --
#    used as CONTEXT, not converted into a binary signal (per the review:
#    PMI/trade-flow variables should read as evidence, not pass/fail gates).
# ---------------------------------------------------------------------------
SULPHUR_TRADE_CONTEXT = {
    "china_h2so4_exports_may2026_kt": 116.7,
    "china_h2so4_exports_jun2026_t": 980.12,     # SMM: "up over 99% MoM" is a typo-prone framing in the source language for a >99% COLLAPSE from May -- treat the absolute levels (116,700t -> 980t) as the reliable figures, not the percentage label
    "china_h2so4_exports_jul2026_t": 976.24,     # confirms the June collapse was not a one-month blip -- July stayed near-zero too (SMM, "up 8.82% MoM" off a near-zero June base, still down 99.75% YoY)
    "china_sulphur_imports_jul2026_t": 385403.834,  # SMM: +161.99% MoM, -64.76% YoY -- imports partially recovering off a low base, still far below normal
    "kpler_global_sulphur_export_decline_pct_from_late_feb_2026": 45,
    "kpler_sulphur_stranded_gulf_kt": 600,
    "smm_fob_discontinued": (
        "SMM announced discontinuation of its Chinese Sulphuric Acid FOB "
        "Index (copper-smelter basis) and copper-smelting-acid FOB price "
        "points by province, citing the June export-volume collapse leaving "
        "too few firm bid/offer samples to sustain the index (metal.com "
        "announcement) -- a genuine data-availability constraint on any "
        "acid-export-price series going forward, not just an editorial choice."
    ),
    "acid_export_halt_vs_fertiliser_export_window": (
        "ADDED 2026-09-25 -- clarifies the source article's third 'what to "
        "watch' variable, which names only 'China's fertiliser export "
        "policy after the August 31 deadline'. Two DIFFERENT Chinese "
        "export policies are relevant here, and the article's phrasing "
        "risks conflating them: (1) the sulphuric-ACID-specific export "
        "halt itself -- the direct driver of the May->June export collapse "
        "in this dict (116.7kt -> 980t) -- which CRU reporting (citing the "
        "relevant government decree) describes as in force from the start "
        "of May THROUGH THE END OF 2026, i.e. not tied to Aug 31 at all; "
        "and (2) a SEPARATE, ROUTINE, ANNUAL phosphate-FERTILISER (DAP/MAP) "
        "export-declaration control that China implements every year from "
        "March 14 to August 31 (this is the actual mechanism behind the "
        "article's 'August 31 deadline' -- an every-year expiry date, not "
        "a discretionary response invented for the 2026 acid squeeze). On "
        "this second, narrower point, evidence checked 2026-09-25 is "
        "ITSELF mixed: one SMM flash note says the routine window is "
        "'expected to be lifted' from Sept 1 as usual; S&P Global Platts "
        "(2026-09-02) reports producers had received no official guidance "
        "on DAP/MAP export resumption and a trader thought exports might "
        "not resume in 2026 at all. Net read: the fertiliser-export "
        "question the article flags has NOT cleanly resolved either way, "
        "but it was likely never the right lever on the acid glut "
        "specifically -- the acid export halt runs on its own, longer "
        "timeline (through end-2026) regardless of what happens with "
        "phosphate fertiliser exports. That points toward 'sticky, "
        "policy-driven' for the acid-export side of the glut, independent "
        "of the fertiliser-demand question the article poses. Sources: "
        "CRU smelter-economics piece (cited elsewhere in this file) for "
        "the acid-halt duration; SMM Flash on phosphate-fertiliser export "
        "controls; S&P Global Commodity Insights, 'China phosphate "
        "fertilizer exporters await clarity...', 2026-09-02."
    ),
    "note": (
        "China's sulphuric-acid export collapse (source article's central "
        "supply-side story) and the Kpler-tracked Gulf sulphur disruption are "
        "DIFFERENT mechanisms moving through the same chain -- one is a "
        "China-specific export-policy change, the other a Hormuz-linked "
        "feedstock shock. Domestic sulphur itself rebounded ~7.8% WoW in "
        "early September (source article) even as acid kept falling -- rising "
        "input cost alongside falling output price is margin compression for "
        "ACID PRODUCERS, not a clean confirmation of either a pure "
        "demand-side or pure supply-side story for the acid price move."
    ),
}


# ---------------------------------------------------------------------------
# 7. CRU smelter-income-mix figures (cited in source article) -- structural
#    context for why the acid channel now matters as much as it does.
# ---------------------------------------------------------------------------
CRU_SMELTER_INCOME_MIX = {
    "tc_share_2018_pct": 39,
    "free_metal_share_2025_pct_range": (50, 53),
    "byproduct_credit_share_2025_pct_range": (25, 27),   # predominantly sulphuric acid
    "caveat": (
        "CRU built the 2025 split against TCs nowhere near as negative as "
        "the -$200/dmt print seen by Sep 2026 -- at current levels TC is a "
        "net SUBTRACTION free metal and acid must cover outright, so the "
        "real H2-2026 mix is almost certainly skewed further toward acid/"
        "metal than this 2025 snapshot shows (source article's own caveat)."
    ),
    "source": "CRU, published April 2026, cited in source article.",
}


# ---------------------------------------------------------------------------
# 8. Demand / inventory context (PMI, COMEX) -- CONTEXT VARIABLES per the
#    review: read as evidence, never forced into a binary "demand OK / not
#    OK" gate (see thesis_dashboard.py's condition_demand()).
# ---------------------------------------------------------------------------
MARKET_CONTEXT_SEPT_2026 = {
    "as_of": "2026-09-04/09",
    "china_nbs_manufacturing_pmi_aug2026": 49.8,
    "china_ratingdog_manufacturing_pmi_aug2026": 51.5,
    "us_h1_2026_refined_cu_cathode_imports_kt": 885.0,
    "comex_cu_inventory_record_t": 675185,
    "zinc": {
        "smm_spot_zn_tc_aug2026_usd_dmt": -113.0,   # all-time low (Reuters/Mining Weekly, 2026-09-03)
        "zn_tc_annual_benchmark_2026_usd_dmt": 85.0,
        "smm_domestic_zn50_tc_sept2026_cny_mt_zn": -1550.0,  # "flat WoW", awaiting Sept TC pricing
        "note": (
            "Zinc shows the SAME by-product-cushion mechanism (silver + "
            "sulphuric acid) at an even more extreme TC level than copper's "
            "-- supporting (cross-metal) evidence, not the central test. Do "
            "not let zinc's reading move `thesis_confirmed` for the copper "
            "acid-cushion thesis; see thesis_dashboard.py."
        ),
    },
    "note": (
        "PMI readings disagree by 1.7pts depending on survey (official NBS "
        "vs RatingDog/Caixin-style) -- 'Chinese demand is collapsing' is too "
        "simple a read on this data alone. COMEX's record inventory partly "
        "reflects US tariff-driven trade-flow positioning, not pure refined-"
        "metal scarcity or surplus. Both readings are held here as CONTEXT, "
        "not converted into a pass/fail demand signal."
    ),
}


# ---------------------------------------------------------------------------
# 9. Physical-response evidence -- production/output signals possibly
#    linked to the acid-cushion / extreme-TC mechanism. Used by
#    thesis_dashboard.py's condition_physical_response(); kept as a
#    separate small dict (rather than folded into MARKET_CONTEXT_SEPT_2026)
#    because, unlike PMI/COMEX, this is specifically about SMELTER
#    behaviour, the article's Claim E ("this may change smelter
#    behaviour... production cuts / operating changes").
# ---------------------------------------------------------------------------
PHYSICAL_RESPONSE_EVIDENCE = {
    "smm_tc_negotiation_resistance": (
        "SMM's own Sep-4 weekly note: smelters showing 'greater resistance "
        "to accepting deeper negative TC/RCs' -- spot deals concluded at "
        "roughly index-minus-$20 to $28/dmt, with lower-priced deals "
        "struggling to gain volume (source article). This is resistance in "
        "NEGOTIATION, not a confirmed output cut."
    ),
    "china_cathode_output_july2026": (
        "SMM: 'China's Copper Cathode Production Continued to Decline More "
        "Than Expected in July' (news.metal.com, Jul 2026) -- a REAL "
        "output decline, but not cleanly attributable to the acid-cushion "
        "mechanism specifically vs. concentrate/ore-supply tightness more "
        "generally (the two are related but not identical -- a smelter can "
        "cut output because it can't source enough concentrate at all, "
        "independent of whether the TC/acid margin math on the concentrate "
        "it DOES get is favourable)."
    ),
    "smm_production_cut_intentions_sept18": (
        "ADDED 2026-09-25. news.metal.com, 'Imported Copper Concentrate "
        "TCs Continue to Fall, with Some Smelters Beginning to Show "
        "Willingness to Cut Production' (SMM Copper Concentrate Spot "
        "Weekly Review, 2026-09-18): SMM reports declining smelter "
        "willingness to accept current spot terms, with 'production cut "
        "intentions emerging'. This is a genuine escalation from the "
        "Sept-4 'negotiating resistance' framing -- it is the first "
        "sources-checked instance of language about actually CUTTING "
        "output, not just pushing back on price. Still short of a "
        "confirmed, named smelter announcing a specific curtailment: "
        "'intentions emerging' is SMM's own characterization of "
        "sentiment, not a tally of announced cuts."
    ),
    "cspt_no_q4_tc_guidance_sept24": (
        "ADDED 2026-09-25. news.metal.com, 'CSPT Meeting Decides Not to "
        "Set Q4 Copper Concentrate TC Guidance Price -- SMM Copper "
        "Concentrate Spot Weekly Review', 2026-09-24: the CSPT (China "
        "Smelters Purchase Team -- the group that normally sets a "
        "quarterly TC floor/guidance for Chinese smelters) met and did "
        "NOT set a Q4 guidance price at all. A failure to agree on any "
        "number is itself informative -- it suggests the smelter side and "
        "the miner/trader side are too far apart to converge on a "
        "reference TC, consistent with (but not proof of) the acid-cushion "
        "thesis's premise that the negative-TC regime is now genuinely "
        "contested rather than just an accepted, priced-in cost of doing "
        "business. Read as PROCESS evidence (the negotiation itself is "
        "breaking down), not as a physical output signal on its own."
    ),
    "reading": (
        "EMERGING, STRENGTHENING, still not CONFIRMED: as of the original "
        "2026-09-04/16 pass there was negotiating resistance plus an "
        "unattributed output decline. As of 2026-09-25, two more pieces of "
        "evidence point the same direction -- SMM's own language has moved "
        "from 'resistance' to 'production cut intentions emerging' "
        "(2026-09-18), and CSPT's quarterly guidance-setting process itself "
        "broke down for Q4 (2026-09-24). Neither is a named smelter "
        "announcing a specific, dated curtailment explicitly attributed to "
        "the acid cushion -- that bar still has not been cleared in the "
        "sources checked. Treat 'physical response' as a claim that has "
        "gotten materially closer to CONFIRMED over the past three weeks, "
        "not one that has arrived there."
    ),
}


if __name__ == "__main__":
    _selfcheck_grid_never_drops_latest_point()
    _tc_grid = cu_tc_weekly_interpolated()
    _acid_grid = cu_acid_weekly_interpolated()
    assert _tc_grid.index.max() == pd.Timestamp("2026-09-25"), (
        f"TC grid's last date is {_tc_grid.index.max()}, expected "
        f"2026-09-25 (the Friday nearest the 2026-09-24 cited print)")
    assert _acid_grid.index.max() == pd.Timestamp("2026-09-25"), (
        f"acid grid's last date is {_acid_grid.index.max()}, expected "
        f"2026-09-25")
    assert abs(_tc_grid["tc_usd_dmt"].iloc[-1] - (-224.53)) < 1e-6, (
        "TC grid's last value does not match the 2026-09-24 cited print")
    assert abs(_acid_grid["acid_cny_t"].iloc[-1] - 1247.5) < 1e-6, (
        "acid grid's last value does not match the 2026-09-24 cited print")
    print("copper_acid_data.py self-checks passed:")
    print(f"  TC grid runs through   {_tc_grid.index.max().date()}  "
          f"(latest: {_tc_grid['tc_usd_dmt'].iloc[-1]:.2f} USD/dmt, "
          f"status={_tc_grid['status'].iloc[-1]})")
    print(f"  Acid grid runs through {_acid_grid.index.max().date()}  "
          f"(latest: {_acid_grid['acid_cny_t'].iloc[-1]:.1f} CNY/t, "
          f"status={_acid_grid['status'].iloc[-1]})")