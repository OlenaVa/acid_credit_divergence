# Methodology, data inventory and limitations

Companion to [`../STRATEGY_NOTE.md`](../STRATEGY_NOTE.md). Everything technical lives here so the note can stay about the market.

## 1. The metric

**Acid cushion ratio = acid credit ÷ |TC|**, per tonne of concentrate for a representative custom smelter.

- `acid credit = acid_yield × acid price (USD/t)`; `acid_yield = 0.83 t acid / t concentrate` (Freeport FY2025 by-product data in `data/freeport_copper_byproducts.csv`: 680 kt acid / 821 kt concentrate = 0.83; ±7.5% used for sensitivity).
- `acid price` = SMM China Copper-Smelting Acid Index (RMB/t) **divided by 1.13** (the index is quoted VAT-inclusive by SMM's convention; VAT is not smelter revenue) and converted at **quarterly-average** USD/CNY (a known limitation: FX steps at quarter boundaries; effect on the cushion since April ≈ 1%).
- `TC` = SMM Imported Copper Concentrate Index (USD/dmt), taken as published. **The refining charge (RC) is not included** in the headline — see §5.
- Regime bands: ≥100% *absorbing*, 50–100% *eroding*, <50% *exhausted* — **judgment levels, not calibrated**.

Why a ratio, not a margin: the ratio depends only on acid yield, FX and the quote basis, so it is **independent of the uncalibrated cost inputs**. The model's treatment margin (`margin_model.treatment_margin`) is used only for attribution of *changes*; its absolute level is deliberately not reported in outputs or the note.

## 2. Strategy layer (`strategy_layer.py`)

| Function | What it does |
|---|---|
| `attribute_ratio_change` | Exact log decomposition: ln(R_end/R_start) = ln(acid_end/acid_start) − ln(\|TC_end\|/\|TC_start\|). Acid leg further split into local-currency price and FX. No residual. |
| `attribute_margin_change` | Additive $/t decomposition of the treatment-margin change into TC, acid, free metal, silver (energy, conversion cost and premium are constants). Residual checked ≈ 0. |
| `counterfactual_paths` | Cushion and margin from a reference date with (i) acid held at its reference-date RMB level, (ii) TC held at its reference-date level. Coincides with actual at the reference date (asserted). |
| `regime_matrix`, `cushion_frontier_acid_cny` | Cushion ratio and margin on a (TC × acid RMB/t) grid; the cell at the latest observation reproduces the monitor headline (asserted). |
| `definition_sensitivity`, `definition_paths` | Latest and historical cushion under acid yield × RC (excluded / included) × VAT basis (13% deducted = headline / as quoted). |
| `regional_divergence`, `kamoa_bridge` | China-domestic vs EXW DRC/Zambia; Kamoa Q1→Q2 credit-vs-opex bridge and Q3 forward coverage. |
| `sulphur_parity` | Burner-feedstock context for acid price (stale: sulphur last refreshed 31 Jul). Not an input to any headline number. |
| `falsification_checks` | Pre-registered conditions C1–C7 with status. Thresholds are judgment levels. |

Self-checks: `python strategy_layer.py` asserts decomposition exactness, margin additivity, counterfactual consistency at the reference date, regime-matrix/monitor agreement, frontier correctness, definition-variant collapse to the headline, and the Kamoa opex-vs-credit bridge.

## 3. Data inventory and provenance

Every weekly point in `copper_acid_data.py` is tagged **cited** (a dated print in a named public source, including prints implied by "down X from Y" statements in a later SMM review), **cited-approx** (value tied to a date range or qualitative anchor) or **interpolated** (grid-fill between the nearest cited points; never overwrites a cited value). Interpolated weeks appear only to give charts and trend windows a regular weekly grid; **no headline statistic uses an interpolated endpoint** (the `trend_basis` field in `model_a` reports which reference points are cited, and the monitor prints a warning if any is not).

| Series | Source | Cadence | Latest | Status |
|---|---|---|---|---|
| Copper TC (Imported Copper Concentrate Index) | SMM | weekly | 24 Sep 2026 | 20 of 39 grid weeks cited / cited-approx |
| China copper-smelter acid index | SMM | weekly | 24 Sep 2026 | 18 of 39 grid weeks cited / cited-approx |
| Both series cited on the same week | — | — | — | 16 of 39 |
| Copper, silver price | yfinance | daily | 25 Sep 2026 | observed |
| EXW DRC / EXW Zambia acid | SMM (launched 5 Jun 2026) | weekly | 4 Sep 2026 | observed; flat 5+ weeks — stable or thin, undetermined. **Stale.** |
| Sulphur EXW Shandong | SMM weekly reviews | weekly | 31 Jul 2026 | two cited points only. **Stale.** |
| Kamoa-Kakula quarterly disclosure | Ivanhoe Mines releases (Q1: 6 May; Q2: 29 Jul) | quarterly | Q2 2026 | checked against the releases. Q3 forward figure ($0.60/lb) is a management indication from a secondary summary of the 30 Jul call. |
| China H2SO4 exports | China Customs via SMM | monthly | Jul 2026 | observed |
| CRU smelter income mix | CRU (via the article) | annual snapshot | 2025 | built against TCs far less negative than today's |
| Freeport by-product data (`data/freeport_copper_byproducts.csv`) | Freeport filings | annual | FY2025 | as transcribed in the repo; used for the acid-yield default |
| Nexa by-product data | placeholder | — | — | **UNVERIFIED; not used in any headline output** |

Series definitions the model does **not** know: freight, handling, storage, the exact VAT basis of the national RMB acid index (inferred, not read from its RMB page), and any specific smelter's contract terms.

## 4. Model inputs and what is uncalibrated

`margin_model.SmelterParams` / `model_a.DEFAULT_CU_PARAMS`: metal grade 25.5% and acid yield are cited; **payable fraction (96%), conversion cost ($260/t), energy intensity (0.40 MWh/t), premium ($20/t) and the by-product yields are rule-of-thumb**; energy price is a flat $70/MWh placeholder. Consequences:

- The margin **level** is not reported anywhere (it is dominated by the assumed conversion cost); only changes are, because the constants cancel.
- Freeport calibration (`smelter_calibration.py`) is used only for acid yield and metal grade (0.828 t/t, 25.5%). The CSV's silver figure is company-wide silver sales divided by Miami smelter throughput (≈5.2 oz/t, not a plausible smelter yield), so the code rejects it (silver yield set to 0 with a printed warning); the model's silver input is the 0.05 oz/t placeholder.
- The precious-metal credit is token: silver is priced (0.05 oz/t); a placeholder gold yield (0.002 oz/t) is defined but **no gold price is loaded**, so gold contributes zero. This is deliberate: at any plausible gold price it is < $12/t of concentrate (vs a TC of -$225 and an acid credit of ~$136), it cannot touch the cushion ratio, and its *change* over any window is ~$1/t. The margin level is not credible for other, much larger reasons (conversion cost, §4), so adding gold would add precision to an invented parameter.

## 5. Definition sensitivity (why the level is fragile)

- **Refining charge.** SMM states the convention that RC is 10% of TC (RC in cents/lb = TC in $/dmt ÷ 10). On a 25.5% concentrate with 96% payable, that adds ≈$121/dmt of drag at TC -$224.53 (≈54% on top of TC). It is a **convention, not an observed series**, so it is used only as a sensitivity.
- **VAT.** Checked on SMM's price pages (2 Oct 2026): the *original RMB* price includes 13% VAT and the USD series deducts it — e.g. Inner Mongolia EXW: CNY 785/t = USD 111.19 VAT-included = USD 98.40 VAT-excluded; the national index's USD page (SMM-CU-SA-001) states "13% VAT deducted for USD pricing". The national index's RMB page itself was not retrieved, so a VAT-inclusive RMB quote is **inferred from that convention**. The headline therefore deducts VAT (÷1.13); the as-quoted figure is shown as a sensitivity.
- **Acid yield.** ±7.5% around 0.83.

Result at the latest print: 60% (headline: TC only, VAT deducted) → 68% (as quoted) → 39% (TC + RC, VAT deducted) → 44% (TC + RC, as quoted); full range 36%–73% including yield. The date the cushion drops below 100% for good ranges from 26 Jun (TC + RC, VAT deducted) to 28 Aug (TC only, as quoted); the headline definition: 21 Aug.

## 6. Kamoa-Kakula

Disclosed per lb of payable copper on an integrated mine+smelter basis; **never fed through `SmelterParams`** (per tonne of concentrate). Acid credit ÷ smelter opex: Q1 0.32/0.27 = 118.5%; Q2 0.39/0.41 = 95.1%. Bridge (`kamoa_bridge`): realised acid price $467 → $465/t (-0.4%; the Q2 release states it was unchanged); credit per lb +22% (more acid sold per lb of copper produced: +10.6% acid revenue on ~10% less copper produced); opex per lb +52%, which the Q2 release attributes to partial capitalisation of smelter operating costs in Q1 (utilisation ~60% in both quarters). Implied yield from Q2 ($0.39/lb at $465/t) ≈ 1.85 t acid / t Cu. Forward: management ~$0.60/lb for Q3 (secondary source); implied-yield cross-check $840/t × yield ≈ $0.70/lb (172% of Q2 opex). Opex is held at its Q2 level in both forward figures — an assumption.

## 7. Known limitations

1. **Benchmark model of a representative smelter**, not any real smelter's economics.
2. **Interpolated weeks** — 23 of 39 grid weeks still have at least one interpolated series (mostly Jan–Jun). Charts mark cited prints separately from the line; statistics use cited endpoints.
3. **Uncalibrated costs; token precious-metal credit** (§4).
4. **RC and the inferred VAT basis** change the level materially (§5).
5. **FX** uses quarterly averages.
6. **Regional benchmark** is young (launched 5 Jun) and stale since 4 Sep; DRC/Zambia are inland leach markets, not an arbitrage leg for a Chinese producer. The China–ex-China comparison is dated 4 Sep on both sides.
7. **Kamoa** is one company; Q3 is a management indication, not a result.
8. **Physical response is unconfirmed**; cuts may reflect concentrate scarcity rather than acid.
9. **No backtest, no statistical test.** The strategy layer is descriptive and makes the thesis falsifiable; it does not estimate a relationship. Thresholds and regime bands are judgment.
10. **No tradeable instrument identified** for acid; the market-expression section lists observables only.

## 8. Code map

Primary path: `copper_acid_data.py` → `model_a.run_model_a_copper_acid_cushion` → `model_b.run_model_b_acid_robustness` / `model_c.run_model_c_realized_acid_economics` → `thesis_dashboard.build_thesis_dashboard` → `strategy_layer.run_strategy_layer` → `acid_cushion_monitor` (report, tables) and `strategy_charts` (PNGs).

`extras/` holds the original zinc-vs-copper experiment (`real_data_check.py`, `demo.py` on a synthetic fixture, with outputs in `extras/synthetic_demo/`) and the data-download scripts; none of it feeds the analysis. Every script switches to the repo root itself, so it can be launched from any directory (e.g. an IDE run button) without creating stray `extras/extras` or `output` folders. `model_a`/`model_b`/`model_c` still contain old zinc-path functions next to the copper ones (and `model_a` imports `thesis_monitor` and `data_loaders`), so those files stay in the root; splitting them was not done.

Verification: `python copper_acid_data.py && python margin_model.py && python strategy_layer.py`. Refresh: add new cited weeks to `CU_TC_WEEKLY_RAW` / `CU_ACID_WEEKLY_RAW` (and, for a new quarter, a USD/CNY rate to `USD_CNY_QUARTERLY`; a missing quarter falls back to the nearest one with a printed warning), run `python copper_acid_data.py` (checks the grid picked them up), then `python acid_cushion_monitor.py`. The "last 4 weeks" attribution window rolls with the grid; the other two windows are fixed historical dates.

Note: comments in the legacy code refer to "the earlier README" / "the earlier strategy note" — those were the pre-1 Oct documents; they are not part of this folder (see git history).