"""miso-103 Stage-1 pin-strength test for the coal minimum-take constraint's
tonnage — the admissibility gate that adjudicated the lane DATA-BLOCKED.

The chartered mechanism (MISO lever queue item 1, miso-96 §7 / miso-102 §6) is
an LP constraint ``sum_t P[p,t] >= MinTake[p, period]`` whose RHS must NOT be the
same year's measured receipts (rule 13 ``[R-MEASURED]``: EIA-923 publishes
deliveries, not contract terms). The only forward-regenerable candidate is a
lagged / multi-year-trailing-mean contracted tonnage,
``MinTake[p, Y] = contract_share[p] x mean(receipts tons, Y-3..Y-1)``.

This probe answers, from committed artifacts only (NO LP):

  1. Is the multi-year Schedule-5 receipts series on disk at plant grain?
     (``eia923_monthly_fuel_costs.parquet``, monthly plant-grain, 2018-2025 —
     but only for the 39/49 take-or-pay plants that report fuel COSTS, which
     is exactly the regulated set: merchants' costs are withheld upstream.)
  2. PIN STRENGTH: regress year-Y actual receipts on the trailing mean, and
     express the floor as a fraction of same-year actual tonnage / CAMPD
     energy. Verdict inputs: log-space cross-section R^2 0.87-0.94 (lag-1 and
     lag-5 windows the same), aggregate floor/actual 0.96 / 1.14 / 0.98,
     energy-weighted floor 90-96 % of actual coal energy.
  3. BINDING MARGIN: against the discount-free miso-102 arm B dispatch
     (``2026-07-29-miso-102b-sunkfixed``), the floor binds at 20-33 of 38
     plants (20-44 TWh forced above unconstrained economics) — so the
     constraint, not economics, would set annual coal energy, and it sets it
     to ~= the same year's actual. That is the rule-13 pin.
  4. DELTA test: R^2 of year-to-year changes is 0.17 — the trailing mean
     carries the LEVEL of actual burn without the year-specific driver signal.

Finding: ``results/calibration/FINDING-miso103-coal-mintake-tonnage-2026-07-29.md``.

Usage:
    python scripts/probes/miso103_mintake_pin_strength.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import scripts.legitimacy_diagnostics as LD  # noqa: E402
from market_sim.data.fleet.eia860 import eia860_regulated_plants  # noqa: E402

YEARS = [2023, 2024, 2025]
ARM_B_SIDECAR = "frontend/data/backcast/registry/2026-07-29-miso-102b-sunkfixed.json"


def annual_tons() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-plant annual coal receipt tons for MISO take-or-pay plants, 2018-2025.

    Source: the Schedule-5 fuel-cost parquet. Receipts whose cost is withheld
    are dropped upstream, so the series covers the 39/49 cost-reporting
    (regulated) plants — coincidentally the exact set the constraint targets.
    """
    df = pd.read_parquet(
        REPO / "data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet"
    )
    coal = df[(df.fuel_group == "Coal") & (df.year <= 2025)]
    top = pd.read_csv(
        REPO / "data/raw/_processed-legacy/coal_takeorpay_MISO.csv"
    ).set_index("plant_code")
    coal = coal[coal.plant_id.isin(top.index)]
    ann = coal.groupby(["plant_id", "year"])["quantity"].sum().unstack("year")
    return ann, top


def r2(x: np.ndarray, y: np.ndarray) -> float:
    """Plain OLS R^2 between two vectors, NaN-safe."""
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3:
        return float("nan")
    return float(np.corrcoef(x[m], y[m])[0, 1] ** 2)


def coal_energy_by_plant(bench: dict, model: dict | None = None) -> dict[int, float]:
    """Annual coal MWh per plant code from a bench (or model-payload) mapping."""
    out: dict[int, float] = {}
    for k, b in bench.items():
        if not b["group"].startswith("COAL"):
            continue
        code = int(str(k).split(":")[0])
        src = model[k] if model is not None else b["mw"]
        if model is not None and k not in model:
            continue
        out[code] = out.get(code, 0.0) + float(np.asarray(src[:8760]).sum())
    return out


def main() -> None:
    ann, top = annual_tons()
    share = top["contract_share"].reindex(ann.index)
    reg = eia860_regulated_plants()
    print(f"plants with receipts on disk 2018-2025: {len(ann)} "
          f"(regulated: {sum(p in reg for p in ann.index)}) of {len(top)} take-or-pay plants")
    print(f"tons-weighted contract_share: "
          f"{float((top.contract_share * top.total_tons).sum() / top.total_tons.sum()):.3f}; "
          f"share==1.0 at {int((top.contract_share == 1.0).sum())}/{len(top)} plants")

    sidecar = json.load(open(REPO / ARM_B_SIDECAR))

    for y in YEARS:
        lag3 = ann[[y - 3, y - 2, y - 1]].mean(axis=1)
        lag1 = ann[y - 1]
        lag5 = ann[[c for c in range(y - 5, y) if c in ann.columns]].mean(axis=1)
        act = ann[y]
        mintake = share * lag3
        m = np.isfinite(act) & np.isfinite(lag3) & (act > 0) & (lag3 > 0)
        ratio = (mintake[m] / act[m]).values

        bench = LD.load_bench(REPO, "MISO", y)
        model = LD.load_payload_plants(REPO, sidecar, y, bench)
        ae = coal_energy_by_plant(bench)
        me = coal_energy_by_plant(bench, model)
        codes = [c for c in ann.index[m] if c in me and ae.get(c, 0) > 0]
        # floor energy via the receipts-as-burn proxy: tons ratio x CAMPD energy
        fr = (share[codes] * lag3[codes] / ann.loc[codes, y]).clip(upper=1.5)
        floor_e = (fr * pd.Series(ae).reindex(codes)).astype(float)
        arm_e = pd.Series(me).reindex(codes).astype(float)
        binds = int((floor_e > arm_e).sum())
        shortfall = float((floor_e - arm_e).clip(lower=0).sum() / 1e6)
        pinned = float((fr.clip(upper=1.0) * pd.Series(ae).reindex(codes)).sum())
        tot = float(pd.Series(ae).reindex(codes).sum())

        print(f"\n== {y} ==  n={int(m.sum())} plants")
        print(f"  R2 actual_Y ~ trailing mean (logs): lag3 {r2(np.log(lag3[m]), np.log(act[m])):.3f}   "
              f"lag1 {r2(np.log(lag1[m].clip(lower=1)), np.log(act[m])):.3f}   "
              f"lag5 {r2(np.log(lag5[m]), np.log(act[m])):.3f}")
        print(f"  MinTake(share x lag3)/actual tons: p25 {np.percentile(ratio, 25):.3f}  "
              f"p50 {np.percentile(ratio, 50):.3f}  p75 {np.percentile(ratio, 75):.3f}  "
              f"aggregate {float(mintake[m].sum() / act[m].sum()):.3f}")
        print(f"  floor >= 90% of actual burn at {float((ratio >= 0.9).mean()):.0%} of plants; "
              f">= 100% at {float((ratio >= 1.0).mean()):.0%}")
        print(f"  energy-weighted floor (capped at 1) = {pinned / tot:.1%} of actual CAMPD coal energy")
        print(f"  BINDING vs discount-free arm B: binds at {binds}/{len(codes)} plants, "
              f"forced energy above unconstrained economics {shortfall:.1f} TWh "
              f"(arm {arm_e.sum() / 1e6:.1f} vs floor {floor_e.sum() / 1e6:.1f} TWh)")

    # within-plant delta test: does the trailing mean carry the year-specific signal?
    d_act, d_lag = [], []
    for y in [2024, 2025]:
        lag3 = ann[[y - 3, y - 2, y - 1]].mean(axis=1)
        lag3p = ann[[y - 4, y - 3, y - 2]].mean(axis=1)
        da, dl = ann[y] - ann[y - 1], lag3 - lag3p
        m = np.isfinite(da) & np.isfinite(dl)
        d_act += list(da[m].values)
        d_lag += list(dl[m].values)
    print(f"\n== within-plant DELTA test (pooled 2024+2025, n={len(d_act)}) ==")
    print(f"  R2 of (actual_Y - actual_Y-1) ~ (lag3_Y - lag3_Y-1): "
          f"{r2(np.array(d_lag), np.array(d_act)):.3f} "
          f"-> the trailing mean carries the LEVEL, not the year signal")


if __name__ == "__main__":
    main()
