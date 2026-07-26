"""ERCOT-116 scorer: seasonal-SHAPE gates for the coal-availability joint arm.

Scores the ERCOT-116 arm (measured coal DAM availability on the ercot115
keeper) against the criteria fixed in
``results/calibration/PRECOMMIT-ercot116-coal-avail-on-keeper-2026-07-26.md``
BEFORE any arm year was solved (rule 1). The gates are SHAPE gates: the
ERCOT-116 charter forbids re-gating on annual level ("the annual level is
already right, and gating on it again will just re-refute a mechanism that is
aimed at a different defect") — annual ratio and C1-style level impact are
REPORTED, never gated.

* **G1 (PRIMARY)** — the matched-price-band excess seasonal lift
  (``a2_matched_price_bands`` headline: model summer-minus-shoulder utilization
  lift minus actual, mean over the 8 fixed absolute price bands) must fall by
  >= 5.0 pp vs the keeper in EVERY year.
* **G2** — the monthly-ratio seasonal spread (Jun-Sep mean monthly coal ratio
  minus Feb-Apr mean) must narrow vs the keeper in EVERY year, with mean
  narrowing across the three years >= 0.10.
* **G3** — scarcity not degraded (same numerics as ERCOT-112 P2b / ERCOT-115
  P2): C3a no worse than the keeper by > 2.0 pp in any year, C3c no worse by
  > 5 hours in any year.
* **BITE** — annual coal TWh differs from the keeper by > 0.5 TWh in at least
  one year (armed-but-inert voids the probe).

All model series come from committed ``hourly/`` sidecars (rule 15 — no
re-solve); the metric implementations are imported from the ERCOT-112/113/114
probe scripts verbatim so every number is directly comparable to the published
ones.

Usage:
    python scripts/probes/ercot116_seasonal_shape.py \
        --keeper results/calibration/ercot115_coal_floor_only \
        --arm    results/calibration/ercot116_coal_avail_on_keeper
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from ercot112_score_coal_arms import year_row  # noqa: E402
from ercot113_summer_coal_decomp import SUMMER, year_table  # noqa: E402
from ercot114_coal_quantity_drivers import a2_matched_price_bands  # noqa: E402

YEARS = (2023, 2024, 2025)
FEB_APR = (2, 3, 4)

# Pre-committed thresholds — fixed in the ERCOT-116 pre-commit doc, never
# re-tuned here.
_G1_MIN_EXCESS_DROP_PP = 5.0
_G2_MIN_MEAN_NARROWING = 0.10
_G3_C3A_MAX_DEGRADE_PP = 2.0
_G3_C3C_MAX_DEGRADE_HOURS = 5
_BITE_MIN_TWH = 0.5


def matched_band_excess(bundle: Path, year: int) -> float | None:
    """Mean summer-minus-shoulder utilization-lift excess (model - actual), pp."""
    tab = a2_matched_price_bands(bundle, year)
    if tab is None:
        return None
    both = tab.dropna(subset=[("act_util", "summer"), ("act_util", "shoulder")])
    act = 100.0 * (both[("act_util", "summer")] - both[("act_util", "shoulder")]).mean()
    model = 100.0 * (
        both[("model_util", "summer")] - both[("model_util", "shoulder")]
    ).mean()
    return float(model - act)


def ratio_spread(bundle: Path, year: int) -> float | None:
    """Jun-Sep mean monthly coal ratio minus Feb-Apr mean."""
    t = year_table(bundle, year)
    if t is None:
        return None
    return float(
        t.loc[list(SUMMER), "coal_ratio"].mean() - t.loc[list(FEB_APR), "coal_ratio"].mean()
    )


def score(keeper: Path, arm: Path) -> pd.DataFrame:
    """Per-year metric table for both bundles plus the gate deltas."""
    rows = []
    for year in YEARS:
        kr, ar = year_row(keeper, year), year_row(arm, year)
        if kr is None or ar is None:
            raise SystemExit(f"{year}: missing sidecars (keeper={kr is None}, arm={ar is None})")
        ke, ae = matched_band_excess(keeper, year), matched_band_excess(arm, year)
        ks, asp = ratio_spread(keeper, year), ratio_spread(arm, year)
        rows.append(
            {
                "year": year,
                "k_excess_pp": ke,
                "a_excess_pp": ae,
                "d_excess_pp": ae - ke,
                "k_spread": ks,
                "a_spread": asp,
                "d_spread": asp - ks,
                "k_ratio": kr["ratio"],
                "a_ratio": ar["ratio"],
                "k_coal_twh": kr["coal_twh"],
                "a_coal_twh": ar["coal_twh"],
                "k_c3a": kr["c3a"],
                "a_c3a": ar["c3a"],
                "k_c3c": kr["c3c"],
                "a_c3c": ar["c3c"],
                "c3c_act": kr["c3c_act"],
            }
        )
    return pd.DataFrame(rows).set_index("year")


def verdict(t: pd.DataFrame) -> dict[str, bool]:
    """Evaluate the pre-committed gates on the metric table."""
    g1 = bool((t["d_excess_pp"] <= -_G1_MIN_EXCESS_DROP_PP).all())
    g2 = bool(
        (t["d_spread"] < 0).all() and (-t["d_spread"]).mean() >= _G2_MIN_MEAN_NARROWING
    )
    g3 = bool(
        ((t["a_c3a"] - t["k_c3a"]).abs() <= _G3_C3A_MAX_DEGRADE_PP).all()
        and ((t["a_c3c"] - t["k_c3c"]).abs() <= _G3_C3C_MAX_DEGRADE_HOURS).all()
    )
    bite = bool((t["a_coal_twh"] - t["k_coal_twh"]).abs().max() > _BITE_MIN_TWH)
    return {"G1_excess": g1, "G2_spread": g2, "G3_scarcity": g3, "BITE": bite}


def main() -> None:
    """Score the arm against the keeper and print the pre-committed verdicts."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keeper", required=True, type=Path)
    ap.add_argument("--arm", required=True, type=Path)
    args = ap.parse_args()

    pd.set_option("display.width", 240)
    pd.set_option("display.max_columns", 40)

    t = score(args.keeper, args.arm)
    print(f"keeper: {args.keeper.name}\narm:    {args.arm.name}\n")
    print(t.round(3).to_string())
    v = verdict(t)
    print()
    for gate, ok in v.items():
        print(f"  {gate:12s}: {'PASS' if ok else 'FAIL'}")
    print(
        f"\n  OVERALL: {'ALL GATES PASS' if all(v.values()) else 'FAIL'}"
        "  (annual ratio is REPORTED above, never gated — ERCOT-116 charter)"
    )


if __name__ == "__main__":
    main()
