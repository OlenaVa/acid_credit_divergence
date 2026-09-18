"""
demo.py
=======
SECONDARY / cross-metal pipeline smoke test, using SYNTHETIC data (clearly
labelled as such) for the zinc-vs-copper analysis (model_a.run_model_a,
model_b.run_model_b, model_c.run_model_c). Confirms that pipeline runs
end-to-end before plugging in real public data via real_data_check.py.

For the project's PRIMARY output -- the copper acid-cushion thesis, on
REAL weekly SMM data through this project's data-collection date -- run
`python acid_cushion_monitor.py` instead. That pipeline needs no synthetic
fixture: copper_acid_data.py's cited real series IS its input, so there is
no "demo" version of it to smoke-test separately from the real thing.

The synthetic series below roughly follow the qualitative shape the
ORIGINAL version of this project's thesis assumed (TC collapsing
2024-2026, acid price falling too) -- NOT what real_data_check.py and
copper_acid_data.py actually found happened (acid ROSE sharply through
most of 2024-2026, then narrowed from an elevated level starting mid-2026
-- see STRATEGY_NOTE.md). That mismatch is fine, even expected: this file
exists ONLY to prove the zinc/copper code paths execute correctly, not to
model real dynamics -- treat every number below as a pipeline smoke test,
never as a market claim.

Run:
    python demo.py
Outputs (in ./output/):
    demo_margins.png, demo_monitor.png, model_abc_comparison.csv

REVIEW NOTE (2026-09-15): this run now (1) deletes the stale, pre-rename
`output/demo_signal.png` artifact on every run (see _clean_stale_outputs
below -- README.md's "Known limitations" already warned this file could
linger and be mistaken for current output; it was found still present),
and (2) prints an explicit reminder at the end that every number here is
synthetic, because `output/model_abc_comparison.csv`'s "A (core, public
data)" label describes methodology (public vs proprietary data SOURCES),
not "this run used real prices" -- it's easy to conflate the two at a
glance. For real-data numbers, run real_data_check.py instead.
"""

import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from margin_model import SmelterParams
from model_a import run_model_a, DEFAULT_ZN_PARAMS, DEFAULT_CU_PARAMS
from model_b import run_model_b, run_cost_stress
from model_c import run_model_c, compare_a_b_c
from thesis_monitor import MonitorConfig, narrative_summary, conditions_met_distribution

# Pre-rename artifacts that must never linger next to current output --
# see thesis_monitor.py's docstring for why "signal" framing was dropped.
_STALE_OUTPUT_FILES = [
    "output/demo_signal.png",
]


def _clean_stale_outputs():
    for path in _STALE_OUTPUT_FILES:
        if os.path.exists(path):
            os.remove(path)
            print(f"Removed stale artifact: {path}")


def make_synthetic_data(n=730, seed=7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    t = np.linspace(0, 1, n)

    zn_price = 2600 + 400 * np.sin(2 * np.pi * t * 1.3) + rng.normal(0, 25, n).cumsum() * 0.02
    cu_price = 9000 + 1800 * t + rng.normal(0, 60, n).cumsum() * 0.02

    # TC collapsing over the period, per the note's description of 2024-2026
    zn_tc = 150 - 130 * t + rng.normal(0, 8, n)
    cu_tc = 80 - 85 * t + rng.normal(0, 6, n)

    # acid price under downward pressure with regional-style noise
    acid_price = 350 - 120 * t + rng.normal(0, 20, n)

    silver_price = 28 + 6 * t + rng.normal(0, 0.6, n)
    energy_price = 70 + 10 * np.sin(2 * np.pi * t * 2) + rng.normal(0, 3, n)

    zn_production = 1000 - 60 * np.clip(t - 0.5, 0, None) * 100 + rng.normal(0, 8, n).cumsum() * 0.05
    zn_stocks = 200 - 90 * np.clip(t - 0.4, 0, None) + rng.normal(0, 5, n).cumsum() * 0.05
    cu_stocks = 180 - 20 * t + rng.normal(0, 5, n).cumsum() * 0.05

    df = pd.DataFrame({
        "zn_price": zn_price, "cu_price": cu_price,
        "zn_tc": zn_tc, "cu_tc": cu_tc,
        "acid_price": acid_price, "silver_price": silver_price,
        "energy_price": energy_price,
        "zn_production": zn_production, "zn_stocks": zn_stocks, "cu_stocks": cu_stocks,
    }, index=dates)
    return df


def make_regional_acid_variants(base_acid: pd.Series, seed=11) -> dict:
    rng = np.random.default_rng(seed)
    regions = ["guangxi", "fujian", "jiangsu", "shandong", "hubei"]
    out = {}
    for r in regions:
        offset = rng.normal(0, 15)
        noise = rng.normal(0, 12, len(base_acid))
        out[r] = (base_acid + offset + noise).rename(r)
    return out


def make_tc_variants(df: pd.DataFrame, seed=13) -> dict:
    rng = np.random.default_rng(seed)
    benchmark = df[["zn_tc", "cu_tc"]].copy()
    spot = benchmark.copy()
    spot["zn_tc"] = spot["zn_tc"] - 40 + rng.normal(0, 10, len(df))
    spot["cu_tc"] = spot["cu_tc"] - 90 + rng.normal(0, 15, len(df))
    return {"benchmark": benchmark, "spot": spot}


def main():
    os.makedirs("output", exist_ok=True)
    _clean_stale_outputs()

    df = make_synthetic_data()

    # Demo-only smelter parameters: thinner copper margin than the module
    # defaults so the synthetic 2025-26 TC/acid squeeze actually reaches the
    # curtailment threshold within the plotted window (illustrative only --
    # calibrate the real DEFAULT_ZN_PARAMS / DEFAULT_CU_PARAMS from filings).
    demo_zn_params = SmelterParams(**{**DEFAULT_ZN_PARAMS.__dict__})
    demo_cu_params = SmelterParams(**{**DEFAULT_CU_PARAMS.__dict__, "premium": 0.0, "conversion_cost": 420.0})

    # ---- Model A ----
    result_a = run_model_a(df, zn_params=demo_zn_params, cu_params=demo_cu_params)
    print("=== MODEL A (core) -- SYNTHETIC demo data ===")
    print(f"Relative acid sensitivity (Zn - Cu): {result_a['relative_acid_sensitivity']:.3f}")
    print(f"Mean threshold gap (Acid*_Zn - Acid*_Cu): {result_a['threshold_gap'].mean():.1f}")
    print()
    print(narrative_summary(result_a["monitor"]))
    print("\nHow strict is the all-5 filter, empirically? Distribution of conditions_met:")
    print(conditions_met_distribution(result_a["monitor"]))

    # ---- Model B ----
    regional_acid = make_regional_acid_variants(df["acid_price"])
    tc_variants = make_tc_variants(df)
    result_b = run_model_b(df.drop(columns=["acid_price", "zn_tc", "cu_tc"]), regional_acid, tc_variants,
                            zn_params=demo_zn_params, cu_params=demo_cu_params)
    print("\n=== MODEL B (robustness) stability summary ===")
    for k, v in result_b["stability"].items():
        print(f"{k}: {v}")

    cost_stress = run_cost_stress(df, zn_params=demo_zn_params, cu_params=demo_cu_params)
    print("\nCost stress test (+0/5/10/20% conversion & energy cost):")
    print(cost_stress)

    # ---- Model C (no proprietary data supplied -> falls back to Model A, labelled) ----
    result_c = run_model_c(df, zn_params=demo_zn_params, cu_params=demo_cu_params)
    print("\n=== MODEL C (industry benchmark layer) ===")
    print(f"Used proprietary series: {result_c['used_proprietary_series'] or 'none (identical to Model A)'}")

    comparison = compare_a_b_c(result_a, result_b["stability"], result_c)
    comparison.to_csv("output/model_abc_comparison.csv", index=False)
    print("\n=== A vs B vs C comparison ===")
    print(comparison.to_string(index=False))

    # ---- plots ----
    fig, ax = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    ax[0].plot(result_a["sm_zn"].index, result_a["sm_zn"], label="Zinc smelter margin")
    ax[0].plot(result_a["sm_cu"].index, result_a["sm_cu"], label="Copper smelter margin")
    ax[0].axhline(0, color="grey", lw=0.8)
    ax[0].set_title("Representative smelter margin, Zn vs Cu (synthetic demo data)")
    ax[0].legend()

    ax[1].plot(df.index, df["acid_price"], label="Acid price (national proxy)", color="tab:red")
    ax[1].plot(result_a["acid_star_zn"].index, result_a["acid_star_zn"], "--", label="Acid* (Zn curtailment threshold)")
    ax[1].plot(result_a["acid_star_cu"].index, result_a["acid_star_cu"], "--", label="Acid* (Cu curtailment threshold)")
    ax[1].set_title("Sulfuric acid price vs estimated curtailment thresholds")
    ax[1].legend()
    plt.tight_layout()
    plt.savefig("output/demo_margins.png", dpi=130)
    plt.close(fig)

    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.fill_between(result_a["monitor"].index, 0, result_a["monitor"]["conditions_met"], step="mid", alpha=0.5)
    ax2.axhline(5, color="red", lw=1, ls="--", label="all 5 conditions confirmed")
    ax2.set_title("Thesis-monitoring conditions met over time (0-5) -- a research-note input, not a trading signal")
    ax2.legend()
    plt.tight_layout()
    plt.savefig("output/demo_monitor.png", dpi=130)
    plt.close(fig2)

    print("\nSaved: output/demo_margins.png, output/demo_monitor.png, output/model_abc_comparison.csv")
    print(
        "\n*** REMINDER: every number above comes from demo.py's SYNTHETIC fixture "
        "(make_synthetic_data()), including output/model_abc_comparison.csv. It proves "
        "the pipeline runs; it is NOT evidence about real markets, and 'A (core, public "
        "data)' describes data-source METHODOLOGY, not 'this run used real prices'. For "
        "real-data numbers on the zinc-vs-copper cross-metal check, run real_data_check.py "
        "(and make sure data/fred_zinc.csv and data/metal_prices.csv are both present "
        "first). ***"
    )
    print(
        "\n*** For this project's PRIMARY output -- the copper acid-cushion thesis on "
        "REAL weekly SMM data through this project's data-collection date -- run "
        "`python acid_cushion_monitor.py` instead. That pipeline needs no synthetic "
        "fixture and is not demonstrated by this file. ***"
    )


if __name__ == "__main__":
    main()
