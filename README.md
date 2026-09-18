# Copper's Hidden Margin / Acid-Credit Divergence — code

**Start with `STRATEGY_NOTE.md`, not this file** — it's the primary
document (thesis, real-data read, case studies, what changed our mind).
This README covers how the code works. The split mirrors a common pattern
for this kind of research repo: one document for whether the idea holds
up, one for how the code that tests it works — with the emphasis here on
the former, since a market-strategist deliverable is judged on the thesis,
not the pipeline.

**Quick start — the current read, real data:**
```
python acid_cushion_monitor.py
```
This is the project's PRIMARY output now (see the changelog below for
why): the "Copper Acid Cushion Monitor," built entirely from real, cited
weekly SMM data through this project's data-collection date
(2026-09-16), no synthetic fixture involved.

This is **not** a systematic trading strategy. There is no backtest,
Sharpe ratio, or walk-forward evaluation anywhere in this project, on
purpose — see `STRATEGY_NOTE.md`'s "What this is and isn't."

## Changelog — 2026-09-16: pivot to the copper acid-cushion thesis

A new source article ("Copper's Hidden Margin: When the Acid Cushion
Starts Shrinking," Sep 7 2026) plus a full review of this project against
it concluded the project's original framing — a **zinc-vs-copper**
long/short thesis built on "acid rose, TC fell" — had drifted from the
sharper, better-evidenced question actually worth testing: **is copper
smelters' acid-credit cushion, which absorbed a year of collapsing TC,
now itself shrinking?** That's a COPPER-specific question. Zinc shows the
same mechanism (see the Cross-check section of the monitor output) but is
now corroborating evidence, not the central test.

**What changed, concretely:**

1. **New primary data module, `copper_acid_data.py`.** Real, weekly,
   cited SMM data: the Imported Copper Concentrate Index (TC) and the
   China Copper Smelting Sulphuric Acid Index, both from ~Jan 2026 through
   2026-09-04 (the most recent print as of this project's data-collection
   date). Every point is tagged `cited` (a specific dated print),
   `cited-approx` (tied to a range/qualitative anchor, not one dated
   print) or `interpolated` (no citation for that exact week — linearly
   filled between cited anchors, and never presented as more precise than
   that). Also holds: Kamoa-Kakula's (Ivanhoe Mines) quarterly disclosed
   acid credit/opex figures, the SMM EXW DRC/Zambia regional acid
   benchmark, a period-matched USD/CNY FX table (see point 6), CRU's
   smelter-income-mix figures, and PMI/COMEX/sulphur-trade context. See
   its module docstring for the full citation list.
2. **New primary metrics, in `margin_model.py`:** `acid_cushion_ratio()`
   (acid revenue ÷ |TC|, the direct answer to "how much of the TC drag is
   acid absorbing"), `cushion_loss()` (its change over time),
   `residual_margin()` (splits margin into `margin_ex_acid` +
   `acid_contribution`, so "is the smelter already underwater without
   acid" is a direct read, not an inference), `acid_stress_test()`
   (-10/-20/-30% acid-price shock table), `implied_acid_yield_and_buffer()`
   (dimension-safe version of the old Acid* idea, for a disclosure like
   Kamoa's that's per lb of payable copper, not per tonne of concentrate),
   and `treatment_margin()`/`free_metal_revenue()` — see point 4.
3. **Models renamed by function, not just robustness-tier:**
   - **Model A → "Acid Cushion."** `model_a.
     run_model_a_copper_acid_cushion()` is now the core analysis: real
     weekly TC + acid data → `acid_cushion_ratio`, `residual_margin`,
     `acid_stress_test`, trend figures. `run_model_a()` (zinc vs copper)
     is kept, unchanged, as the secondary cross-metal check.
   - **Model B → "Acid Price Robustness."** `model_b.
     run_model_b_acid_robustness()` checks whether the reading survives a
     different acid-price SOURCE (SMM China domestic vs SMM EXW DRC/
     Zambia) or a different TC-index PROVIDER (SMM vs S&P Global Platts).
     Real, but sparse — snapshot comparisons at the nearest dates an
     alternative source has a print, not a second full time series (see
     the function's docstring). It does NOT uniformly confirm the
     thesis — see "What robustness actually found," below.
   - **Model C → "Realized Acid Economics."** `model_c.
     run_model_c_realized_acid_economics()` centers Kamoa-Kakula's own
     Q1/Q2 2026 disclosed numbers (not Freeport, which is now a secondary
     cross-check) — the article's own empirical anchor. Computes Kamoa's
     own cushion-ratio narrowing (Q1 118.5% → Q2 95.1%, visible in its own
     filings before the SMM index-level shrinkage) and tests "does
     integration earn a pricing edge" against the DRC benchmark (it
     doesn't, on this data point — a real $95/t discount).
4. **A real modeling gap, found and fixed: `treatment_margin()`.** The
   original `smelter_margin()` folds in the smelter's FULL payable-metal
   revenue — correct for an INTEGRATED mine+smelter (Kamoa), but a huge
   overstatement for a CUSTOM/TOLLING smelter (Freeport Miami, typical
   Chinese import smelters), whose own margin the industry actually prices
   as **TC + "free metal" + byproducts − costs** (this is exactly CRU's
   own income-mix framing, quoted in the source article: "TC revenue...
   free metal... by-product credits"). Feeding TC-scale numbers ($ tens to
   hundreds per tonne) into a metal-price-scale margin (thousands of $/t)
   would have buried the whole acid-cushion signal in copper-price noise —
   and the review's own illustrative "Residual Margin" figures (Margin
   ex-acid ≈ +20 / −5 / −40, not +$3,020 / +$2,995 / +$2,960) only make
   sense on the treatment-scale reading. `residual_margin()` and
   `acid_stress_test()` now run on `treatment_margin()`, not
   `smelter_margin()`. `smelter_margin()` itself is untouched — still the
   right function for Kamoa-style integrated economics, and still used
   as-is by the unchanged zinc-vs-copper secondary path.
5. **The binary "N of 5 conditions" framework is replaced for this
   thesis.** `thesis_dashboard.py` is new: 7 categorical states (TC
   regime, acid cushion, treatment margin, physical response, acid-market
   regime, demand, regional realization), each with a cited one-line
   reason, plus a narrative status block (Observed / Mechanism / Physical
   response / Cause of acid decline / Forward catalyst) — this is
   literally what the review asked for, because forcing PMI, the zinc
   cross-check, and "what's causing the acid decline" into pass/fail
   conditions would misrepresent evidence the source article itself calls
   mixed or unclear. `thesis_monitor.py`'s original 5-condition boolean
   machinery is UNCHANGED and still used for the secondary zinc-vs-copper
   check — it was never wrong for that narrower question.
6. **Fixed: flat 7.1 CNY/USD conversion used for every quarter
   2023-2026 alike.** USD/CNY moved from ~7.1-7.3 in 2023-2025 to
   ~6.7-7.0 by mid-2026 (the yuan's strongest levels since Jan 2023) — the
   flat rate was understating 2026 acid prices in USD terms by roughly
   5-8%. `copper_acid_data.cny_to_usd()` / `USD_CNY_QUARTERLY` replace it
   with a period-matched (still approximate, but no longer flat) quarterly
   table. `real_data_check.py`'s `acid_price` column now uses it too.
7. **`real_data_check.py`'s stale gaps closed.** `zn_price` is no longer
   100% invented — `data/fred_zinc.csv` (flagged missing in the
   2026-09-15 changelog below) has since been added and is real for every
   quarter. `2026-Q1`/`2026-Q3`'s `cu_tc`/`acid_cny` — previously all-NaN
   — are now derived from `copper_acid_data.py`'s cited weekly series
   (quarter-mean, clearly labelled as derived, not a single dated print).
   `2026-Q3`'s `zn_tc` is now populated too (Aug-2026 all-time-low print).
   `2026-Q1`'s `zn_tc` honestly stays NaN — no citation was found.
8. **New self-check, `_selfcheck_residual_margin_additivity()`** in
   `margin_model.py` (run via `python margin_model.py`) — proves
   `margin_ex_acid + acid_contribution == total_margin` exactly, at every
   `acid_stress_test()` shock level, not just asserted in a docstring.

**What robustness (Model B) actually found — reported straight, not
smoothed over:** the ~94% cushion-ratio reading is specific to China's
domestic acid market. At the SMM EXW DRC benchmark (~$935/t vs China's
~$228/t as of 2026-09-04), the same TC would show a cushion ratio over
380%; at the Zambia benchmark (~$400/t), over 160%. This does not
undermine the thesis — the TC series and the domestic acid index describe
the SAME population of Chinese smelters — but it means "the cushion is
shrinking" is a claim about the Chinese domestic market specifically, not
a universal acid-market statement, and the monitor's Cross-check section
reports the DRC/Zambia comparison explicitly rather than only showing the
number that confirms the headline. The TC-index-provider check (SMM vs
Platts, $2.94/dmt apart in April) agrees closely — that part of the
reading is NOT source-specific.

## Files
- **`copper_acid_data.py`** — PRIMARY real-data module. See changelog
  point 1.
- **`model_a.py`** — `run_model_a_copper_acid_cushion()` (PRIMARY, see
  changelog point 3) + `run_model_a()` (secondary, zinc vs copper,
  unchanged). `DEFAULT_CU_PARAMS`'s header comment records which fields
  are cited vs rule-of-thumb/invented.
- **`model_b.py`** — `run_model_b_acid_robustness()` (PRIMARY) +
  `run_model_b()`/`run_cost_stress()` (secondary, synthetic-regional-
  variant robustness for the zinc/copper check, unchanged).
- **`model_c.py`** — `run_model_c_realized_acid_economics()` (PRIMARY,
  Kamoa-centered) + `run_model_c()`/`compare_a_b_c()` (secondary,
  proprietary-data overlay layer for the zinc/copper check, unchanged).
  Read the module docstring's UNIT-BASIS WARNING before touching Kamoa's
  $/lb figures — they are not on the same basis as `SmelterParams`.
- **`thesis_dashboard.py`** — PRIMARY. 7-category Thesis Dashboard, see
  changelog point 5.
- **`acid_cushion_monitor.py`** — PRIMARY entry point. Runs A → B → C →
  Dashboard on real data and renders the "Copper Acid Cushion Monitor"
  report; also writes `output/copper_acid_cushion_weekly.csv`,
  `output/copper_acid_cushion_stress.csv`, `output/kamoa_kakula_
  quarterly.csv`. Run directly: `python acid_cushion_monitor.py`.
- **`margin_model.py`** — `SmelterParams`, `smelter_margin()` (full,
  metal-inclusive — right basis for an integrated miner+smelter),
  `treatment_margin()`/`free_metal_revenue()` (TC-scale, custom-smelter
  basis — see changelog point 4), `acid_sensitivity()`,
  `curtailment_threshold()` (root-finds Acid* where `smelter_margin` = 0),
  `threshold_gap()` (sign convention corrected 2025-09-15 — read its
  docstring before quoting a gap number in prose), `margin_bridge()`
  (exact linear decomposition of a `smelter_margin` CHANGE),
  `empirical_acid_sensitivity()`, `energy_stress_test()`, and the new
  PRIMARY-path functions from changelog point 2. Two runnable self-checks
  at the bottom (`python margin_model.py`).
- **`thesis_monitor.py`** — secondary/cross-metal. The five
  thesis-confirmation conditions for zinc vs copper, `build_monitor()`,
  `conditions_met_distribution()`, `narrative_summary()`. Unchanged; see
  its module docstring for why the primary thesis moved to
  `thesis_dashboard.py` instead.
- **`data_loaders.py`** — one loader per free source, plus (new)
  `load_daily_metal_prices()` for the primary pipeline's weekly-reindexed
  copper price. `load_fred_zinc()` and `load_real_metal_prices_quarterly()`
  both now have real, verified data behind them (see changelog point 7).
  The rest (World Bank Pink Sheet, USGS, ILZSG, ICSG, company filings,
  China Customs HS2807 export-proxy, regional acid quotes) each document
  the exact CSV schema and page to download from. None fetch data
  automatically from inside this sandbox.
- **`smelter_calibration.py`** — unchanged. `load_calibrated_params()`
  now doubles as `model_c.py`'s Freeport cross-check source.
- **`real_data_check.py`** — secondary/cross-metal real dataset. See
  changelog points 6-7. Prints a provenance table every run — which of
  `zn_price`/`cu_price`/`silver_price` are real for which quarters, which
  quarters are missing manually-curated TC/acid figures, and event-window
  notes for known non-fundamental price shocks.
- **`demo.py`** — secondary/cross-metal pipeline smoke test on a
  SYNTHETIC fixture. Proves the zinc/copper code paths run; proves
  nothing about real markets. The primary pipeline has no synthetic demo
  — `copper_acid_data.py`'s real series IS its input.
- **`fetch_metal_prices_yfinance.py`** — run **locally**, not in this
  sandbox. Copper and silver only (zinc via FRED instead — see
  `data_loaders.py`). Currently fetched through 2026-09-16.
- **`provenance.py`** — unchanged, generic quarter×field provenance-matrix
  builder; used conceptually by `real_data_check.py`'s printed table
  (not literally imported by it — that file builds its own provenance
  dicts inline).

## Using it with real data
**Primary (copper acid-cushion thesis):** already wired to real data —
just run `python acid_cushion_monitor.py`. To refresh it later in 2026,
re-run `fetch_metal_prices_yfinance.py` locally for `cu_price` (needed
for the weekly reindex), and add new cited weeks to
`copper_acid_data.py`'s `CU_TC_WEEKLY_RAW`/`CU_ACID_WEEKLY_RAW` as SMM
publishes them — the interpolation grid updates automatically once new
cited anchors are added.

**Secondary (zinc-vs-copper cross-metal check):**
1. Run `fetch_metal_prices_yfinance.py` locally for copper/silver, and
   download FRED `PZINCUSDM` for zinc (`scripts/download_fred_zinc.py`
   or manually — see `data_loaders.load_fred_zinc`'s docstring). Both are
   now present in `data/`.
2. Build one `pd.DataFrame` indexed by date with columns: `zn_price,
   cu_price, acid_price, zn_tc, cu_tc, silver_price, energy_price,
   zn_production, zn_stocks, cu_stocks` (see `demo.make_synthetic_data` or
   `real_data_check.REAL_DATA` for the exact shape).
3. Finish calibrating `SmelterParams` for zinc and copper from Nexa's
   20-F/6-K and Freeport's 10-K (`load_company_filing_byproducts`) —
   `acid_yield` and copper's `metal_grade` are cited industry/filing
   figures; `payable_fraction`, `conversion_cost`, `energy_per_t`,
   `premium` and the by-product yields are still rule-of-thumb or
   invented. Until these are tightened, `curtailment_threshold()`'s Acid*
   values will keep landing far outside any realistic observed acid
   price for the zinc/copper path — see that function's docstring. (The
   primary copper acid-cushion path sidesteps this for Kamoa specifically
   via `implied_acid_yield_and_buffer()`, which derives its own implied
   yield from Kamoa's own disclosed numbers instead of trusting
   `SmelterParams.acid_yield`.)
4. `run_model_a(df)`, then `run_model_b(...)` with regional acid series and
   TC variants, then optionally `run_model_c(...)`. Compare with
   `compare_a_b_c()`. Use `margin_bridge()` to decompose any margin move
   you see into its channels before concluding anything from it.

## Known limitations (code-level — see STRATEGY_NOTE.md for thesis-level ones)
- **No automated data fetching** for any source from inside this sandbox;
  `fetch_metal_prices_yfinance.py` and the FRED CSV download both need a
  machine with real network access, and every `data_loaders.py` loader
  still requires a manually-downloaded file regardless of environment (TC
  and the China acid index specifically have no free API — every weekly
  point in `copper_acid_data.py` was transcribed from a named SMM/Platts
  article, checked 2026-09-16).
- **`copper_acid_data.py`'s weekly grid mixes provenance levels.** The
  `status` column on every row tells you which — `cited`, `cited-approx`
  or `interpolated` — but a naive reader of `cu_tc_weekly_interpolated()`
  alone could mistake a smooth-looking weekly series for uniformly dated
  prints. Always check `status` before quoting an individual week
  externally; the 9W/13W trend figures in particular may use an
  interpolated reference point (see `model_a.py`'s `provenance_note`).
- **`ENERGY_PRICE_USD_MWH = 70.0` (model_a.py) is a flat, uncalibrated
  placeholder** — no free public daily/weekly industrial-electricity
  series for Chinese copper smelters was found. Its effect on the
  acid-cushion outputs is modest (energy is a small share of
  `treatment_margin()` at current TC/acid levels — check
  `acid_stress_test()`'s output directly if you want to verify that
  claim on today's numbers) but it is a real gap, not a solved input.
  `real_data_check.REAL_DATA` uses the same placeholder for 2026-Q1/Q3
  (previously NaN, which cascaded into the whole quarter's margin
  figures being NaN — see changelog point 7).
- **`treatment_margin()`'s absolute dollar level still inherits
  uncalibrated inputs** (`conversion_cost`, `premium`, the energy
  placeholder above) — the DIRECTION (deteriorating through 2026) and the
  SENSITIVITY to the acid channel (`acid_stress_test()`'s shock table) are
  the load-bearing outputs; the exact "-$128/t" headline number should be
  read as "this shape and sign are real, this precision is not," same as
  every other dollar figure in this project.
- **Kamoa-Kakula's Q1 2026 `implied_acid_yield_and_buffer()` is
  intentionally left NaN** — Ivanhoe's Q1 release disclosed a new
  CONTRACT acid price (~$725/t), not a realized weighted-average price;
  computing an implied yield/buffer from a contract price would silently
  assume they're equal, which this project does not do. Q2 has a clean
  realized price ($465/t) and is computed.
- **`REGIONAL_ACID_BENCHMARK`'s "unchanged for five weeks" (DRC/Zambia)**
  is reported exactly as ambiguous as the source article itself treats
  it — consistent with genuine price stability OR a thin market with no
  fresh print. Do not upgrade this to "stable" in downstream prose.
- **`model_b.run_model_b_acid_robustness()`'s TC-index-provider check
  compares dates 15 days apart** (SMM 2026-04-24 vs Platts 2026-04-09) —
  the closest real overlap found, not a same-day cross-check.
- (Secondary/cross-metal, unchanged from the 2026-09-15 review):
  `thesis_monitor.py`'s rolling windows are shaped for daily data as a
  matter of code convenience; `margin_bridge()`'s decomposition is exact
  only because `smelter_margin()` is linear in its inputs;
  `curtailment_threshold()`'s root-finding bounds are wide but not
  guaranteed to bracket a root for every parameter combination;
  `load_real_metal_prices_quarterly()`'s flat/stale guard is a blunt
  50%-identical-values threshold; `aggregate_monthly_to_quarterly()` has
  no staleness guard (deliberate — see its docstring);
  `model_b.run_model_b()`'s structural `relative_acid_sensitivity` figure
  is fixed by `SmelterParams.acid_yield` and reported once, not as a
  range — its empirical counterpart is a short, regime-mixed OLS slope,
  directional only.

## Changelog — 2026-09-15 code review (superseded in emphasis by
2026-09-16 above, kept for history)

A full read-through (code + data + docs) found and fixed the following.
Kept here, dated, in the same self-critical spirit as `arbitragebot`'s
README — a strategist portfolio piece is stronger for showing the bugs
that were found and fixed, not just the finished state.

1. **`margin_model.threshold_gap()`'s docstring had the sign convention
   backwards** ("positive => zinc curtails later" — it's the opposite: a
   positive gap means zinc's Acid* is the HIGHER one, i.e. zinc is the
   MORE exposed / earlier-curtailing metal). The arithmetic itself was
   never wrong, and the demo's +1441.98 figure was directionally
   consistent with the original thesis once read correctly — only the
   prose explanation needed fixing. Corrected, with a runnable self-check
   (`python margin_model.py`).
2. **`model_b.py`'s "robustness range" for `relative_acid_sensitivity`
   was tautological** — fixed entirely by `SmelterParams.acid_yield`,
   which no regional-acid or TC-variant combination touches. Added a
   genuine empirical (OLS-fit) sensitivity that does vary.
3. **Duplicate `fetch_metal_prices_yfinance.py`** — a second, unguarded
   copy at the project root was deleted; the one inside the project
   folder (with the flat/stale guard and `_warn_if_large_jump`) is
   canonical.
4. **A stale `output/demo_signal.png`** from before `thesis_monitor.py`
   was renamed away from "signal" framing — `demo.py` now deletes it
   automatically every run.
5. ~~**`zn_price` is still 100% invented in `real_data_check.py`**~~ —
   **RESOLVED 2026-09-16**: `data/fred_zinc.csv` has since been added;
   `zn_price` is real for every quarter now. Left here, struck through,
   rather than deleted, so the "reported but not yet fixed" → "fixed"
   arc is visible, not quietly edited away.
6. **`real_data_check.QUARTERS` extended** to include `2026-Q1` and
   `2026-Q3` (partial). `2025-Q2`/`2025-Q3` remain deliberately excluded
   (see point 7).
7. **Two real, verified, non-fundamental price shocks** flagged via
   `EVENT_WINDOW_NOTES`: the 2025-07-30 COMEX copper tariff-exemption
   collapse (~20-22% in one session — a US-exchange-specific policy
   distortion, why `2025-Q3` stays excluded) and the 2026-01-29/30 silver
   melt-up/crash (all-time high ~$121/oz to a ~30%+ one-day drop,
   Fed-nomination news + forced liquidations).
8. **Floating-point display noise** (`0.17000000000000004`) now rounded
   before reaching any printed table or CSV — see `model_c._r()`.
