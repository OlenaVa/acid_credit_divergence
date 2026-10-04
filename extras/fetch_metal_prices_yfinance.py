"""
fetch_metal_prices_yfinance.py
================================
RUN THIS ON YOUR OWN MACHINE, NOT IN A NETWORK-RESTRICTED SANDBOX.
This project's execution environment cannot reach finance.yahoo.com (only
package registries are reachable there) -- confirmed with a real attempted
pull, not assumed: `HTTP Error 403: Host not in allowlist:
query1/query2.finance.yahoo.com`. Run this locally instead.

REVIEW NOTE (2026-09-15): this project had TWO copies of this file -- this
one (inside acid_credit_divergence/, with the history and safety checks
below) and a second, simplified copy sitting at the project root (missing
_warn_if_flat_or_stale entirely). That is the ONLY copy that should exist
now -- delete the root-level duplicate. See the earlier README's changelog for the
full account of why this matters: whichever copy actually gets run is the
one that determines whether data/metal_prices.csv was quality-checked at
all, and the simplified root copy had no checks running.

Copper and silver only -- zinc was REMOVED from this script (2025-09)
after a real local pull proved COMEX zinc unusable, and a better free
source was found. Worth recording plainly rather than quietly patching,
the same way arbitragebot's README documents its own bugs-found-and-fixed:

  1. `ZN=F` is NOT zinc -- it's the CBOT 10-Year Treasury Note futures
     contract. Using it fed a bond price into every zinc calculation.
     First fix: switched to `ZNC=F`, COMEX's actual "Special High Grade
     Zinc" contract.
  2. That fix was insufficient. A real local pull of `ZNC=F` came back
     frozen at a single settlement price (2297.0) for 93% of a
     2023-2026 sample -- 5 of 6 quarters this project uses had exactly
     ONE unique zn_price value for the entire quarter. COMEX zinc is
     essentially untraded; averaging a frozen price and calling it "real"
     is worse than an honestly-labelled invented number.
  3. Final fix: zinc now comes from FRED's PZINCUSDM (IMF "Global price
     of Zinc", monthly, verified real, no unit conversion needed) via
     `data_loaders.load_fred_zinc` -- a genuine benchmark series, not a
     thin futures print. See `real_data_check.py` and the earlier strategy note.
     This script no longer fetches zinc at all, to avoid two competing
     "sources of truth" for the same variable.

  Separately, `HG=F` (COMEX copper) is quoted in USD per POUND, not USD
  per tonne -- this project's SmelterParams/margin_model expect USD/tonne
  throughout. Fixed: multiplied by 2204.62 (lb per tonne) below.
  `SI=F` (COMEX silver) was already correct -- quoted in USD/troy oz,
  which is what silver_price means everywhere else in this project.
  Both verified reliable (continuously varying, no flat/stale runs) on a
  real local pull -- unlike zinc, copper and silver are safe to automate
  this way.

  4. (2026-09-15) `HG=F` is a US EXCHANGE price, and for several months in
     2025 it diverged sharply from LME copper -- up to a ~28-30% premium
     -- due to a US Section 232 tariff-arbitrage episode, unwinding in a
     record ~20-22% single-session collapse around 2025-07-30 when refined
     copper was excluded from the tariff. That move is REAL (verified
     against contemporaneous reporting, not a data artifact), but it is a
     US-exchange-specific policy distortion, not a reflection of the
     global/Chinese smelter economics this project's thesis is about. If
     you see a huge single-day move flagged by _warn_if_large_jump below
     around that date, that's why -- decide deliberately (LME splice,
     footnote, or exclude the window) rather than averaging through it
     unexamined. Silver has an analogous, unrelated episode around
     2026-01-29/30 (a historic melt-up to an all-time high near $121/oz
     followed by a ~30%+ one-day crash, driven by Fed-nomination news and
     forced liquidations -- again real, again unrelated to smelter
     byproduct economics). See the earlier strategy note's correction note.

Sulfuric acid and TC are NOT available via any free API -- nothing here
fetches those; keep using data_loaders.load_regional_acid_prices and
data_loaders.load_company_filing_byproducts for those two, built from
manually-transcribed public figures. Zinc price: use
data_loaders.load_fred_zinc instead of this script -- see above.

Usage (locally, with network access):
    pip install yfinance pandas
    python extras/fetch_metal_prices_yfinance.py --start 2023-01-01 --out data/metal_prices.csv
"""

import argparse
import sys

LB_PER_TONNE = 2204.62


def _warn_if_flat_or_stale(series, ticker, col):
    """A stale/untraded futures series shows up as long runs of an
    identical value. Flag it loudly instead of letting a flat series pass
    silently into margin calculations that then produce nonsense -- this
    is exactly how the ZNC=F problem above was confirmed: it fires on
    2297.0 repeating for 93% of a real pull. Kept here for copper/silver
    too, as a general safety net, even though neither has shown this
    problem on a real pull so far."""
    if series.empty:
        return
    most_common_share = series.value_counts(normalize=True).iloc[0]
    if most_common_share > 0.30:
        print(
            f"WARNING: {ticker} ({col}) -- {most_common_share:.0%} of values are "
            f"identical. This looks like a thin/stale series, not a real daily "
            f"market. Verify before trusting it.",
            file=sys.stderr,
        )


def _warn_if_large_jump(series, ticker, col, threshold=0.15):
    """Added 2026-09-15. A single-day move this large is unusual for a
    base/precious metal and deserves a human sanity-check before it feeds
    a smelter-margin calculation -- it can be a genuine event (see the two
    documented, verified examples in the module docstring above: the
    ~20-22% COMEX copper collapse on 2025-07-30, and the ~30%+ silver
    crash on 2026-01-30) or a data artifact (an un-adjusted futures
    contract-roll splice, a bad print). This check deliberately does NOT
    try to tell those apart -- like _warn_if_flat_or_stale above, it just
    surfaces the day so a human decides, rather than silently trusting it
    either way."""
    if series.empty:
        return
    pct_change = series.pct_change().abs()
    big_moves = pct_change[pct_change > threshold].dropna()
    for date, move in big_moves.items():
        print(
            f"WARNING: {ticker} ({col}) moved {move:.1%} on {date.date()} -- "
            f"verify this is a real, expected market move (news / contract-roll "
            f"check) before trusting it in a smelter-margin calculation.",
            file=sys.stderr,
        )


def main():
    import os
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # default --out data/metal_prices.csv is relative to the repo root
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default=None, help="defaults to today")
    parser.add_argument("--out", default="data/metal_prices.csv")
    args = parser.parse_args()

    try:
        import yfinance as yf
        import pandas as pd
    except ImportError:
        print("Run this locally with: pip install yfinance pandas", file=sys.stderr)
        sys.exit(1)

    tickers = {"HG=F": "cu_price", "SI=F": "silver_price"}
    frames = {}
    for ticker, col in tickers.items():
        df = yf.download(ticker, start=args.start, end=args.end, auto_adjust=False, progress=False)
        if df.empty:
            print(f"WARNING: no data returned for {ticker} -- check the ticker is still valid on Yahoo.",
                  file=sys.stderr)
            continue
        close = df["Close"]
        # yfinance sometimes returns MultiIndex columns (PriceType, Ticker)
        # even for a single ticker, depending on version -- squeeze to a
        # plain Series either way so this doesn't silently misbehave.
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close = close.rename(col)

        if ticker == "HG=F":
            close = close * LB_PER_TONNE  # USD/lb -> USD/tonne

        _warn_if_flat_or_stale(close, ticker, col)
        _warn_if_large_jump(close, ticker, col)
        frames[col] = close

    if not frames:
        print("No data fetched for any ticker -- nothing written.", file=sys.stderr)
        sys.exit(1)

    out = pd.DataFrame(frames)
    out.index.name = "date"
    out.to_csv(args.out)
    print(f"Wrote {len(out)} rows to {args.out}")
    print(
        "Reminder: HG=F (copper) has been converted from USD/lb to USD/tonne. "
        "Continuous-futures tickers can splice contracts at rollover without "
        "adjustment; verify there's no artificial jump at each contract's expiry "
        "date before trusting daily returns from either of these. For zinc, use "
        "data_loaders.load_fred_zinc (FRED PZINCUSDM) instead -- not fetched here. "
        "HG=F is a US exchange price and diverged materially from LME copper "
        "during the 2025 tariff episode -- see this file's module docstring "
        "before using mid/late-2025 data unexamined."
    )


if __name__ == "__main__":
    main()