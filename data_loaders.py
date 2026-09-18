"""
data_loaders.py
================
This project does NOT fetch data automatically -- your sandbox / bash tool
has no network access to LME, World Bank, USGS, ILZSG, ICSG etc, and several
of these sources gate their fullest data behind manual downloads or
subscriptions anyway (see the feasibility table in the research note).

Instead, each loader below defines the EXACT schema it expects, so you can:
  1. download the raw file yourself from the source listed,
  2. save it under ./data/<name>.csv,
  3. call the loader, which validates columns and returns a tidy DataFrame
     indexed by date.

Sources & what to actually download
------------------------------------
World Bank Pink Sheet   -> "CMO-Historical-Data-Monthly.xlsx" from
                            worldbank.org/en/research/commodity-markets
                            (free, no login). Columns needed: Zinc, Copper
                            (both $/mt), Silver ($/troy oz).
FRED zinc (PZINCUSDM)   -> fred.stlouisfed.org/series/PZINCUSDM (free, no
(recommended zinc        login). IMF "Global price of Zinc" benchmark,
 price source)            monthly, USD/tonne -- verified real and current.
                            Replaces an earlier attempt to pull zinc from
                            COMEX via yfinance (ZNC=F), which a real local
                            pull showed was frozen at one settlement price
                            for 93% of a 2023-2026 sample; see
                            load_fred_zinc and STRATEGY_NOTE.md.
USGS MCS data releases   -> data.usgs.gov, "Copper"/"Zinc" commodity data
                            release (CC0, free). Annual mine/refined
                            production by country.
ILZSG free-access data   -> ilzsg.org/free-access-data (free). LME/SHFE
                            zinc stocks & prices, some production charts.
ICSG selected statistics -> icsg.org/selected-copper-statistics (free
                            summary tables; full monthly database is
                            subscription).
China sulfuric acid      -> no single free official series. Use SMM /
(regional proxy)            Hangzhou Harmony public articles for regional
                            spot quotes, OR the China Customs HS 2807
                            export unit-value proxy (export value / export
                            volume) as a robustness alternative -- see
                            `acid_price_from_trade_proxy` below.
LME reference prices     -> lme.com day-delayed prices (free, limited
                            history) or World Bank Pink Sheet as the
                            long-history anchor.
Copper/silver, daily      -> fetch_metal_prices_yfinance.py, run locally
(yfinance, optional)         (HG=F, SI=F -- both verified reliable on a
                              real pull). Zinc was removed from that
                              script for the reason above; use
                              load_fred_zinc instead.

If you don't have a file yet, every loader also accepts `path=None` and
will raise a clear FileNotFoundError telling you what to fetch -- this is
intentional, so Model A/B/C fail loudly rather than silently running on
placeholder numbers.

NOTE (2026-09-15 review): the single-day jump/outlier check that used to
live only in fetch_metal_prices_yfinance.py (_warn_if_large_jump) is
deliberately NOT duplicated here. It belongs at fetch time, once, on the
raw pull -- duplicating similar-but-not-identical staleness/outlier logic
in two places is exactly how the two copies of fetch_metal_prices_yfinance.py
drifted apart in the first place (see README.md's changelog). This module
keeps its own, different check (the per-cell flat/stale guard in
load_real_metal_prices_quarterly below), which is a second, independent
line of defense against a different failure mode (a frozen quarterly
average), not a copy of the first.
"""

from __future__ import annotations

import os
import pandas as pd


class MissingDataError(FileNotFoundError):
    pass


def _require(path: str, hint: str):
    if path is None or not os.path.exists(path):
        raise MissingDataError(
            f"Expected a data file at '{path}'. {hint}"
        )


def load_generic_price_csv(path: str, value_col: str, date_col: str = "date") -> pd.Series:
    """
    Generic loader for any two-column (date, value) CSV -- the common
    denominator format for LME day-delayed exports, World Bank Pink Sheet
    (after you slice one column out), SMM spot-price articles you've
    transcribed, etc.
    """
    _require(path, f"Provide a CSV with columns ['{date_col}', '{value_col}'].")
    df = pd.read_csv(path)
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col).sort_index()
    return df[value_col].rename(value_col)


def load_worldbank_pink_sheet(path: str) -> pd.DataFrame:
    """
    Expects a CSV you've exported/cleaned from the World Bank "Pink Sheet"
    monthly workbook, with columns:
        date, zinc_usd_t, copper_usd_t, silver_usd_toz
    (rename the raw workbook's columns to these before loading -- the raw
    file has a multi-row header and needs a one-off cleanup pass in Excel
    or pandas.read_excel(skiprows=...)).
    """
    _require(path, "Export & clean the World Bank Pink Sheet monthly workbook "
                    "to columns [date, zinc_usd_t, copper_usd_t, silver_usd_toz].")
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    expected = {"zinc_usd_t", "copper_usd_t", "silver_usd_toz"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Pink Sheet CSV missing columns: {missing}")
    return df


def load_usgs_production(path: str, metal: str) -> pd.DataFrame:
    """
    Expects a CSV from a USGS MCS data release, columns:
        year, country, mine_production_kt, refined_production_kt
    `metal` is just used to tag the output (not validated against content).
    """
    _require(path, f"Download the USGS MCS '{metal}' data release from data.usgs.gov "
                     "and map its columns to [year, country, mine_production_kt, refined_production_kt].")
    df = pd.read_csv(path)
    df["metal"] = metal
    return df


def load_ilzsg_free_access(path: str) -> pd.DataFrame:
    """
    Expects a CSV transcribed/exported from ilzsg.org/free-access-data,
    columns:
        date, zinc_lme_price, zinc_shfe_price, zinc_lme_stocks
    """
    _require(path, "Export the ILZSG free-access LME/SHFE zinc stocks & price "
                    "series to columns [date, zinc_lme_price, zinc_shfe_price, zinc_lme_stocks].")
    return pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()


def load_icsg_selected_statistics(path: str) -> pd.DataFrame:
    """
    Expects a CSV transcribed from icsg.org/selected-copper-statistics,
    columns:
        date, copper_mine_production_kt, copper_refined_production_kt,
        copper_stocks_kt
    """
    _require(path, "Transcribe ICSG's selected copper statistics tables to "
                    "columns [date, copper_mine_production_kt, copper_refined_production_kt, copper_stocks_kt].")
    return pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()


def load_company_filing_byproducts(path: str, company: str) -> pd.DataFrame:
    """
    Expects a hand-built CSV of disclosed by-product figures pulled
    directly from filings (Nexa 20-F/6-K, Freeport 10-K), columns:
        period, concentrate_processed_kt, sulfuric_acid_production_kt,
        sulfuric_acid_sales_kt, silver_sales_koz, tc_benchmark_usd_t,
        tc_spot_usd_t
    Optional (used by smelter_calibration.py): refined_metal_kt (copper),
        conversion_cost_usd_t, energy_mwh_per_t, premium_usd_t,
        gold_yield_oz_per_t_conc
    This is the calibration source for SmelterParams.acid_yield,
    silver_yield_oz, etc -- e.g. acid_yield ~= sulfuric_acid_production_kt
    / concentrate_processed_kt.
    """
    _require(path, f"Build a CSV of {company}'s disclosed by-product figures with columns "
                    "[period, concentrate_processed_kt, sulfuric_acid_production_kt, "
                    "sulfuric_acid_sales_kt, silver_sales_koz, tc_benchmark_usd_t, tc_spot_usd_t].")
    df = pd.read_csv(path)
    df["company"] = company
    return df


def acid_price_from_trade_proxy(export_value: pd.Series, export_volume_t: pd.Series) -> pd.Series:
    """
    China Customs HS 2807 (sulfuric acid / oleum) export unit-value proxy:
        UnitValue_t = ExportValue_t / ExportVolume_t
    This is NOT the same as the domestic spot price (export mix and export
    tax rebates distort it), but it's a legitimate free robustness check
    per section 16 of the research note -- use it in Model B, not Model A.
    """
    proxy = (export_value / export_volume_t).rename("acid_export_unit_value")
    return proxy


def load_regional_acid_prices(path: str) -> pd.DataFrame:
    """
    Expects a wide CSV of regional Chinese sulfuric-acid spot quotes
    (transcribed from SMM / Hangzhou Harmony public articles), columns:
        date, guangxi, fujian, jiangsu, shandong, hubei, guizhou, henan, yunnan
    (include whichever regions you actually have -- missing columns are fine).
    """
    _require(path, "Transcribe regional 98% smelter-grade sulfuric acid spot "
                    "quotes into columns [date, <region_1>, <region_2>, ...].")
    return pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()


def load_fred_monthly_csv(path: str, date_col: str, value_col: str, output_name: str) -> pd.Series:
    """
    Generic loader for a FRED-exported monthly series CSV (the standard
    "Download" button format on any fred.stlouisfed.org series page, or
    the equivalent fredgraph.csv export -- both use a DATE column plus one
    value column named after the series ID). No API key needed for a
    single-series CSV download.

    Expected columns: [date_col, value_col].
    """
    _require(path, f"Provide a FRED CSV with columns ['{date_col}', '{value_col}'].")
    df = pd.read_csv(path)
    if date_col not in df.columns or value_col not in df.columns:
        raise ValueError(f"FRED CSV must contain ['{date_col}', '{value_col}']. Found: {list(df.columns)}")
    df[date_col] = pd.to_datetime(df[date_col])
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    return df.set_index(date_col).sort_index()[value_col].rename(output_name).dropna()


def load_fred_zinc(path: str) -> pd.Series:
    """
    IMF "Global price of Zinc" via FRED, series PZINCUSDM -- verified real
    (fred.stlouisfed.org/series/PZINCUSDM): monthly, USD per metric tonne,
    IMF benchmark price, history back to 2003.

    Download: fred.stlouisfed.org/series/PZINCUSDM -> Download -> CSV, or
    `python scripts/download_fred_zinc.py`. FRED exports use either
    ``DATE`` (manual download) or ``observation_date`` (fredgraph.csv).
    """
    df = pd.read_csv(path)
    date_col = "DATE" if "DATE" in df.columns else "observation_date"
    if date_col not in df.columns:
        raise ValueError(f"FRED zinc CSV needs DATE or observation_date; found {list(df.columns)}")
    return load_fred_monthly_csv(path, date_col=date_col, value_col="PZINCUSDM", output_name="zn_price")


def load_daily_metal_prices(path: str = "data/metal_prices.csv") -> pd.DataFrame:
    """
    Reads the RAW daily cu_price/silver_price CSV produced by
    fetch_metal_prices_yfinance.py (run locally), WITHOUT collapsing it to
    a quarterly average -- unlike load_real_metal_prices_quarterly above,
    which exists specifically for real_data_check.py's quarterly zinc/
    copper table. The copper acid-cushion pipeline (model_a.
    run_model_a_copper_acid_cushion) needs a WEEKLY-cadence price to match
    the SMM TC/acid series in copper_acid_data.py, so it reindexes this
    daily series itself rather than going through a quarterly aggregator.

    Returns an empty DataFrame (not an error) if `path` doesn't exist,
    same convention as load_real_metal_prices_quarterly, so callers can
    check `.empty` and raise a clear, specific error instead of a bare
    KeyError three functions later.
    """
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()


def aggregate_monthly_to_quarterly(series: pd.Series, quarter_labels) -> pd.Series:
    """
    Collapses an already-loaded monthly (or any sub-quarterly) series to a
    quarterly mean for each label in `quarter_labels` (e.g. "2024-Q1"),
    matching real_data_check.REAL_DATA's index. Deliberately separate from
    load_real_metal_prices_quarterly: that function reads a CSV AND
    aggregates AND applies a flat/stale-window guard, because daily
    futures data can go stale from a lack of trading. A monthly IMF/FRED
    benchmark doesn't have that failure mode -- every month is already one
    considered value, not a possibly-untraded settlement print -- so no
    staleness guard is applied here; genuinely flat prices across months
    would reflect the real market, not a data artefact.
    """
    rows = {}
    for label in quarter_labels:
        period = pd.Period(label, freq="Q")
        window = series.loc[str(period.start_time.date()):str(period.end_time.date())]
        if not window.empty:
            rows[label] = window.mean()
    return pd.Series(rows, name=series.name)


def load_real_metal_prices_quarterly(path: str, quarter_labels, stale_share_threshold: float = 0.5) -> pd.DataFrame:
    """
    Reads the daily zn_price/cu_price/silver_price CSV produced by
    `fetch_metal_prices_yfinance.py` (run locally -- see that script's
    docstring for why it can't run inside this sandbox) and collapses it
    to a quarterly average for each label in `quarter_labels` (e.g.
    "2024-Q1"), matching `real_data_check.REAL_DATA`'s index so it can be
    dropped straight in. Returns an empty DataFrame (not an error) if
    `path` doesn't exist yet, so callers can check `.empty` and fall back
    to the illustrative round-number prices without a crash -- the file
    only exists once you've actually run the fetch script locally.

    PER-CELL STALENESS GUARD, added after a real local pull surfaced the
    problem directly: COMEX zinc (`ZNC=F`) turned out to be frozen at a
    single settlement price (2297.0) for 93% of a real 2023-2026 pull --
    5 of 6 quarters this project actually uses had EXACTLY ONE unique
    zn_price value for the entire quarter (verified: `nunique() == 1` on
    every quarter except the one containing the first real trade in
    mid-2026). Averaging a flat window doesn't fix that -- it just hands
    back the same flat number dressed up as a "real quarterly average,"
    which is worse than the clearly-labelled invented round number it
    would silently replace. So: for each (quarter, column), if the most
    common single value accounts for more than `stale_share_threshold` of
    that quarter's observations, that cell is returned as NaN instead of
    an average -- letting the caller's real_data_check.py-style overlay
    logic skip it and keep the invented fallback for that cell specifically,
    while still upgrading any column/quarter that has genuine variation
    (this project's real cu_price/silver_price pulls did, throughout).

    NOTE this guard catches a FROZEN price, not a single large one-day
    JUMP (e.g. a real event or a contract-roll splice) -- that is a
    different failure mode, checked once at fetch time by
    fetch_metal_prices_yfinance.py's _warn_if_large_jump, not here. See
    that module and STRATEGY_NOTE.md's correction note for two real,
    verified examples (the 2025-07-30 COMEX copper tariff-exemption
    collapse and the 2026-01-30 silver crash) that this guard is not
    meant to catch, and should not catch -- both are real market moves.
    """
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    rows = {}
    for label in quarter_labels:
        period = pd.Period(label, freq="Q")
        window = df.loc[str(period.start_time.date()):str(period.end_time.date())]
        if window.empty:
            continue
        row = {}
        for col in window.select_dtypes("number").columns:
            series = window[col].dropna()
            if series.empty:
                continue
            most_common_share = series.value_counts(normalize=True).iloc[0]
            if most_common_share > stale_share_threshold:
                row[col] = float("nan")  # flat/stale window -- don't average a frozen price
            else:
                row[col] = series.mean()
        rows[label] = row
    return pd.DataFrame(rows).T
