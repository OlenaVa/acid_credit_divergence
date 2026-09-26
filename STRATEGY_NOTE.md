# Copper's Hidden Margin — Strategy Note

This is the primary document for this project. `README.md` covers how the
code works; this covers whether the thesis holds up, which is the actual
job of a market strategist. There is no backtest, Sharpe ratio, or
walk-forward evaluation anywhere in this project, on purpose — see "What
this is and isn't" below.

## Pivot note (2026-09-16)

A new source article — "Copper's Hidden Margin: When the Acid Cushion
Starts Shrinking" (Olena Vasiuta, Sep 7 2026) — reports that the SMM
Imported Copper Concentrate Index (TC) sat at **-$200.31/dmt** on
2026-09-04, its most negative print yet, while the SMM China Copper
Smelting Sulphuric Acid Index has fallen for a **ninth consecutive week**
to RMB 1,539.5/t, down from a peak near RMB 1,789/t in early July. Those
two facts together are a sharper, better-evidenced, and — importantly —
narrower question than this project originally set out to test.

**The project's original framing** (Part Two, below) was a **zinc-vs-
copper** relative-value thesis: declining acid economics were hypothesised
to hit zinc smelter margins harder than copper's, predicting relative
zinc tightening. The 2026-09-15 review already found that acid price had
moved the *opposite* way from what that thesis assumed — it *rose*
sharply through 2024-2026, becoming a "profit lifeline" for smelters
rather than a second blow alongside collapsing TC.

**What the new article adds is the next chapter of that same story, not a
different one:** the acid cushion that absorbed a year of TC collapse is
now, itself, starting to narrow — and the sharpest, most current, most
falsifiable version of that question is COPPER-specific, not a zinc-vs-
copper comparison. Zinc shows the same mechanism (SMM's spot zinc TC hit
an all-time low of -$113/t in August 2026, and Reuters reports zinc
smelters leaning harder on silver and acid credits too) but it is
corroborating evidence now, not the central test — see "Cross-check:
zinc," below.

**This note is restructured accordingly.** Part One is the new primary
analysis: the copper acid-cushion thesis, on real data through
2026-09-24 (extended 2026-09-25 from the original 2026-09-04/09-16
pass — see Part One's own changelog at the end for what that extension
changed and two real code bugs it exposed and fixed). Part Two is the
original zinc-vs-copper note, preserved as-is (including its own
2026-09-15 correction note, now itself updated 2026-09-25 — see below) —
still useful secondary evidence, and an honest record of how this
project's thinking evolved, not deleted just because the emphasis moved.

---

# Part One: the copper acid-cushion thesis (primary)

## The mechanism

Copper smelter income has three lines: the treatment charge (TC), the
smelter's own retained ("free") metal, and by-product credits —
predominantly sulphuric acid. CRU's own numbers (cited in the source
article) show how much that mix has shifted: TC revenue was **39%** of
smelter income in 2018; by 2025, free metal was roughly **50-53%** and
by-product credits — mostly acid — another **25-27%**. CRU's own caveat
matters here too: that 2025 split was built against TCs nowhere near as
negative as today's -$200/dmt print. At current levels, TC isn't a
shrinking revenue line any more — it's a net subtraction that free metal
and acid have to cover outright, so the real H2-2026 mix is almost
certainly skewed further toward acid/metal than the 2025 snapshot shows.

For most of the past year, acid income did that job: as TC collapsed,
rising acid prices cushioned the hit (this project's own real-data read
found the same thing on the zinc/copper side — see Part Two). **What
changed in Q3 2026 is that TC's deterioration may be slowing (SMM's own
weekly note: smelters showing "greater resistance to accepting deeper
negative TC/RCs," spot deals struggling below roughly index-minus-$20 to
-$28/dmt) while the acid offset is now actively, and independently,
declining.** TC and acid don't need to move in mechanical opposition to
matter together — they sit on the same revenue equation, and the question
this project's models now answer directly is: **how much of the negative
TC is currently being absorbed by acid revenue, and what happens if that
cushion keeps eroding while TC stays near its floor?**

## The current read (as of 2026-09-24, data extended through 2026-09-25)

Run `python acid_cushion_monitor.py` for the live version of this table;
the figures below are what that script prints on this project's real,
cited weekly data. **Updated 2026-09-25** with three new real weekly
prints (2026-09-11, 09-18, 09-24) that were not yet available at the
2026-09-04/16 pass — the numbers below replace that snapshot; see this
note's own changelog at the bottom for the before/after and for the two
code bugs that extending the data exposed and fixed. The same run also
writes `output/copper_acid_cushion.png` (added 2026-09-26) — a real-data
chart of TC vs acid price and the Acid Cushion Ratio over time, the
clearest single picture of the finding below.

| Metric | Value (2026-09-24) | Value (2026-09-04, for comparison) |
|---|---|---|
| TC (SMM Imported Copper Concentrate Index, weekly) | **-$224.53/dmt** | -$200.31/dmt |
| Acid credit (treatment basis, `DEFAULT_CU_PARAMS.acid_yield` × acid price) | **+$153/t concentrate** | +$189/t concentrate |
| **Acid Cushion Ratio** (acid credit ÷ \|TC\|) | **68.2%** | 94.3% |
| Margin ex-acid (treatment basis) | **-$339/t concentrate** | -$317/t concentrate |
| Total treatment margin | **-$186/t concentrate** | -$128/t concentrate |

Two things worth being direct about in that table. First, **acid is now
covering roughly two-thirds of the TC drag, down from essentially all of
it seven weeks earlier** — 68.2% is a real number, not a rounding
artefact, and the 26-point drop in three weeks is a materially faster
deterioration than the 2026-09-04 snapshot on its own implied. Second,
**the model's own treatment-margin read is negative even WITH the acid
credit**, and has gotten MORE negative — margin ex-acid is deeply
negative (-$339/t) and acid isn't close to big enough to pull the total
back to zero (total margin -$186/t, worse than -$128/t three weeks
earlier). Read the *direction and relative sensitivity* here as the
load-bearing finding, not the exact dollar figures — `conversion_cost`,
`premium` and the energy-price placeholder behind that number are still
rule-of-thumb, the same honest caveat this project has carried since its
first version (see `model_a.py`'s calibration comment) — but the
DIRECTION of this specific move (cushion narrowing fast, margin widening
its deficit) is the single most-changed fact in this update.

**Trend, not just level (as of 2026-09-24):**

- Acid price: **-21.2% over 1 month, -25.8% over 3 months, -28.4% over 9
  weeks** (all three legs accelerated sharply from the 2026-09-04 read of
  -9.6%/-7.4%/-11.8% — this is no longer a "concentrated in the most
  recent stretch" story, it's a broad acceleration across every window).
- TC: **-$24.69/dmt over 1 month, -$72.13/dmt over 9 weeks** (reported as
  a level change, not a %, because TC is negative throughout this series
  and a "% change of a negative number" reads backwards — see
  `model_a.py`'s `trend` dict).
- **Acid Cushion Ratio: -72.2 percentage points over 9 weeks, -97.5pp
  over 13 weeks.** Still the single sharpest number in this note, and
  sharper than it was three weeks ago (-68.6pp / -85.3pp then). It is
  bigger than acid's own -28.4% move over the same window because TC
  deteriorated even faster in relative terms — the cushion is shrinking
  because BOTH legs are now moving against the smelter, not because
  acid alone fell. Don't attribute this move to acid alone.

**On the reference points these figures compare against, not just
"today" (added 2026-09-26):** the "today" side of every figure above is
always a genuine SMM print — structurally guaranteed, and covered by a
regression test (`copper_acid_data._selfcheck_grid_never_drops_latest_
point()`). The OTHER end of a comparison is not automatically that: the
9-week figures' reference date, 2026-07-24, has no direct SMM print for
either TC or acid and is interpolated between the nearest real citations
on either side — the 1-month, 3-month and 13-week figures all land on
real cited prints instead. That does not make the 9-week figures wrong
(interpolating an already-elapsed, closed historical gap for a trend
comparison is standard practice, not a look-ahead problem — see
`copper_acid_data._interpolate_to_grid()`'s docstring for the full
reasoning), but it's now disclosed rather than implicit: `model_a.py`
returns a `trend_basis` dict alongside `trend`, and the monitor marks the
affected lines with `*`.

**Stress test (acid price shock, TC and copper price held at the latest
snapshot):**

| Acid shock | Total treatment margin | Cushion ratio |
|---|---|---|
| flat | -$186/t | 68.2% |
| -10% | -$201/t | 61.4% |
| -20% | -$216/t | 54.6% |
| -30% | -$232/t | 47.7% |

A further 20-30% acid decline is no longer a hypothetical tail scenario —
the index has ALREADY fallen roughly 30% from its early-July peak
(RMB 1,789/t → RMB 1,247.5/t) in eleven weeks, i.e. the stress test's
"-30%" column and the base case are converging. On the current trajectory
the cushion ratio is on a path toward the range this stress test used to
treat as an extreme downside case, with TC unchanged (and TC has not been
moving in the smelter's favor either). This is a stress test, not a
forecast: it deliberately does not model TC and acid moving together,
even though in practice they may (see "What would move this thesis,"
below).

**Acid-yield sensitivity, added 2026-09-26 (TC/acid/metal price held at
the latest snapshot; `acid_yield` flexed across the full cited range):**

| `acid_yield` | Total treatment margin | Cushion ratio |
|---|---|---|
| 0.765 (industry range, low end) | -$198/t | 62.9% |
| 0.83 (current default, ≈Freeport-implied) | -$186/t | 68.2% |
| 0.8925 (industry range, high end) | -$174/t | 73.3% |

The headline Acid Cushion Ratio is directly proportional to
`DEFAULT_CU_PARAMS.acid_yield`, which is itself a single point estimate
(close to, not identical to, Freeport's own implied figure of ~0.828 —
see "A real modeling gap," below) inside a wider cited industry range.
This table answers directly how much of the "68.2%, down from 94.3%"
finding depends on exactly where in that range the true figure sits: not
much, in the sense that matters — the cushion ratio moves by roughly 5
points either side of the default across the ENTIRE cited range, nowhere
close to enough to challenge the qualitative finding (a 26-point collapse
from three weeks earlier). Read this as "the assumption isn't
load-bearing for the direction of the thesis," not as "the assumption is
precisely known" — it still isn't.

## The Thesis Dashboard

Replacing the original project's binary "N of 5 conditions" framework for
this thesis specifically — several of these inputs are evidence the
source article itself calls mixed or unclear, and forcing them into
pass/fail would misrepresent that. See `thesis_dashboard.py`.

| # | Category | State | Why |
|---|---|---|---|
| 1 | TC regime | **EXTREME** | -$224.53/dmt as of 2026-09-24, a NEW record low (also -$221.89/dmt on 09-18, itself a record when printed) — still deteriorating on a 9-week view (-$72.13/dmt) and on the latest single weekly move (-$2.64/dmt). CSPT (the group that normally sets Chinese smelters' quarterly TC guidance) declined to set ANY Q4 guidance price at its 2026-09-24 meeting — the negotiation itself is now breaking down, not just settling at a worse level. |
| 2 | Acid cushion | **SHRINKING** | 68.2% as of 2026-09-24, down 72.2pp over 9 weeks — down from 94.3% just three weeks earlier (2026-09-04); the deterioration has accelerated, not slowed. |
| 3 | Treatment margin | **DETERIORATING** | -$186/t as of 2026-09-24, down from -$128/t on 2026-09-04 (uncalibrated cost inputs — see above; direction is the reliable part). |
| 4 | Physical response | **EMERGING, STRENGTHENING**, not yet CONFIRMED | As of 2026-09-04/16: SMM's note on TC-negotiation resistance, and a reported decline in Chinese copper cathode output in July 2026. Two more pieces added 2026-09-25: SMM's own language shifted from "resistance" to "production cut intentions emerging" among smelters (2026-09-18), and CSPT's Q4 guidance-setting process broke down entirely (2026-09-24, see row 1). Still no smelter statement found that attributes a cut specifically to the acid cushion, as opposed to concentrate scarcity or the extreme TC alone — the CONFIRMED bar has not been cleared, but the gap to it has narrowed materially in three weeks. |
| 5 | Acid-market regime | **UNCLEAR** | China's sulphuric-acid exports collapsed from ~116.7kt (May) to ~980t (June) and stayed near-zero into July — but domestic sulphur (the acid feedstock) itself rebounded ~7.8% w/w in early September even as acid kept falling, which is margin compression for acid PRODUCERS, not a clean read on either a pure export-policy or pure demand story. Added 2026-09-25: the acid-specific export halt is reported (via a government decree cited in CRU's reporting) to run through end-2026 independent of the article's "August 31 fertiliser deadline," which was a different, routine, annual phosphate-fertiliser export-declaration window whose own resumption is, itself, reported inconsistently across sources as of this update (see "What would move this thesis," below) — net effect: leans slightly toward "policy-driven, sticky" on the acid-export side specifically, still UNCLEAR overall pending confirmation either way. |
| 6 | Demand | **MIXED** | China's official NBS Manufacturing PMI (Aug 2026): 49.8 (contractionary). The RatingDog China General Manufacturing PMI, same month: 51.5 (expansionary). A 1.7-point gap is too wide for "Chinese demand is collapsing" to be a clean read. COMEX copper inventories hit a record 675,185t on H1 tariff-driven cathode imports — partly trade-flow positioning, not pure scarcity or surplus. September PMI prints not yet released as of this update. |
| 7 | Regional realization | **DISCOUNT** | Kamoa-Kakula's own Jul/Aug contract acid price (~$840/t) sits **below** the independent SMM EXW DRC benchmark (~$935/t as of 2026-09-04, still the benchmark's own latest print — no fresher regional print found as of this update) — despite an integrated mine-gate structure that should, in principle, help. "Integration equals a pricing edge" is not supported by this data point. |

**Current thesis status:**
- **Observed:** TC extreme and still worsening, acid cushion shrinking
  faster than three weeks ago.
- **Mechanism:** CONSISTENT (both legs of the article's central claim are
  independently confirmed in this project's own data, and both have
  gotten more pronounced since the original 2026-09-04 read).
- **Physical response:** EMERGING, STRENGTHENING, not yet CONFIRMED.
- **Cause of acid decline:** UNCLEAR (though the export-halt timeline
  clarification above leans it slightly toward policy-driven/sticky).
- **Forward catalyst:** acid continues lower while TC remains near its
  floor — the gap between an acid-advantaged smelter and an exposed one
  widens on its own, without either variable needing to move again (the
  source article's own closing framing, and this project's models agree
  with it independently — and, as of 2026-09-24, this is no longer just
  a framing but an observed three-week trend).

## Case study: Kamoa-Kakula (Ivanhoe Mines)

This is the article's own central empirical anchor, and this project now
centers it too (Model C), ahead of Freeport (kept as a secondary
cross-check — see "A real modeling gap," below, and `model_c.py`'s
UNIT-BASIS WARNING before comparing the two numerically).

| | Q1 2026 | Q2 2026 |
|---|---|---|
| Smelter opex | $0.27/lb Cu | $0.41/lb Cu |
| Acid credit | $0.32/lb Cu | $0.39/lb Cu |
| **Acid/OPEX coverage** (credit ÷ TOTAL SMELTER OPEX) | **118.5%** | **95.1%** |
| Realized acid price | n/a (only a new-contract price disclosed) | $465/t |
| Contract price (fwd) | ~$725/t | ~$840/t (Jul/Aug) |

**On terminology (fixed 2026-09-25):** this row used to be labelled
"acid cushion ratio" — the same name used elsewhere in this note for the
benchmark model's Acid Credit ÷ \|TC\| figure (94.3%→68.2% above). They
are NOT the same measurement: Kamoa's disclosure has no TC line to divide
by, so its own ratio is Acid Credit ÷ TOTAL SMELTER OPEX, a broader,
methodologically different denominator. Both point the same direction
(narrowing), which is the genuinely useful read here — but they should
never be read as two numbers on the same scale, and are labelled
differently from here on to avoid exactly that.

**Kamoa's own disclosed numbers already show the cushion narrowing —
from acid MORE than covering smelter opex in Q1, to acid falling just
short in Q2 — a full quarter before the SMM index-level shrinkage shows
up.** At Q2's own realized acid price, this project can back out an
implied acid yield (0.39 ÷ 465 = 0.000839 t acid per lb copper) and from
it a breakeven acid price of **$488.85/t** — against a realized price of
$465/t, an implied buffer of **-$23.85/t**. In other words: even before
the broader SMM decline, Kamoa's Q2 acid channel alone was already
running a small deficit against its own smelter opex. Q1's implied
buffer is deliberately left uncalculated — Ivanhoe's Q1 release disclosed
only a new contract price (~$725/t), not a realized weighted-average, and
assuming the two are equal would be exactly the kind of quiet precision
this project avoids.

**The "does integration earn a pricing edge" question, tested directly
and not confirmed:** Kamoa's Jul/Aug contract price (~$840/t) sits about
**$95/t below** the independent SMM EXW DRC benchmark (~$935/t), despite
Kamoa's integrated mine-gate structure that should, in principle, help.
The source article calls "integration equals a pricing edge" a
"reasonable hypothesis... not a demonstrated one," and this project's own
number agrees — plausible explanations (contract timing vs. spot, offtake
terms lagging the benchmark, internal group pricing) aren't
distinguishable from the data available here.

## Robustness: what survives a different source, and what doesn't

`model_b.run_model_b_acid_robustness()` checks two things, honestly, not
selectively:

**Does the reading depend on which acid market you look at?** Yes, and
substantially — but this comparison is necessarily dated to the regional
benchmark's own latest print, **2026-09-04**, which has not moved since
and is now three weeks behind the domestic TC/acid series' own latest
reading (2026-09-24); the two dates are reported separately in
`model_b`'s output (`acid_price_source_reference_date` /
`domestic_series_latest_date`) rather than silently treated as the same
snapshot — this used to be a real bug (see this note's changelog at the
end). As of that shared 2026-09-04 date: at the SMM China domestic index
(this note's primary series), the cushion ratio is 94.3%. At the SMM EXW
DRC benchmark (~$935/t), the same TC would imply a cushion ratio over
**387%**. At the Zambia benchmark (~$400/t), over **166%**. **This does
not undermine the thesis** — the TC series and the domestic acid index
describe the SAME population of Chinese smelters, which is exactly the
population the source article is about — but it means "the cushion is
shrinking" is a claim about the Chinese domestic market specifically, and
should be stated that way, not generalized to "acid is cheap everywhere."
Kamoa's own numbers (a DRC-based, non-China-domestic operation) show the
SAME directional narrowing (118.5% → 95.1%, on its own Acid/OPEX
coverage basis — see the terminology note above) from a much higher
starting level — consistent with a real, if smaller and later-arriving,
version of the same pressure outside China too. There is no fresher
DRC/Zambia print to re-run this specific comparison against as of
2026-09-25; by 2026-09-24 the domestic-only cushion ratio had fallen to
68.2% (see "The current read," above), which would presumably narrow
this cross-market gap too if a fresh regional print existed — that is a
plausible expectation, not a measured one.

**Does the reading depend on which TC index provider you trust?** No, not
materially. SMM's TC print and an independent S&P Global Platts CIF China
assessment, compared at the closest dates both published one (2026-04-24
vs. 2026-04-09, 15 days apart — not a same-day cross-check, but the
nearest real overlap available), agree to within **$2.94/dmt** (-$81.44
vs. -$78.50). "TC is in extreme-negative territory" is not an
SMM-specific read.

## Cross-check: zinc (secondary, corroborating)

Zinc shows the same by-product-cushion mechanism, at an even more extreme
TC level: SMM's spot imported zinc TC hit an **all-time low of -$113/t**
in August 2026, against an $85/t annual benchmark, with Reuters reporting
zinc smelters leaning harder on silver and sulphuric-acid credits to
compensate. This corroborates the mechanism (by-product credits cushioning
collapsing TC across more than one metal) but is deliberately **not**
allowed to move this thesis's own dashboard — see Part Two for the full
zinc-vs-copper analysis, which remains this project's original, and now
secondary, thread.

## What would move this thesis next (the article's own watch list)

Three variables, carried through largely unchanged because they're
mostly still the right ones, with one clarified 2026-09-25: **the acid
credit itself; China's fertiliser export policy after the August 31
deadline SMM is watching; and whether the DRC/Zambia benchmark spread
holds once it has more than five weeks of data behind it** (see "Known
limitations" — a flat 5-week print on a 9-week-old benchmark is exactly
as consistent with a thin, untraded market as with genuine stability, and
this project does not resolve that ambiguity in either direction, and no
fresher print has appeared as of this update). TC does not need to move
again for this thesis to matter further: if it holds near its floor while
the acid cushion keeps eroding, the gap between an acid-advantaged
smelter and an exposed one widens on its own — and, as of 2026-09-24,
this is exactly what has happened.

**Clarification on the middle variable, added 2026-09-25:** the article's
"August 31 fertiliser deadline" and the acid-export collapse this project
actually tracks (China's H2SO4 exports, 116.7kt in May → ~980t in June,
staying near-zero into July) are two DIFFERENT Chinese export policies,
and worth not conflating. The August 31 date belongs to a ROUTINE,
ANNUAL phosphate-fertiliser (DAP/MAP) export-declaration control that
China runs every year from March 14 to August 31 — not something invented
for 2026. The sulphuric-ACID-specific export halt that actually drove the
H2SO4 collapse in this project's data is, per CRU's reporting (citing the
relevant government decree), in force from the start of May THROUGH THE
END OF 2026 — independent of the routine fertiliser deadline entirely.
On the narrower fertiliser question itself, evidence checked 2026-09-25
is mixed: an SMM flash note says the routine window is "expected to be
lifted" as usual from Sept 1; S&P Global Commodity Insights (2026-09-02)
reports fertiliser producers had received no official guidance on DAP/MAP
export resumption, with one trader thinking exports might not resume in
2026 at all. Net read: the article's third watch variable has not cleanly
resolved, but it was likely never the right lever on the acid glut
specifically — the acid halt runs on its own, longer, already-fixed
timeline regardless of what happens with fertiliser exports. That leans
the "cause of acid decline" dashboard category slightly toward
policy-driven/sticky, though it stays UNCLEAR overall (see the dashboard
table above) since this doesn't resolve the domestic-demand side of the
question at all.

## A real modeling gap, found and fixed while building this

The original `smelter_margin()` function folds in the smelter's FULL
payable-metal revenue (`metal_price × metal_grade × payable_fraction`) —
the right convention for an INTEGRATED mine+smelter like Kamoa, which
genuinely owns the metal outright, but a large overstatement for a
CUSTOM/TOLLING smelter (Freeport Miami, typical Chinese import
smelters), whose own margin the industry actually prices closer to **TC +
"free metal" + byproducts − costs** — which is exactly CRU's own
income-mix framing quoted above. Feeding the model's original,
metal-inclusive margin into this note's Residual Margin metric would have
buried the entire TC/acid signal in copper-price noise (metal revenue
alone runs into the thousands of $/t; TC is a few hundred). This project
now computes `treatment_margin()` — TC + free metal (the `1 -
payable_fraction` sliver only) + byproducts − costs — specifically for
the acid-cushion metrics above, while leaving the original
`smelter_margin()` untouched for the Kamoa-style integrated case and the
unchanged zinc-vs-copper secondary path. See `margin_model.py`'s
`treatment_margin()` docstring and README.md's 2026-09-16 changelog point
4 for the full account, including a runnable self-check
(`_selfcheck_residual_margin_additivity()`, `python margin_model.py`)
proving the margin-ex-acid / acid-contribution split is exact.

## Known limitations (this thesis specifically)

- **`copper_acid_data.py`'s weekly series mixes cited, cited-approx, and
  interpolated points** — every number in this note that names a specific
  week is `cited` in that module (check the `status` column before
  quoting a different week externally); the 9W/13W trend figures may
  reference an interpolated reference point even when the latest point
  itself is cited — see `model_a.py`'s `provenance_note`.
- **The absolute treatment-margin dollar figures inherit uncalibrated
  cost inputs** (`conversion_cost`, `premium`, and a flat, unsourced
  $70/MWh-equivalent energy-price placeholder — no free public series for
  Chinese industrial electricity was found). The direction (deteriorating
  through 2026) and the sensitivity to the acid channel (the stress-test
  table above) are the load-bearing outputs; treat "-$186/t" (the
  2026-09-24 reading) as "this shape and sign are real, this precision is
  not."
- **The DRC/Zambia regional benchmark is only ~9 weeks old** (launched
  2026-06-05) and its "unchanged for five consecutive weeks" print is
  reported here exactly as ambiguous as the source article treats it —
  consistent with genuine stability OR a thin market with no fresh
  transaction. Do not read "unchanged" as "stable" in any downstream
  summary of this note.
- **"Physical response: EMERGING, STRENGTHENING" rests on four pieces of
  evidence, not one** (SMM's TC-negotiation-resistance note, a reported
  July output decline, SMM's 2026-09-18 "production cut intentions
  emerging" language, and CSPT declining to set a Q4 TC guidance price on
  2026-09-24) **and none of them cleanly isolates the acid-cushion
  mechanism from plain concentrate scarcity** as the cause. Don't upgrade
  this to CONFIRMED without a smelter statement that actually says so.
- **This note's own `DEFAULT_CU_PARAMS`** (the representative-smelter
  calibration behind the treatment-margin figures) is the SAME set of
  parameters used throughout this project — `acid_yield` and
  `metal_grade` are cited (see Part Two's calibration notes);
  `payable_fraction`, `conversion_cost`, `energy_per_t` and `premium` are
  still rule-of-thumb. Kamoa's own numbers sidestep this entirely (they
  use Ivanhoe's own disclosed $/lb figures directly, not this project's
  calibration), which is exactly why the Kamoa case study above is this
  note's most load-bearing real-money evidence, not the DEFAULT_CU_PARAMS
  treatment-margin figures.
- **Added 2026-09-25 — the TC and acid figures throughout are SMM's
  published BENCHMARK index levels, not any specific real smelter's
  actual realized economics**, and this project does not net out
  freight, handling, storage, or VAT treatment between the SMM index and
  what a smelter actually books as revenue — none of these have a
  public, citable figure for this market, and this project does not
  fabricate one rather than leave the gap disclosed. The one place real,
  company-disclosed realized economics exist is Kamoa-Kakula, which is
  why it is kept as a separate case study rather than folded into the
  benchmark-model figures.
- **Added 2026-09-25 — Kamoa's own "Acid/OPEX coverage" ratio and the
  benchmark model's "Acid Cushion Ratio" (Acid ÷ \|TC\|) are
  methodologically different measurements** that used to share the same
  name in this note ("cushion ratio") — fixed; see the terminology note
  in the Kamoa case study above. Both narrow over the period covered
  here, which is the genuinely useful read, but they are not on the same
  scale and should not be quoted as if they were.

---

# Part Two: the original zinc-vs-copper thesis (secondary, preserved)

This is the project's original analysis, unchanged from before the
2026-09-16 pivot above except for this framing note. It remains useful
secondary/corroborating evidence (see "Cross-check: zinc," above) and an
honest record of how this project's thinking evolved — kept in full,
including its own correction note, rather than trimmed now that the
emphasis has moved to Part One.

## Correction note (2026-09-15)

A full code/data review on this date found several issues worth flagging
before anything below is quoted externally. None of them overturn the
core finding (acid price rising alongside, not falling with, TC weakness)
— but two of them change what can currently be claimed with confidence,
and are listed first for that reason:

1. ~~**`zn_price` is still 100% invented, not real, throughout this
   note.**~~ **RESOLVED 2026-09-16** (real data added) **and re-run
   2026-09-25** — `data/fred_zinc.csv` has since been downloaded and
   added; `real_data_check.py`'s `zn_price` column is now real for every
   quarter it covers. The dollar figures below (e.g. "roughly +100 $/t to
   zinc's margin change") were originally computed on the PREVIOUS,
   invented `zn_price` (2500 / 2450 / 2600 / 2750 / 3100 / 3050) and sat
   un-re-verified for over a week — including a derived "share of margin
   change" paragraph that carried the same staleness WITHOUT its own "see
   correction note" flag, and was consequently still wrong when actually
   checked. Both are now fixed in place (2026-09-25, by actually running
   `real_data_check.py`): the dollar figures are $106.8/t (zinc acid),
   $88.6/t (copper acid), -$110.0/t (zinc TC), -$90.0/t (copper TC); the
   share-of-margin-change figures are -25.4%/-7.2% (TC) and +24.6%/+7.1%
   (acid). The qualitative finding (acid positive, TC negative, acid
   dominating, zinc more geared than copper on both legs) did not flip —
   but the specific percentages had drifted further from the dollar
   figures than expected, which is exactly why "a caveat next to the
   dollar figures" isn't the same guarantee as "re-run before quoting
   anything downstream of them," and both are worth doing together.
2. **`threshold_gap`'s sign convention was documented backwards in
   `margin_model.py` (now fixed).** The arithmetic (`Acid*_Zn - Acid*_Cu`)
   was always correct; a positive gap has always meant zinc's curtailment
   trigger sits at a HIGHER (less negative) acid price than copper's,
   i.e. **zinc is the more exposed / earlier-curtailing metal** — which
   is directionally consistent with everything else in this note. The
   code comment describing that number previously said the opposite
   ("zinc curtails later"). If you have discussed `threshold_gap` in any
   conversation or draft based on the old comment, the conclusion you'd
   have drawn was inverted — re-check against the corrected docstring in
   `margin_model.threshold_gap()`.
3. **Two real, large, verified price shocks sit in or near this note's
   data window and have nothing to do with the acid/TC mechanism:**
   COMEX copper collapsed a record ~20-22% in a single session on
   2025-07-30 (a US Section 232 tariff-exemption unwind, after trading
   up to ~28-30% above LME for months on the arbitrage) and silver
   spiked to an all-time high near $121/oz on 2026-01-29 before crashing
   ~30%+ in about a day. Both are genuine market events, not data errors
   — but neither reflects smelter byproduct economics, and both need
   explicit handling (not a silent quarterly average) before any
   extension of this analysis into 2025-Q3 or a finer read of 2026-Q1.
   See `real_data_check.py`'s new `EVENT_WINDOW_NOTES` and
   `fetch_metal_prices_yfinance.py`'s docstring.
4. **`relative_acid_sensitivity`'s "robustness" across regional/TC
   variants (Model B) was previously tautological** — it's fixed by
   `SmelterParams.acid_yield` alone and can't vary with the data being
   swept. `model_b.py` now also reports an empirical (OLS-fit) version
   that genuinely can vary; re-run before citing a Model-B "robustness
   range" for this figure.
5. **The CNY-to-USD acid conversion used a flat 7.1 rate for every
   quarter 2023-2026 alike — now fixed (2026-09-16).**
   `real_data_check.py`'s `acid_price` column uses `copper_acid_data.
   cny_to_usd()`, a period-matched quarterly FX table, instead. USD/CNY
   moved from ~7.1-7.3 in 2023-2025 to ~6.7-7.0 by mid-2026, so the flat
   rate was understating 2026 acid prices in USD terms by roughly 5-8% —
   folded into the 2026-09-25 re-run referenced in point 1, above.

Everything below this point is the note as it stood before this review —
kept as-is except where a footnote marks a specific figure affected by
points 1-3 above, so the reasoning trail stays intact. Re-verify anything
with a "(see correction note)" marker before using it externally.

## What this is and isn't

This is a fundamentals-driven relative-value thesis with an explicit,
falsifiable monitoring checklist, meant to sit in a research note handed to
a PM or desk. It is not a systematic trading strategy. The distinction
matters beyond style: the best available public data for this thesis
(ILZSG, ICSG, company filings) is monthly or quarterly, so a daily
backtest would mostly be measuring interpolation noise, not the mechanism.
Where the code has daily-shaped scaffolding (`thesis_monitor.py`'s rolling
windows), it exists to be walked through by a person each time new
monthly/quarterly data lands — not run unattended. (Part One's copper
acid-cushion thesis inherits this same discipline — `thesis_dashboard.py`
is a checklist for a written view, not a signal generator, same as
`thesis_monitor.py` always was.)

## The mechanism, restated

Declining sulfuric-acid by-product economics were hypothesised to create a
larger marginal smelter-margin shock for zinc than copper, because TC
collapse and acid-price weakness were assumed to hit smelters together.
Full mechanism in `README.md`; the margin formula and curtailment-threshold
logic are in `margin_model.py`.

One part of this was checked against real data before any code was
written and holds up well: **copper TC/RC genuinely went to zero/negative
in 2025-2026** (Antofagasta's 2026 benchmark settled near $0/t; spot
prints have gone as low as roughly -$200/t by September 2026 — see Part
One). That part of the foundation is solid.

## The finding that changes the thesis: acid price moved the WRONG way

The thesis assumed acid price would decline alongside TC, compounding the
squeeze. Checked against real 2024-2026 reporting, **the opposite
happened**: China 98% sulfuric acid rose from roughly 375 yuan/t (2024
average, implied) to ~688 yuan/t (2025 average, +83% y/y — SunSirs, Mar
2026), and kept climbing into 2026 — SMM's own China Copper Smelting Acid
Index rose from RMB 919.5/t at the start of 2026 to a peak near RMB
1,789/t in early July (see `copper_acid_data.py` for the full weekly
series). Industry language for what this did to smelter economics is
explicit and consistent across sources: acid became a **"profit
lifeline"** for copper smelters, a **"cash flow buffer"** offsetting
negative TCs (SunSirs, Mar 2026; procurementresource.com, Jul 2026), and
Fastmarkets reported in June 2026 that Chinese zinc smelters were *still*
not cutting output despite TC concerns specifically because **"byproduct
gains from sulfuric acid have still lent strong support to smelters'
margins."** *(Part One picks up exactly where this leaves off: that
cushion itself started narrowing from July 2026 — this is not a
contradiction of the finding below, it's the next chapter of it.)*

The mechanism driving this makes sense once you see it: TC collapse and
the acid-price surge share the same root cause (concentrate/ore scarcity
constraining how much smelters can run), but they hit smelter revenue with
**opposite signs**. Less concentrate processed industry-wide means less
by-product acid supply reaching the market; acid demand (fertiliser,
metal-leaching) didn't fall with it, so acid price rose — and that higher
price cushions exactly the smelters whose TC income was just cut. This is
a genuine natural hedge in the current regime, not a modelling artefact —
`real_data_check.py`'s exact margin-bridge decomposition (linear, no
approximation error in the arithmetic itself) on 2024-Q1 → 2026-Q2 inputs,
using `acid_yield` values now derived from cited industry stoichiometry
rather than invented (see `model_a.py`'s calibration notes), shows the
acid channel contributing **+$106.8/t to zinc's margin change and +$88.6/t
to copper's** *(re-verified 2026-09-25 by actually running
`real_data_check.py` on real data — see this note's changelog. The prior
draft flagged these as needing a re-run on real `zn_price`/FX rather than
the original invented placeholder and flat FX rate; that re-run is now
done and these are the real-data figures, not rounded placeholders)*,
both positive, while TC contributed **-$110.0/t (zinc) and -$90.0/t
(copper)** — acid offsetting close to all of TC's drag on zinc and most
of it on copper. The arithmetic is exact, and `acid_yield` is now a cited
figure (~2 t acid/t zinc metal per AusIMM; 3.0-3.5 t acid/t copper metal
per a 2026 industry review — see `model_a.py`), but `payable_fraction`,
`conversion_cost`, `energy_per_t`, `premium` and both by-product-yield-
adjacent inputs stay rule-of-thumb or invented, and several of the
real-data price points are interpolated between cited dates rather than
cited themselves (see `real_data_check.py`'s header comment for exactly
which cells are which) — so treat the **direction and order of magnitude**
as the load-bearing finding, not the fourth significant figure.

This does not kill the underlying asymmetry, but it changes its shape.
As a *share of each metal's own total margin change* over the same window,
TC's drag is proportionally larger for zinc (**-25.4%**) than for copper
(**-7.2%**), and so is acid's offset (**+24.6%** vs **+7.1%**) — zinc's
margin is structurally more geared to both channels, because its baseline
metal-revenue cushion is thinner relative to copper's. **Fixed 2026-09-25:
this paragraph previously read "-44%/-15%, +41%/+14%"** — figures computed
under the same old invented-`zn_price`/flat-FX run flagged above, but
(unlike the dollar figures right above them) never explicitly marked as
needing a re-run, so they sat here for over a week reading as validated
when they weren't. On the actual re-run, the total margin-change
denominator each ratio divides by moved by more than the acid/TC dollar
figures did (real `zn_price` swung further than the old placeholder), so
the SHARE figures changed more than the dollar figures did, even though
the underlying dollar-figure caveat covered both. The direction of the
asymmetry (zinc more geared than copper, on both legs) is unchanged and
still real; only the specific percentages were wrong. That's a real,
quantifiable asymmetry, and it is now reinforced by a second, independent
one: with `acid_yield` corrected to real stoichiometric ratios, zinc's
acid sensitivity (`acid_sensitivity_zn`, $ per $ of acid price, per tonne
of concentrate) comes out genuinely **larger** than copper's
(`relative_acid_sensitivity` = +0.17, not the small negative number the
first, invented-parameter draft produced) — zinc concentrate really does
generate more acid per tonne processed, relative to its own metal payable
fraction, than copper concentrate does. That structural claim is now
grounded in cited industry ratios, not assumed — and is a STRUCTURAL
number (fixed by `SmelterParams.acid_yield` alone), not something that
varies with market data; see correction note point 4 and `model_b.py`'s
new empirical companion figure for what a genuine data-driven robustness
check on this asymmetry looks like. It is still a different claim from
"zinc curtails first because acid is disappearing" — right now acid is
doing the opposite of disappearing, and the more defensible near-term
framing is: **zinc margin is the more volatile of the two to any given TC
or acid move, in either direction** — not "zinc is one acid-price leg away
from curtailment," and (per correction note point 2) a positive
`threshold_gap` is the number that actually says zinc is the
earlier-curtailing metal, once read with the corrected sign convention.

**Revised risk scenario worth watching, precisely because of this:** the
setup that would actually validate the original "long zinc / short
copper" thesis is not "TC stays low" (already true, already priced into
this cushion) but **acid price reversing down while TC stays weak** — e.g.
if Chinese smelters chase volume/state directives despite negative TCs
(as copper smelters were reported doing in 2024, per `README`'s original
research) and flood the acid market even while processing lower-grade,
lower-payable concentrate. **This is, almost exactly, what Part One now
documents happening on the copper side from July 2026** — the scenario
this section flagged as "the actual thing to monitor for" is the current
state of the market, which is exactly why this project's emphasis moved.

## Historical case studies (not a backtest — see "What this is and isn't")

**2021-2022, European zinc smelters, energy channel.** Nyrstar cut output
by up to 50% at its Budel (Netherlands), Balen (Belgium) and Auby (France)
zinc smelters from October 2021, citing electricity costs that had risen
several-fold; Budel was later placed on full care-and-maintenance in
September 2022. Macquarie estimated energy had gone from roughly 50% to
80% of European zinc production cost over the same period (S&P Global,
Oct 2021; Mining Weekly / Argus / Euronews, 2022). This validates the
**curtailment-threshold mechanism itself** — a real smelter really did
shut down once a specific cost line pushed margin to an unviable level —
but through the **energy** term in `SmelterParams`, not the acid term.
Useful evidence that `curtailment_threshold()`'s zero-margin logic
describes something real; not evidence about the acid channel specifically.

**2024-2026, Chinese zinc/copper TC collapse, acid channel — live, and
now (per Part One) starting to resolve.** This is the actual test of the
acid-specific mechanism. Through mid-2026, Chinese zinc and copper
smelters largely did **not** curtail despite TC weakness, and said so
explicitly, citing acid support (Fastmarkets, Jun 2026). By Q3 2026, per
Part One, the acid side of that support is itself under real pressure,
and the first EMERGING (not yet CONFIRMED) signs of physical response are
visible. Read plainly: **the acid-credit-divergence trade did not fire on
the original schedule, the public data explained why at the time, and
that same public data is now the earliest evidence for what might make it
fire next** — a more useful and more honest arc than a synthetic backtest
that fires on schedule because the fixture was built to make it fire.

**2025, US copper tariff arbitrage and unwind — a reminder that price
proxies carry their own regime risk (added 2026-09-15).** Not a case
study for the acid mechanism, but worth recording here for the same
"validate against something real" discipline: COMEX copper traded up to
~28-30% above LME for several months in 2025 on a Section 232
tariff-arbitrage premium, then collapsed a record ~20-22% in a single
session on 2025-07-30 when refined copper was excluded from the tariff.
This project sources `cu_price` from COMEX (`HG=F`) throughout — a
reasonable, standard proxy in normal conditions, but one that visibly
decoupled from the global (and specifically Chinese-smelter-relevant)
copper price for months in exactly this window. See correction note
point 3.

## Is the 5-condition filter too strict?

Yes, on the evidence available. `demo.py`'s synthetic fixture was
deliberately built to make the thesis play out (TC collapsing, acid
falling, zinc production/stocks weakening in tandem) — the friendliest
possible case for the filter. Even there, `conditions_met_distribution()`
shows all 5 conditions aligning on **0% of the 730-day sample**; 4/5 is
the most it ever reaches, and only briefly. The strict AND-of-5
`thesis_confirmed` flag is not a usable trigger even in a fixture rigged
in its favour — it is a ceiling, not a switch. `conditions_met` (the 0-5
count) should be the primary output a strategist reads, with something
like ≥4/5 read as high conviction and ≥3/5 as "worth a fresh look" —
calibrated against how the distribution behaves on real data once enough
of it is assembled, not against an arbitrary "all must agree" bar chosen
in advance. `thesis_monitor.narrative_summary()` already reports the count
for this reason; treat the all-5 case as a reference point, not the bar.
**This count is a research-note input, never a "trade active/inactive"
flag — see `README.md`'s changelog for a stale output file that briefly
blurred that distinction in this project's own `output/` folder.** (Part
One's Thesis Dashboard takes a different shape for exactly this same
reason, applied to a thesis whose inputs are more genuinely
mixed/qualitative than pass/fail — see its own introduction, above.)

## Data path forward

Two options were on the table: hand-collect real figures, or automate
metal prices. Practical constraint worth being direct about: this
project's execution sandbox has no network access to Yahoo Finance, FRED,
the World Bank, ILZSG, or ICSG — only package registries (PyPI, npm,
GitHub). So none of the automated fetching can run *here* — every one of
the paths below needs to run on your own machine.

**Copper and silver: `fetch_metal_prices_yfinance.py`, verified reliable
— done, and current through 2026-09-16.** Daily, continuous, no flat runs
on a real pull. `HG=F` needed a unit fix (USD/lb → USD/tonne); `SI=F` was
already correct. `data/metal_prices.csv` covers 2023-01-03 through
2026-09-16 — this is genuinely real data, confirmed against two
independent, large single-day moves in it (see correction note point 3)
that both check out against contemporaneous public reporting.

**Zinc: FRED's `PZINCUSDM`, not yfinance — resolved 2026-09-16.** The
original plan mirrored copper/silver — COMEX via yfinance. Ticker `ZN=F`
turned out to be the CBOT 10-Year Treasury Note future, not zinc, and the
corrected ticker `ZNC=F` turned out to be essentially untraded: frozen at
one settlement price for 93% of a real 2023-2026 pull, with 5 of 6
quarters this project uses showing exactly one unique value for the
entire quarter. Switched to FRED's `PZINCUSDM` (IMF "Global price of
Zinc," monthly, verified real, no unit conversion needed) instead — a
genuine benchmark series, not a thin futures print, and a MORE credible
source for a fundamentals thesis note than a thinly-traded futures
contract would have been anyway. `data/fred_zinc.csv` is now present and
`zn_price` is real for every quarter `real_data_check.py` covers.

Sulfuric acid and TC still can't be automated from any free API regardless
of environment — no source publishes them that way — so company filings
and industry/SMM reporting stay the calibration method for those two
regardless of what happens with metal prices. That's the real ceiling on
how "live" this thesis can ever get: metal prices can be fully real and
low-effort to refresh; the two variables the mechanism actually runs on
cannot, on any current free source, and every weekly TC/acid figure in
this project (Part One included) was hand-transcribed from a named public
article, not fetched.

**What changed once metal prices were actually real, not invented:**
`real_data_check.py`'s acid/TC "share of total change" figures shift once
real copper price appreciation replaces the old invented estimate —
copper's own metal-price channel turns out to dominate its margin change
even more than previously modelled (its 2024-Q1→2026-Q2 real price move
was larger than the round number this note originally assumed), which
*sharpens* the zinc-vs-copper asymmetry (zinc structurally more exposed
to the acid/TC channels as a share of its own margin move) rather than
softening it. **RESOLVED 2026-09-25**: the figures in "The finding that
changes the thesis," above, previously still reflected the OLD invented
`zn_price` and the OLD flat FX rate (correction note points 1 and 5) —
they have now actually been re-run and corrected in place (dollar figures
and share-of-margin-change percentages both), rather than left flagged
as pending. See correction note point 1 for the specific before/after
numbers.

## Known limitations (thesis-level, not code-level — see README.md for those)

* **Frequency mismatch.** TC and acid data are realistically quarterly at
  best for zinc (weekly for copper as of Part One — see
  `copper_acid_data.py`); metal prices are daily. Any framework mixing
  them (this one included) is only as frequent as its slowest input for
  the parts of the mechanism that matter most.
* **`SmelterParams` is now partially calibrated, not uniformly
  placeholder — know which parts are which.** `acid_yield` (both metals)
  and copper's `metal_grade` are now cited (industry acid-per-tonne-metal
  ratios; Freeport's real 2025 Miami concentrate-to-anode figures) —
  see `model_a.py`'s calibration comment for the exact sources and
  arithmetic. `payable_fraction`, `conversion_cost`, `energy_per_t`,
  `premium`, `silver_yield_oz`, `gold_yield_oz`, and zinc's `metal_grade`
  are still rule-of-thumb or invented. Before citing anything externally,
  finish the job: calibrate the remaining fields from Nexa's 20-F/6-K
  (zinc) and Freeport's 10-K (copper) via
  `data_loaders.load_company_filing_byproducts` — company-specific
  figures, not industry-wide ratios, for the parameters that still need it.
* ~~**CNY-to-USD acid conversion in `real_data_check.py` uses a single
  rounded FX rate for all periods**~~ — **FIXED 2026-09-16**, see
  correction note point 5.
* **Chinese policy-driven curtailment (environmental inspections, power
  rationing during heatwaves, CSPT-coordinated "voluntary" cuts) is not in
  the margin model at all**, and per the sources above has been at least
  as important a driver of actual Chinese smelter behaviour as pure
  economics in 2024-2026. A margin threshold being crossed and a
  government-mandated cut are different triggers with different timing,
  and the current framework cannot distinguish which one caused an
  observed curtailment. (This applies equally to Part One's "physical
  response" dashboard category — EMERGING evidence there could reflect
  either mechanism, and the framework can't yet tell which.)
* **The 2021-2022 European case study validates the general
  curtailment-threshold mechanism, not the acid channel specifically** —
  see the case-study section above; don't cite it as acid-specific
  evidence.
* **`real_data_check.py`'s TC and acid cells mix genuinely-sourced values
  with interpolated, invented, and (new, 2026-09-16) derived-from-
  `copper_acid_data.py` values in the same table without visually
  distinguishing them in the printed table itself** — the file's header
  comment lists exactly which is which. `energy_price` for the original
  six quarters is still invented, plausible round numbers; the two new
  2026-Q1/Q3 quarters use the same flat $70 placeholder Part One's
  primary pipeline uses (previously NaN — see README.md's changelog
  point 7 for why that was a worse default, not a more honest one).
  Rebuild the TC/acid side properly — separate benchmark-vs-spot TC
  series, and an explicit source/confidence tag per cell in the printed
  table, not just the header comment — before using it externally.
* **The five-condition monitoring framework (`thesis_monitor.py`) has only
  ever been run on the synthetic fixture, never on real data.** The real
  dataset's quarters are irregularly spaced and indexed by quarter
  labels, not real dates — `build_monitor()`'s rolling windows can't run
  on it as-is. We know the filter is over-conjunctive on synthetic data
  (see above); we don't yet know how it behaves on the real, sparse,
  gappy cadence this thesis will actually be monitored at.
* **`margin_bridge()` holds `SmelterParams` fixed across both dates being
  compared** — it can't capture a smelter's own technical parameters
  (feed blend, acid recovery rate) changing over a 2+ year window,
  only price/TC/cost-driven change at constant technical efficiency.
* **The recommended `conditions_met` thresholds (≥4 = high conviction, ≥3
  = worth a look) are a reasonable-sounding heuristic, not a calibrated
  one** — calibrating them properly needs a real monitor history, which
  doesn't exist yet per the point above.
* **`curtailment_threshold()`'s current default calibration produces Acid*
  values far outside any realistic observed acid price** (roughly -1000
  to -2600 $/t in the demo, versus a real observed range of roughly
  $40-250/t) — see `margin_model.py`'s docstring. Until `SmelterParams`'s
  remaining uncalibrated fields are tightened, read a deeply-out-of-range
  Acid* as a calibration flag, not a finding, and treat
  `thesis_monitor.condition_2`'s "acid price crossed Acid*" branch as
  close to structurally unreachable for now. (Part One sidesteps this
  specific problem for the Kamoa case study by using
  `implied_acid_yield_and_buffer()`, which derives its own implied yield
  from Kamoa's own disclosed numbers rather than trusting
  `SmelterParams.acid_yield` — see "A real modeling gap," above.)

## Changelog — 2026-09-25

A second review pass extended Part One's data three weeks (to
2026-09-24), found and fixed two real code bugs that the extension
exposed, fixed two methodological/labelling issues, and fixed one stale,
previously-unflagged figure in Part Two. Full technical detail (the two
bugs, the exact citations for the new data points, and which parts of an
external review's larger refactor proposal were adopted vs. declined and
why) is in `README.md`'s own 2026-09-25 changelog — not duplicated here
in full. Summary of what changed in THIS document specifically:

- **Part One's entire "current read" section** (headline table, trend,
  stress test, dashboard, Kamoa comparison, robustness section)
  **updated from the 2026-09-04 snapshot to 2026-09-24** — most
  consequentially, the Acid Cushion Ratio fell from 94.3% to 68.2% in
  three weeks, a materially faster deterioration than the prior snapshot
  alone suggested.
- **"What would move this thesis"** now distinguishes the sulphuric-acid
  export halt (through end-2026, per CRU/decree reporting) from the
  source article's "August 31 fertiliser deadline," which turns out to be
  a different, routine, annual policy — evidence on the fertiliser
  question itself stayed mixed as of this check.
- **Kamoa's "cushion ratio" relabelled "Acid/OPEX coverage"** throughout,
  to stop implying it's the same measurement as the benchmark model's
  Acid ÷ \|TC\| ratio (it divides by a different, broader denominator).
- **Correction note point 1, and the "finding that changes the thesis"
  paragraph it flagged, resolved**: both the dollar figures AND a
  derived "share of margin change" paragraph that had been carrying the
  same staleness without its own flag are now re-run and corrected in
  place (-44%/-15%/+41%/+14% → -25.4%/-7.2%/+24.6%/+7.1%; the direction
  of the underlying zinc-more-geared-than-copper asymmetry did not
  change, only the specific percentages).
- Two new "known limitations" bullets added: the benchmark model's TC/
  acid figures are SMM benchmark index levels, not any specific
  smelter's realized/net-of-freight-and-VAT economics (Kamoa's own
  disclosure is the one place real realized economics exist in this
  project); and the Kamoa-vs-benchmark ratio-naming fix above.

**What an external review's larger refactor proposal got right, and
what this pass declined, and why:** see README.md's 2026-09-25
changelog for the full reasoning — in short, the two concrete bugs it
flagged (the interpolation grid, the Model B vintage mismatch) were
real and are fixed; its proposal to net a virgin-sulfur feedstock cost
against the copper smelter's own acid credit was declined as a genuine
conceptual error (copper smelters produce acid from SO2 already captured
from concentrate they're smelting anyway, at near-zero marginal
feedstock cost — that's the entire reason the acid credit is such a
powerful cushion; buying market sulfur is a different business); its
proposed binary margin-triggers-shutdown curtailment rule was declined
as directly contradicting this note's own "Known limitations" point on
policy-driven curtailment, above; and its larger architecture proposals
(machine-readable provenance objects, a generic vintage-access layer,
automated ingestion/CI, a dashboard) were judged disproportionate to
what this project actually is — a strategist's research note, not a
production trading-desk data platform — and would have required
fabricating inputs (freight, VAT, utilization-elasticity coefficients)
this project has no public source for.

## Changelog — 2026-09-26

A third review pass against five specific follow-up points on the
2026-09-25 fixes above, plus a separate, directly-raised gap in the
project's chart outputs. Full technical detail is in README.md's own
2026-09-26 changelog; summary of what changed in THIS document:

- **Acid-yield sensitivity table added** to "The current read," above —
  the headline Acid Cushion Ratio (68.2%) moves between 62.9% and 73.3%
  across the full cited plausible range of `acid_yield` (0.765-0.8925);
  the qualitative finding (a 26-point collapse from three weeks earlier)
  is not sensitive to this specific assumption. Previously this was an
  unquantified caveat, not a measured answer.
- **The 9-week trend figures' reference point (2026-07-24) is disclosed
  as interpolated, not cited** — the 1-month/3-month/13-week figures'
  reference points are all real prints; only the 9-week ones weren't
  flagged either way before this pass.
- **A real, previously-unguaranteed vintage-safety gap in
  `copper_acid_data._interpolate_to_grid()` fixed**: the 2026-09-25
  fix's off-grid snap used `nearest`, which could in principle (never
  actually triggered by this file's real data) pull a citation dated
  AFTER a grid label backward onto that earlier label. Replaced with
  backward-only ("last observation dated <= this date") alignment, with
  a regression test constructing the failure case synthetically. This
  is a code-correctness fix with no effect on any number printed in this
  note — the underlying data never exercised the bug.
- **A real-data chart added**: `output/copper_acid_cushion.png` (TC vs
  acid price, and the Acid Cushion Ratio, both over the real weekly
  grid), regenerated automatically on every `acid_cushion_monitor.py`
  run. Before this, every chart in the project was `demo.py`'s
  deliberately synthetic pair — real, honestly labelled, but the only
  visual artifact a reviewer had to look at. `demo.py` itself was not
  changed to use real data (it exists specifically as a zero-dependency
  smoke test and should keep doing that job); its chart TITLES were
  fixed instead, since only one of three previously said "synthetic" —
  see README.md's changelog for the full reasoning on why converting
  `demo.py` itself would have been the wrong fix.