"""ERCOT-112 scorer: A/B the coal econ marginal-HR floor across the full span.

Scores the two ERCOT-112 arms against the criteria fixed in
``results/calibration/PRECOMMIT-ercot112-coal-marginal-hr-fullspan-2026-07-25.md``
BEFORE any result was read (rule 1):

* **P1 direction** — per year, the annual coal ratio (model/actual) must move
  toward 1.0 in the treatment arm relative to the like-for-like baseline arm.
* **P2 no over-fire** — no year may undershoot past ``ratio >= 0.90``.
* **P3 leave-one-year-out** — the direction must hold in >= 2 of 3 years and no
  year may degrade ``|ratio - 1|`` by more than 0.05 (rule 24: in-sample gain
  with held-out degradation is overfitting, not skill).

Model generation is read from each bundle's committed ``hourly/`` class
sidecars (rule 15 — no re-solve); actuals are the EIA-930 hourly benchmark, the
same source ``scripts/probes/ercot111_coal_dispatch_econ.py`` scored against, so
the 2023 numbers are directly comparable to the ERCOT-111 finding.

Usage:
    python scripts/probes/ercot112_score_coal_arms.py \
        --baseline results/calibration/ercot112_coal_avail_only_fullspan \
        --arm      results/calibration/ercot112_coal_marginal_hr_fullspan
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia930.actuals import load_eia_hourly_benchmark  # noqa: E402

YEARS = (2023, 2024, 2025)
# Model class -> actuals family. The bench families the EIA-930 benchmark
# publishes are coal/gas; the model's per-class sidecar is aggregated to match.
_COAL_TOKENS = ("COAL",)
_GAS_TOKENS = ("CC_", "CT_", "ST_GAS", "ST_CHP", "CC_CHP", "CT_CHP")

# P2/P3 thresholds — fixed in the pre-commit doc, never re-tuned here.
_OVERFIRE_FLOOR = 0.90
_LOYO_MAX_DEGRADE = 0.05


def _model_series(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray] | None:
    """Return (coal MW, gas MW) hourly for a bundle-year, or ``None``."""
    path = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"]
    if df.empty:
        return None
    kl = df["klass"].astype(str).str.upper()
    coal = df[kl.str.contains("COAL")]
    gas = df[kl.str.startswith(("CC_", "CT_", "ST_"))]

    def _sum(frame: pd.DataFrame) -> np.ndarray:
        if frame.empty:
            return np.zeros(8760)
        return (
            frame.groupby("hour")["mw"]
            .sum()
            .reindex(range(8760), fill_value=0.0)
            .to_numpy(dtype=float)
        )

    return _sum(coal), _sum(gas)


def _month_of_hour() -> np.ndarray:
    """Month index (1-12) for each of the 8760 model hours (non-leap clock)."""
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return np.repeat(np.arange(1, 13), [d * 24 for d in days])


def year_row(bundle: Path, year: int) -> dict | None:
    """Coal/gas TWh, annual ratio, Jun-Sep ratio and monthly ratios for a year."""
    ms = _model_series(bundle, year)
    act = load_eia_hourly_benchmark("ERCOT", year)
    if ms is None or act is None:
        return None
    coal, gas = ms
    a_coal = np.asarray(act["coal"], dtype=float)
    a_gas = np.asarray(act["gas"], dtype=float)
    mo = _month_of_hour()
    jas = (mo >= 6) & (mo <= 9)
    monthly = {
        int(m): float(coal[mo == m].sum() / max(a_coal[mo == m].sum(), 1e-9))
        for m in range(1, 13)
    }
    return {
        "year": year,
        "coal_twh": coal.sum() / 1e6,
        "act_coal_twh": a_coal.sum() / 1e6,
        "gas_twh": gas.sum() / 1e6,
        "act_gas_twh": a_gas.sum() / 1e6,
        "ratio": float(coal.sum() / a_coal.sum()),
        "ratio_jas": float(coal[jas].sum() / a_coal[jas].sum()),
        "monthly": monthly,
    }


def main() -> None:
    """Score both arms and print the pre-committed P1/P2/P3 verdicts."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", required=True, type=Path)
    ap.add_argument("--arm", required=True, type=Path)
    args = ap.parse_args()

    base = {y: year_row(args.baseline, y) for y in YEARS}
    arm = {y: year_row(args.arm, y) for y in YEARS}

    print(f"{'yr':<6}{'arm':<10}{'coal':>8}{'actual':>8}{'ratio':>8}"
          f"{'JAS':>8}{'gas':>9}{'act gas':>9}")
    for y in YEARS:
        for name, tbl in (("baseline", base), ("floor", arm)):
            r = tbl[y]
            if r is None:
                print(f"{y:<6}{name:<10}  -- not solved --")
                continue
            print(f"{y:<6}{name:<10}{r['coal_twh']:8.2f}{r['act_coal_twh']:8.2f}"
                  f"{r['ratio']:8.3f}{r['ratio_jas']:8.3f}"
                  f"{r['gas_twh']:9.2f}{r['act_gas_twh']:9.2f}")

    print("\n--- monthly coal ratio (treatment arm) ---")
    for y in YEARS:
        r = arm[y]
        if r is None:
            continue
        cells = " ".join(f"{m:02d}:{r['monthly'][m]:.2f}" for m in range(1, 13))
        print(f"  {y}  {cells}")

    print("\n=== PRE-COMMITTED VERDICT ===")
    improved, degraded, overfire = [], [], []
    for y in YEARS:
        b, a = base[y], arm[y]
        if b is None or a is None:
            print(f"  {y}: INCOMPLETE — one arm missing")
            continue
        db, da = abs(b["ratio"] - 1.0), abs(a["ratio"] - 1.0)
        ok = da < db
        improved.append(ok)
        if da - db > _LOYO_MAX_DEGRADE:
            degraded.append(y)
        if a["ratio"] < _OVERFIRE_FLOOR:
            overfire.append(y)
        print(f"  {y}: |ratio-1| {db:.3f} -> {da:.3f}  "
              f"{'TOWARD 1.0' if ok else 'AWAY from 1.0'}")

    n_ok = sum(improved)
    print(f"\n  P1 direction (both 2024 & 2025 toward 1.0): "
          f"{'PASS' if all(improved[1:]) and len(improved) == 3 else 'FAIL'}")
    print(f"  P2 no over-fire (ratio >= {_OVERFIRE_FLOOR} every year): "
          f"{'PASS' if not overfire else f'FAIL {overfire}'}")
    print(f"  P3 LOYO (>=2/3 improve, none degrade > {_LOYO_MAX_DEGRADE}): "
          f"{'PASS' if n_ok >= 2 and not degraded else f'FAIL (ok={n_ok}/3, degraded={degraded})'}")


if __name__ == "__main__":
    main()
