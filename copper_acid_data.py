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
main test. See STRATEGY_NOTE.md and docs/METHODOLOGY.md for the reasoning.

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
plus two new physical-response citations -- see the earlier README's changelog for
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
    ("2026-03-13", -60.39, "cited",
     "SMM Imported Copper Concentrate Index, -$60.39/dmt, first print below -$60 (news.metal.com, '[SMM Analysis] How Chinese Copper Smelters Navigate Counter-Cycle & Negative TCs', 2026-03-13). Added in the 2026-10-01 verification pass."),
    ("2026-04-17", -78.61, "cited",
     "SMM Imported Copper Concentrate Index (weekly), implied prior-week "
     "print from the 2026-04-24 SMM article's 'down $2.83/dmt from the "
     "previous reading of -$78.61/dmt' (news.metal.com). Link: https://news.metal.com/newscontent/103881993-Sulphuric-Acid-Prices-Key-to-Copper-Smelter-Cutbacks-Amid-Collapsing-TCs"),
    ("2026-04-24", -81.44, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$81.44/dmt "
     "(news.metal.com, 'Sulphuric Acid Prices Key to Copper Smelter "
     "Cutbacks'; also the source article's own citation). Link: https://news.metal.com/newscontent/103881993-Sulphuric-Acid-Prices-Key-to-Copper-Smelter-Cutbacks-Amid-Collapsing-TCs"),
    ("2026-05-15", -102.84, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$102.84/dmt, "
     "first time below -$100/dmt (news.metal.com, 'Copper Concentrate "
     "TCs Break Through Negative Triple Digits'). Cross-checked: "
     "Mysteel's own index printed -$103.62/dmt the same day. Link: https://news.metal.com/newscontent/103909269-Copper-Concentrate-TCs-Break-Through-Negative-Triple-Digits-What-Challenges-Do-Smelters-Face"),
    ("2026-06-26", -124.45, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$124.45/dmt (exact figure per the 2026-07-03 SMM weekly review; an earlier source rounded it to -$124.5) "
     "(news.metal.com, 'China's Copper Cathode Production Continued to "
     "Decline More Than Expected in July', which quotes this as the "
     "prior print ahead of the Jul-31 figure below). Link: https://news.metal.com/en/newscontent/103987313-mid-year-long-term-contract-pricing-scheme-settled-index-linked-model-breaks-new-ground-smm-copper-concentrates-spot-wee"),
    ("2026-07-03", -128.25, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$128.25/dmt, down $3.80 from -$124.45 (news.metal.com, 'Mid-Year Long-Term Contract Pricing Scheme Settled...', SMM Copper Concentrates Spot Weekly Review, 2026-07-03). Replaces a grid-fill interpolation (-131.47) -- added 2026-10-01. Link: https://news.metal.com/en/newscontent/103987313-mid-year-long-term-contract-pricing-scheme-settled-index-linked-model-breaks-new-ground-smm-copper-concentrates-spot-wee"),
    ("2026-07-10", -132.84, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$132.84/dmt, down $4.59 from -$128.25 -- published directly in the SMM weekly review of 2026-07-10 (news.metal.com) and repeated as the 'previous reading' in the 2026-07-17 review. Replaces a grid-fill interpolation (-138.45) -- added 2026-10-01. Link: https://news.metal.com/newscontent/103999281-las-tc-spot-caen-por-debajo-de-la-marca-de--130-y-la-brecha-entre-los-niveles-de-precios-psicológicos-de-las-fundiciones"),
    ("2026-07-17", -146.15, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$146.15/dmt, down $13.31 from -$132.84 (same 2026-07-17 SMM weekly review). Replaces a grid-fill interpolation (-145.42) -- added 2026-10-01. Link: https://news.metal.com/en/newscontent/104011502-spot-transactions-of-imported-copper-concentrates-increase-tcs-continue-to-deteriorate-smm-copper-concentrate-spot-weekl"),
    ("2026-07-24", -154.76, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$154.76/dmt -- the 'previous' reading in the 2026-07-31 SMM weekly review (news.metal.com, 'Cobre Panama mine restart accelerates...'). This is the 9-week reference point of the headline trend figures; it was a grid-fill interpolation (-152.40) until 2026-10-01. Link: https://news.metal.com/en/newscontent/104036547-cobre-panama-mine-restart-accelerates-imported-copper-concentrate-spot-tcs-continue-to-deteriorate-smm-copper-concentrat"),
    ("2026-07-31", -159.37, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$159.37/dmt, down "
     "$4.61/dmt from the prior-week print of -$154.76 (24 Jul) and $34.92/dmt "
     "from -$124.45 on 26 Jun (news.metal.com). An earlier note in this file "
     "said 'down $30.31 from -$124.5 on Jun 26' -- that arithmetic does not "
     "match these three cited prints (-124.5 -> -159.37 is -34.87). "
     "Link: https://news.metal.com/en/newscontent/104036547-cobre-panama-mine-restart-accelerates-imported-copper-concentrate-spot-tcs-continue-to-deteriorate-smm-copper-concentrat"),
    ("2026-08-07", -173.91, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$173.91/dmt, down $14.54 from -$159.37 (news.metal.com, 'Imported Copper Concentrate TCs Fall Steadily...', SMM weekly review 2026-08-07). Replaces a grid-fill interpolation (-169.49) -- added 2026-10-01. Link: https://news.metal.com/newscontent/104048814-imported-copper-concentrate-tcs-fall-steadily-some-construction-and-development-projects-at-el-teniente-the-worlds-large"),
    ("2026-08-14", -175.37, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$175.37/dmt, down $1.46 from -$173.91 (SMM weekly review published 2026-08-14, dated 13 Aug). Replaces a grid-fill interpolation -- added 2026-10-02. Link: https://news.metal.com/newscontent/104060789-chilean-copper-commission-again-lowered-its-annual-production-forecast-and-the-pace-of-decline-in-the-imported-copper-co"),
    ("2026-08-21", -182.14, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$182.14/dmt -- the 'previous period' in the 2026-08-28 SMM weekly review (news.metal.com, 'Jiangxi Copper Corporation Further Expanded...'). Replaces a grid-fill interpolation (-189.72) -- added 2026-10-01. Link: https://news.metal.com/newscontent/104085966-jiangxi-copper-corporation-further-expanded-its-global-resource-footprint-the-imported-copper-concentrate-index-continue"),
    ("2026-08-28", -199.84, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$199.84/dmt "
     "(source article, citing the print one week before its own "
     "2026-09-04 headline figure). Link: https://news.metal.com/newscontent/104085966-jiangxi-copper-corporation-further-expanded-its-global-resource-footprint-the-imported-copper-concentrate-index-continue"),
    ("2026-09-04", -200.31, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$200.31/dmt "
     "(source article's headline TC figure). Link: https://news.metal.com/newscontent/104099029-codelco-q2-own-copper-production-declined-yoy-spot-tc-decline-slowed-smm-copper-concentrates-spot-weekly-review"),
    ("2026-09-11", -209.70, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$209.70/dmt -- "
     "back-calculated from the 2026-09-18 print's own citation ('down "
     "$12.19/dmt from -$209.7/dmt in the previous period'); "
     "news.metal.com, 'Imported Copper Concentrate TCs Continue to Fall, "
     "with Some Smelters Beginning to Show Willingness to Cut "
     "Production' (SMM Copper Concentrate Spot Weekly Review, "
     "2026-09-18). Added 2026-09-25. Link: https://news.metal.com/newscontent/104123127-imported-copper-concentrate-tcs-continue-to-fall-with-some-smelters-beginning-to-show-willingness-to-cut-production-smm-copper-concentrate-spot-weekly-review"),
    ("2026-09-18", -221.89, "cited",
     "SMM Imported Copper Concentrate Index (weekly), -$221.89/dmt, a "
     "new record low (news.metal.com, same 2026-09-18 SMM Copper "
     "Concentrate Spot Weekly Review as above). Added 2026-09-25. Link: https://news.metal.com/newscontent/104123127-imported-copper-concentrate-tcs-continue-to-fall-with-some-smelters-beginning-to-show-willingness-to-cut-production-smm-copper-concentrate-spot-weekly-review"),
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
     "necessarily durable. Link: https://news.metal.com/newscontent/104133941-cspt-meeting-decides-not-to-set-q4-copper-concentrate-tc-guidance-price-imported-copper-concentrate-trading-activity-declines-smm-copper-concentrate-spot-weekly-review"),
]

# ---------------------------------------------------------------------------
# 2. SMM China Copper-Smelting Sulphuric Acid Index (weekly), RMB/t -- the
#    acid series the source article's "cushion shrinking" claim is built on.
# ---------------------------------------------------------------------------
CU_ACID_WEEKLY_RAW = [
    ("2026-01-02", 919.5, "cited-approx",
     "SMM China Copper Smelting Acid Index, RMB 919.5/t 'at the start of "
     "the year' (news.metal.com, '[SMM Analysis] China's Sulphuric Acid "
     "Production and Sulphur/Sulphuric Acid Imports/Exports in H1 2026'). Link: https://news.metal.com/newscontent/104021425-smm-analysis-chinas-sulphuric-acid-production-and-sulphursulphuric-acid-imports-exports-in-h1-2026"),
    ("2026-02-13", 930.0, "cited-approx",
     "Midpoint placeholder date within the source's stated 'Jan-Feb "
     "moved narrowly in the RMB 900-960/t range' (same H1-2026 SMM "
     "analysis as above) -- no single dated print exists for this week; "
     "930 is the midpoint of the cited range, not a specific print. Link: https://news.metal.com/newscontent/104021425-smm-analysis-chinas-sulphuric-acid-production-and-sulphursulphuric-acid-imports-exports-in-h1-2026"),
    ("2026-03-27", 1235.5, "cited-approx",
     "SMM China Copper Smelting Acid Index 'climbed quickly to RMB "
     "1,235.5/t' in March, following sulphur's Hormuz-driven surge (same "
     "H1-2026 SMM analysis). Dated to end-of-March as the analysis "
     "reports it as the March figure; not a specific dated print. Link: https://news.metal.com/newscontent/104021425-smm-analysis-chinas-sulphuric-acid-production-and-sulphursulphuric-acid-imports-exports-in-h1-2026"),
    ("2026-04-24", 1660.5, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,660.5/t, up RMB "
     "31.5/t WoW (news.metal.com, 'Sulphuric Acid Prices Key to Copper "
     "Smelter Cutbacks'; consistent with the H1-2026 analysis's separate "
     "'rose further to RMB 1,657/t in April'). Link: https://news.metal.com/newscontent/103881993-Sulphuric-Acid-Prices-Key-to-Copper-Smelter-Cutbacks-Amid-Collapsing-TCs"),
    ("2026-05-15", 1665.0, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,665/t (news.metal.com, "
     "'Copper Concentrate TCs Break Through Negative Triple Digits'). The "
     "same article's 'up 83.7% from the start of the year' does not match "
     "this file's start-of-year cited-approx print (919.5 -> 1,665 is +81.1%); "
     "the 1,665 level is kept as the dated print, not the percentage claim."),
    ("2026-06-26", 1751.0, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,751/t -- implied by the 2026-07-03 SMM weekly review (index at RMB 1,789/t, 'up 38 yuan/mt WoW', "
     "news.metal.com). Replaces an earlier cited-approx midpoint placeholder of RMB 1,700/t -- corrected 2026-10-01."),
    ("2026-07-03", 1789.0, "cited",
     "PEAK: SMM China Copper Smelting Acid Index, RMB 1,789/t, up 38 yuan/mt WoW, 'the fourth consecutive weekly rise' (news.metal.com, 'China's Sulphuric "
     "Acid Market Regional Divergence Intensifies, Index Continues to Strengthen', SMM Sulphuric Acid Weekly Review, 2026-07-03). "
     "CORRECTION 2026-10-01: this peak was previously dated 2026-07-10 as a 'representative early-July Friday'. SMM's own consecutive-decline "
     "count (4th decline on 07-31, 9th on 09-04, 12th on 09-24) puts the first decline on 07-10 and therefore the peak on 07-03. Link: https://news.metal.com/en/newscontent/103987041-chinas-sulphuric-acid-market-regional-divergence-intensifies-index-continues-to-strengthen-smm-sulphuric-acid-weekly-rev"),
    ("2026-07-10", 1784.5, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,784.5/t, down 4.5 yuan/mt WoW, 'ending its streak of gains' (SMM Sulphuric Acid Weekly Review, week ended 2026-07-10; also gives SMM Sulphur EXW Shandong weekly average RMB 8,928.5/t). Replaces a grid-fill interpolation (~1,776) -- added 2026-10-01. Link: https://news.metal.com/newscontent/103998631-중국-황산-시장이-고점에-머물며-지역-간-격차가-심화되고-있다-smm-sulfuric-acid-weekly-review"),
    ("2026-07-17", 1763.0, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,763/t 'as of 17 July' "
     "(H1-2026 SMM analysis) -- the first confirmed print of the decline "
     "that reaches 'nine consecutive weeks' by 2026-09-04. Link: https://news.metal.com/newscontent/104021425-smm-analysis-chinas-sulphuric-acid-production-and-sulphursulphuric-acid-imports-exports-in-h1-2026"),
    ("2026-07-24", 1742.0, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,742/t -- implied by the 2026-07-31 SMM weekly review (RMB 1,722.5/t, 'down 19.5 yuan/mt WoW'). "
     "Was a grid-fill interpolation (1,743) until 2026-10-01; the interpolation turned out to be within RMB 1/t of the real print."),
    ("2026-07-31", 1722.5, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,722.5/t, down 19.5 yuan/mt WoW, 'the fourth consecutive week of decline' (news.metal.com, "
     "'China's sulphuric acid market continues to weaken as regional price declines widen...', SMM Sulphuric Acid Weekly Review, 2026-07-31). "
     "Was a grid-fill interpolation (1,723) until 2026-10-01."),
    ("2026-08-07", 1703.0, "cited",
     "Back-calculated from the 2026-08-14 print's own citation ('down "
     "RMB 72/t WoW' from this week) -- see next row. Treated as cited, "
     "not interpolated, since it is implied directly by a dated source, "
     "not smoothed between two distant points. Link: https://news.metal.com/newscontent/104060415-chinas-sulphuric-acid-market-continues-to-hit-bottom-weak-demand-drags-down-the-price-center-smm-sulphuric-acid-weekly-r"),
    ("2026-08-14", 1631.0, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,631/t, down RMB 72/t "
     "WoW, the SIXTH consecutive weekly pullback (news.metal.com, "
     "'China's Sulphuric Acid Market Continues to Hit Bottom'). Link: https://news.metal.com/newscontent/104060415-chinas-sulphuric-acid-market-continues-to-hit-bottom-weak-demand-drags-down-the-price-center-smm-sulphuric-acid-weekly-r"),
    ("2026-08-28", 1583.5, "cited",
     "Back-calculated from the source article's 2026-09-04 figure ('down "
     "44 yuan/t from the previous Friday') -- 1,539.5 + 44 = 1,583.5. Link: https://news.metal.com/newscontent/104098691-china-sulphuric-acid-index-falls-for-nine-consecutive-weeks-with-a-widening-decline-domestic-sulphur-trade-rebounds-from-lows-while-sulphuric-acid-outside-china-stops-falling-and-stabilizes-smm-sulphuric-acid-weekly-review"),
    ("2026-09-04", 1539.5, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,539.5/t, the NINTH "
     "consecutive weekly decline (source article's headline acid "
     "figure). Link: https://news.metal.com/newscontent/104098691-china-sulphuric-acid-index-falls-for-nine-consecutive-weeks-with-a-widening-decline-domestic-sulphur-trade-rebounds-from-lows-while-sulphuric-acid-outside-china-stops-falling-and-stabilizes-smm-sulphuric-acid-weekly-review"),
    ("2026-09-11", 1418.0, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,418.0/t, the TENTH "
     "consecutive weekly decline, down RMB 121.5/t or 7.9% WoW -- "
     "back-calculated from the 2026-09-18 print's own citation of 'the "
     "previous week's drop of 121.5 yuan/mt or 7.9%' (news.metal.com, "
     "SMM China Sulphuric Acid Weekly Review, 2026-09-18). Added "
     "2026-09-25. Link: https://news.metal.com/newscontent/104122023-chinas-sulphuric-acid-weekly-decline-narrowed-significantly-with-shanxi-falling-by-a-further-330-yuanmt-smm-sulphuric-acid-weekly-review"),
    ("2026-09-18", 1351.0, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,351.0/t, down RMB 67/t "
     "or 4.7% from RMB 1,418/t -- the ELEVENTH consecutive weekly "
     "decline, a sharp narrowing from the prior week's 7.9% drop "
     "(news.metal.com, SMM China Sulphuric Acid Weekly Review, "
     "2026-09-18). Added 2026-09-25. Link: https://news.metal.com/newscontent/104122023-chinas-sulphuric-acid-weekly-decline-narrowed-significantly-with-shanxi-falling-by-a-further-330-yuanmt-smm-sulphuric-acid-weekly-review"),
    ("2026-09-24", 1247.5, "cited",
     "SMM China Copper Smelting Acid Index, RMB 1,247.5/t, down RMB "
     "103.5/t or 7.7% from RMB 1,351/t the previous Friday -- the "
     "TWELFTH consecutive weekly decline (news.metal.com, 'CSPT Meeting "
     "Decides Not to Set Q4 Copper Concentrate TC Guidance Price', "
     "2026-09-24 SMM Sulphuric Acid Weekly Review). Dated and "
     "grid-charted exactly as the 2026-09-24 TC print above -- see that "
     "row's note. Added 2026-09-25; most recent print as of this "
     "project's current data-extension pass. Link: https://news.metal.com/newscontent/104133833-waiting-for-policies-and-winter-stockpiling-the-sub-thousand-wave-spreads-to-central-china-smm-sulphuric-acid-weekly-review"),
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
    see the earlier README changelog): `full_index` used to be built as
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
    as current, and this directly contradicted the earlier README's own claim that
    "the interpolation grid updates automatically once new cited anchors
    are added." Fixed by rolling the grid's end up to the next on-cycle
    date whenever df.index.max() isn't already on-cycle, so any cited
    point -- on-cycle or not -- always gets a grid node.

    VINTAGE FIX (2026-09-26, external review feedback -- a real gap in the
    2026-09-25 fix above, though never actually triggered by data this
    file ships): an off-cycle cited date used to be assigned to its
    nearest grid label via `.reindex(full_index, method="nearest",
    tolerance="3D")`. "Nearest" picks whichever side is chronologically
    CLOSER -- which means a citation dated slightly AFTER a grid Friday
    could get snapped BACKWARD onto that EARLIER Friday's label. Example:
    a citation genuinely dated Saturday 2026-09-19 sits 1 day from the
    2026-09-18 grid Friday and 6 days from 2026-09-25 -- "nearest" would
    have displayed it AT 2026-09-18, a date on which that number was not
    yet public. Every citation this file actually ships is dated ON or
    BEFORE its assigned grid Friday (the 2026-09-24 Thursday print is the
    closest case, and it snaps FORWARD to 2026-09-25, which is fine -- a
    grid label may always show OLDER information, never NEWER), so this
    was a property the mechanism failed to GUARANTEE, not a symptom ever
    actually observed. Fixed by replacing "nearest" with `pd.merge_asof(
    ..., direction="backward")`: each grid date is assigned the most
    recent citation dated <= itself (within 3 days), full stop -- never a
    citation dated after it, at any distance. A citation that doesn't
    fall within reach of any grid date under this backward-only rule (as
    the hypothetical Sept-19 one wouldn't, being 6 days from the next
    eligible grid date forward) is not mislabeled "cited" anywhere; it
    still informs the time-interpolated estimate at its true position
    (see below), just without being flagged as if a real print existed
    exactly there.

    Genuine multi-week gaps (no citation within reach on EITHER side --
    e.g. several Fridays between 2026-01-02 and 2026-02-27, where no SMM
    print was cited at all) still fall back to time-interpolation between
    the nearest PAST and FUTURE real citations. This is unaffected by the
    fix above and is NOT a look-ahead problem the way backward-snapping a
    live citation would be: it describes an already-fully-elapsed
    historical window, purely for charting/trend continuity -- nothing in
    this project treats an interior grid row as a live, real-time
    decision point (only `weekly.iloc[-1]`, always the single most
    current row, is used that way, and it is always genuinely "cited" --
    see the self-check below). Using both neighbors to smooth a CLOSED
    gap is standard practice for retrospective series construction; using
    a not-yet-elapsed future value to describe a live "as of today" edge
    reading is the actual violation, and that's what's fixed here.

    The true reported date always stays visible in the raw
    (non-interpolated) `note` field and in `cu_tc_weekly()` /
    `cu_acid_weekly()`, which are untouched by this grid-snapping."""
    grid_end = pd.date_range(start=df.index.max(), periods=1, freq=freq)[0]
    full_index = pd.date_range(df.index.min(), grid_end, freq=freq)
    combined_index = df.index.union(full_index).sort_values()

    # Time-interpolated estimate across the full union of raw + grid
    # dates -- used ONLY as a fallback for grid dates with no citation
    # within reach on the backward-asof pass below (a genuine multi-week
    # gap), never to override an actual citation.
    smoothed = df[[value_col]].reindex(combined_index)
    smoothed[value_col] = smoothed[value_col].interpolate(method="time")
    smoothed_on_grid = smoothed.reindex(full_index)[value_col]

    # Backward-asof alignment: each grid date gets the most recent
    # citation dated <= itself, within 3 days -- never a later one, at
    # any distance. This is what actually decides whether a grid row is
    # labeled "cited" (a real, dated citation genuinely covers it) or
    # falls through to the smoothed estimate above ("interpolated
    # (grid-fill)").
    raw_sorted = df.reset_index().rename(columns={df.index.names[0] or "index": "obs_date"})
    grid_frame = pd.DataFrame({"grid_date": full_index})
    asof = pd.merge_asof(
        grid_frame, raw_sorted.sort_values("obs_date"),
        left_on="grid_date", right_on="obs_date",
        direction="backward", tolerance=pd.Timedelta("3D"),
    ).set_index("grid_date")

    out = pd.DataFrame(index=full_index)
    out[value_col] = asof[value_col]
    out["status"] = asof["status"]
    still_missing = out[value_col].isna()
    out.loc[still_missing, value_col] = smoothed_on_grid[still_missing]
    out["status"] = out["status"].fillna("interpolated (grid-fill)")
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


def _selfcheck_no_future_observation_leaks_backward():
    """Regression test for the 2026-09-26 vintage fix: a citation dated
    AFTER a grid label must never be displayed AT that (earlier) label,
    even if it is chronologically closer to that label than to its own
    correct one. This never happened with data this file actually ships
    (every real citation is dated on/before its assigned grid Friday) --
    this test constructs the case synthetically, on purpose, because the
    old `nearest`-based mechanism had no structural guarantee against it."""
    raw = [
        ("2026-08-14", 100.0, "cited", "x"),
        ("2026-08-28", 90.0, "cited", "x"),
        ("2026-09-04", 80.0, "cited", "x"),
        ("2026-09-18", 70.0, "cited", "x"),
        # Saturday, 1 calendar day after the 2026-09-18 grid Friday, but
        # dated STRICTLY AFTER it -- under the old "nearest" mechanism
        # this would have been closer to 2026-09-18 (1 day) than to
        # 2026-09-25 (6 days) and would have been displayed there.
        ("2026-09-19", 999.0, "cited", "synthetic future-dated point"),
    ]
    df = _weekly_frame(raw, "v")
    grid = _interpolate_to_grid(df, "v")
    assert grid.loc[pd.Timestamp("2026-09-18"), "v"] != 999.0, (
        "vintage bug reintroduced: a citation dated 2026-09-19 leaked "
        "backward onto the earlier 2026-09-18 grid label")
    assert grid.loc[pd.Timestamp("2026-09-18"), "status"] == "cited", (
        "2026-09-18's own genuine citation (70.0) was overwritten")
    assert grid.loc[pd.Timestamp("2026-09-18"), "v"] == 70.0


def _selfcheck_vintage_alignment_model_b():
    """Regression test: model_b's acid_price_source comparison must draw
    cu_price/tc_usd_dmt/silver_price/acid_usd_t for ALL THREE sources from
    the exact same row (same date) -- never a mix of today's China-domestic
    reading against a stale regional-benchmark date under a mismatched TC.
    See model_b.py's run_model_b_acid_robustness docstring for the bug
    this guards against."""
    import model_a as ma
    import model_b as mb

    out_a = ma.run_model_a_copper_acid_cushion()
    out_b = mb.run_model_b_acid_robustness(
        out_a["weekly"], out_a["params"], out_a["energy_price_usd_mwh"]
    )
    ref_date = out_b["acid_price_source_reference_date"]
    weekly = out_a["weekly"]
    reference_row = weekly.loc[pd.Timestamp(ref_date)]
    china_row = out_b["acid_price_source"].loc[
        out_b["acid_price_source"]["acid_price_source"] == "smm_china_domestic"
        ]
    if china_row.empty:
        china_row = out_b["acid_price_source"].iloc[[0]]
    # The china-domestic acid price fed into this comparison must be the
    # value AT ref_date, not at weekly's own true latest date, whenever
    # the two differ (exactly the scenario the 2026-09-25 fix addresses).
    assert abs(china_row["acid_price_usd_t"].iloc[0] - reference_row["acid_usd_t"]) < 1e-6, (
        "model_b's acid_price_source comparison is not pinned to the "
        "regional benchmark's own reference date -- vintage bug reintroduced")


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
#    for every quarter 2023-2026 in real_data_check.py; see the earlier README's
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


_FX_WARNED: set = set()


def usd_cny_for_quarter(quarter_label: str) -> float:
    """CNY per USD for a quarter label like '2026-Q3'. Falls back to the nearest
    quarter in USD_CNY_QUARTERLY (with ONE printed warning per missing quarter)
    rather than crashing or silently defaulting to a flat rate. Single source of
    truth: cny_to_usd() and strategy_layer.fx_for() both use it, so the monitor and
    the strategy layer can never disagree on the rate (they used to: the strategy
    layer raised KeyError on any Q4-2026 date)."""
    if quarter_label in USD_CNY_QUARTERLY:
        return USD_CNY_QUARTERLY[quarter_label]
    keys = sorted(USD_CNY_QUARTERLY)
    target_ord = pd.Period(quarter_label, "Q").ordinal
    nearest = min(keys, key=lambda k: abs(pd.Period(k, "Q").ordinal - target_ord))
    rate = USD_CNY_QUARTERLY[nearest]
    if quarter_label not in _FX_WARNED:
        _FX_WARNED.add(quarter_label)
        print(f"WARNING: no USD/CNY rate for {quarter_label}; using nearest ({nearest} = {rate}).")
    return rate


def usd_cny_for_date(date) -> float:
    """usd_cny_for_quarter() keyed by an actual date."""
    p = pd.Period(pd.Timestamp(date), "Q")
    return usd_cny_for_quarter(f"{p.year}-Q{p.quarter}")


def cny_to_usd(value_cny: float, quarter_label: str) -> float:
    """Period-matched CNY->USD conversion using USD_CNY_QUARTERLY (see usd_cny_for_quarter)."""
    rate = usd_cny_for_quarter(quarter_label)
    # Do not round here: rounding USD/t to 1 decimal leaked into the weekly acid series, so the regime map
    # (unrounded CNY/FX formula) and the monitor (rounded) disagreed at the 2e-3 level and the FX attribution
    # picked up a spurious residual. Round only at display time.
    return value_cny / rate


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
        "realized_acid_price_usd_t": 467.0,  # Ivanhoe Q1 release (2026-05-06): 107,700 t sold to six offtakers at an average realized price of $467/t. (Earlier versions of this file said no Q1 realized price was disclosed -- that was wrong; corrected 2026-10-01.)
        "acid_cushion_ratio": round(0.32 / 0.27, 4),   # 118.5% -- acid MORE than covered smelter opex in Q1
        "smelter_utilisation_pct": 60,
        "note": "Ivanhoe Mines Q1 2026 results (2026-05-06 release). Smelter has run at "
                "~60% of capacity since mid-February, having produced first anodes "
                "in late Q4 2025. Per the Q2 release, Q1 smelter opex ($0.27/lb) was "
                "understated by the PARTIAL CAPITALISATION of smelter operating costs "
                "in Q1 -- so Q1's 118.5% coverage is flattered by accounting.",
    },
    "2026-Q2": {
        "smelter_opex_usd_lb": 0.41,
        "acid_credit_usd_lb": 0.39,
        "logistics_usd_lb": 0.24,
        "acid_production_kt": 112.307,
        "realized_acid_price_usd_t": 465.0,
        "contract_price_usd_t": 840.0,     # July/August contracts, "~80% higher" than the Q2 realized average
        "acid_cushion_ratio": round(0.39 / 0.41, 4),   # 95.1% -- acid almost, not quite, covered smelter opex in Q2
        "note": "Ivanhoe Mines Q2 2026 results (2026-07-29 release); this is also "
                "the exact figure the source article cites for Kamoa-Kakula. "
                "Realised acid price was UNCHANGED q/q ($467 -> $465/t; the "
                "release says so explicitly). Smelter opex per lb rose $0.27 -> "
                "$0.41 because, per the release, Q1 opex was understated by the "
                "partial capitalisation of smelter operating costs in Q1 -- not "
                "because of ramp-up (utilisation was ~60% in both quarters) and "
                "not because of acid prices. Acid credit per lb rose $0.32 -> $0.39 "
                "(+22%: more acid sold per lb of copper produced, price flat). "
                "So the Q1->Q2 coverage dip (118.5% -> 95.1%) is an accounting/"
                "volume effect and says nothing about the acid price; see "
                "KAMOA_FORWARD_INDICATION and strategy_layer.kamoa_bridge().",
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
# 4b. Kamoa-Kakula forward indication (added 2026-10-01). Management said on
#     the Q2 earnings call (2026-07-30) that at contract prices the acid
#     by-product credit "could approach $0.60 per pound in the third quarter,
#     compared with $0.38 per pound in the second quarter". Source is a
#     MarketBeat summary of the call (secondary; not re-checked against the
#     transcript) -- the Q2 RELEASE itself (Ivanhoe, 2026-07-29) only discloses
#     the $0.39/lb Q2 credit, the $465/t Q2 realized price ("unchanged
#     quarter-on-quarter") and the ~$840/t Jul/Aug contract level (+80%).
#     This matters analytically: it means Kamoa's acid/opex coverage is
#     expected to WIDEN in Q3 (ex-China price up ~80% q/q) while China's
#     domestic cushion shrinks -- a regional divergence, not a global
#     "shrinking cushion".
# ---------------------------------------------------------------------------
KAMOA_FORWARD_INDICATION = {
    "q3_acid_credit_usd_lb_mgmt": 0.60,
    "q2_acid_credit_usd_lb_mgmt_quote": 0.38,    # management's spoken figure; the release says 0.39 -- immaterial
    "q2_acid_sold_t": 119603,                   # Ivanhoe Q2 release
    "q2_smelter_utilisation_pct": 60,           # Q2 release: ~60% of capacity since mid-February; further ramp-up constrained by concentrate feed
    "source": "Ivanhoe Mines Q2 2026 results release (2026-07-29); Q2 earnings call 2026-07-30 (MarketBeat summary, 2026-08-01 -- secondary; the $0.60/lb figure is NOT in the release text)",
    "status": "management indication, not a reported result; Q3 results expected late Oct/Nov 2026",
}

# ---------------------------------------------------------------------------
# 4c. Acid quote-basis facts (added 2026-10-01; VAT rule restated 2026-10-03
#     so that this comment matches the code).
#     * SMM's provincial USD acid series state "USD price is exclusive of 13%
#       VAT". The national RMB index (SMM-CU-SA-001) is treated on the same
#       convention: the HEADLINE model deducts 13% VAT
#       (acid_usd_t = acid_cny_t / 1.13 / USD_CNY). The national RMB page itself
#       was not retrieved, so a VAT-inclusive RMB quote is INFERRED from SMM's
#       convention. The as-quoted (VAT-in) figure is kept as a sensitivity, not
#       as the headline. (An earlier version of this comment said VAT was "NOT
#       silently applied" -- that described a pre-headline-change draft.)
#     * SMM's own convention: RC is 10% of TC (RC in cents/lb = TC in $/dmt /
#       10) -- "In international practice, the value of RC is fixed at 10% of
#       the TC value" (SMM, 'Launch of SMM Copper Concentrate Index' notice).
#       The project's TC-only drag therefore omits roughly a further ~54% of
#       the treatment-charge drag (RC, per dmt of concentrate) at the current
#       grade/payable assumptions.
# ---------------------------------------------------------------------------
ACID_QUOTE_BASIS = {
    "vat_rate_cn": 0.13,
    # SMM's own convention (checked 2026-10-02 on metal.com price pages): the ORIGINAL RMB price includes 13% VAT and
    # the USD series is derived by deducting it -- e.g. Inner Mongolia EXW: original CNY 785/t = USD 111.19 VAT-included
    # = USD 98.40 VAT-excluded; SMM-CU-SA-001 (the national index, USD page): "13% VAT deducted for USD pricing".
    # The national index's RMB page itself was not retrieved, so VAT-inclusive RMB is INFERRED from that convention.
    "smm_usd_series_vat": "exclusive of 13% VAT (SMM price pages: 'VAT Rate: 13% VAT deducted for USD pricing')",
    "national_cny_index_vat_basis": "VAT-INCLUSIVE (inferred from SMM's convention; direct RMB page not retrieved)",
    "model_headline_basis": "ex-VAT: acid_usd_t = acid_cny_t / 1.13 / USD_CNY (VAT is passed to the tax authority, not smelter revenue)",
    "rc_to_tc_convention": 0.10,
}

# Sulphur (acid feedstock) -- SMM Sulphur EXW Shandong, RMB/t, cited weekly
# averages found in SMM's own acid weekly reviews (2026-07-03, 2026-07-31).
# Used ONLY for a dated feedstock-parity indicator (see strategy_layer); not
# refreshed since 2026-07-31 -- flagged stale in every output that uses it.
SULPHUR_EXW_SHANDONG_RMB_T = [
    ("2026-07-03", 9150.0, "cited", "SMM Sulphuric Acid Weekly Review 2026-07-03: range 9,000-9,300, avg 9,150 (+~950 WoW); Kazakhstan suspended sulphur exports from 2026-06-27, Russia's export ban extended to end-2026."),
    ("2026-07-10", 8928.5, "cited", "SMM Sulphuric Acid Weekly Review, week ended 2026-07-10 (already quoted in the 2026-07-10 acid row): SMM Sulphur EXW Shandong weekly average RMB 8,928.5/t. Missing from this series until 2026-10-03."),
    ("2026-07-31", 9103.5, "cited", "SMM Sulphuric Acid Weekly Review 2026-07-31: range 8,957-9,250, avg 9,103.5 (-350 WoW)."),
]
T_SULPHUR_PER_T_98_ACID = round(0.98 * 32.06 / 98.08, 4)   # stoichiometry: S + 1.5 O2 + H2O -> H2SO4 ; 0.3203 t S per t of 98% acid


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
    _selfcheck_no_future_observation_leaks_backward()
    _selfcheck_vintage_alignment_model_b()
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