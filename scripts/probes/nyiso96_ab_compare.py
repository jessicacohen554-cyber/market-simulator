"""Compare the nyiso-96 arm against its same-HEAD zero-delta control.

Scores the single mechanism-family delta (``tranche_startup_amortization`` +
``tranche_startup_measured_runs``) against the pre-registered predictions in
``docs/handoffs/nyiso96-preregistration.md`` §3, from the two bundles' own
committed sidecars.

Reports, per year:

* **the liveness check first** (the nyiso-89 §4a lesson): the max absolute
  hourly class delta between the arm and the control. A mechanism recorded ON
  in ``run_config.json`` that produces a byte-identical solve has not been
  tested — it failed to wire, and that is a stop-the-line result, not a null;
* CT_PEAKER / CT_CHP energy, plant-grain start count and run-length
  distribution, arm vs control vs the measured CAMPD bench — prediction 1 and 2;
* every class's energy, so the C1 movement is visible, with the knife-edge
  2023 CC_REGULAR cell called out explicitly — prediction 4;
* model hours over $300 against the measured tail — prediction 3 (C3c).

Usage::

    python scripts/probes/nyiso96_ab_compare.py \
        --control results/calibration/nyiso96_ctrl_zerodelta \
        --arm     results/calibration/nyiso96_ctamort
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.legitimacy_diagnostics import load_bench  # noqa: E402
from scripts.probes.nyiso96_ct_start_characterization import (  # noqa: E402
    CT_CLASSES,
    _online,
    _run_lengths,
    _starts,
    model_fleet_view,
    model_plant_hourly,
)

#: The C3c scarcity threshold the rubric scores the tail at ($/MWh).
TAIL_THRESHOLD = 300.0


def class_energy(bundle: Path, year: int) -> dict[str, float]:
    """Return {class: TWh} from a bundle's class_hourly sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return {str(k): float(v) / 1e6
            for k, v in df.groupby("klass", observed=True)["mw"].sum().items()}


def class_max_delta(a: Path, b: Path, year: int) -> tuple[float, str]:
    """Return (max abs hourly class MW delta, the class carrying it)."""
    da = pd.read_parquet(a / "hourly" / f"class_hourly_{year}.parquet")
    db = pd.read_parquet(b / "hourly" / f"class_hourly_{year}.parquet")
    ka = da.set_index(["klass", "hour"], observed=True)["mw"]
    kb = db.set_index(["klass", "hour"], observed=True)["mw"]
    diff = (ka - kb).abs().dropna()
    if diff.empty:
        return 0.0, ""
    return float(diff.max()), str(diff.idxmax()[0])


def tail_hours(bundle: Path, year: int) -> int:
    """Return the count of hours whose MAX zonal dual exceeds $300.

    Matches the rubric's C3c model-tail convention (``calibration_verdict``
    §C3c: "count of hours the LP's max zonal dual exceeds the per-ISO
    threshold", NYISO threshold $300) — deliberately the max, not a
    demand-weighted mean: on this keeper every model >$300 hour is Long Island
    while the five mainland zones share one lower dual, so a weighted mean
    would understate the tail to zero.
    """
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    px = df.groupby("hour", observed=True)["price"].max()
    return int((px > TAIL_THRESHOLD).sum())


def ct_stats(bundle: Path, year: int) -> dict[str, dict]:
    """Return per-CT-class start count, run-length and energy for a bundle."""
    pure, _hr, _vom = model_fleet_view(year)
    mw, _zone, cap = model_plant_hourly(bundle, year)
    out: dict[str, dict] = {}
    for klass in CT_CLASSES:
        codes = [c for c, k in pure.items() if k == klass and c in mw]
        starts = 0
        runs: list[int] = []
        online = 0
        energy = 0.0
        for c in codes:
            on = _online(mw[c], cap.get(c, 0.0))
            starts += len(_starts(on))
            runs += _run_lengths(on)
            online += int(on.sum())
            energy += float(mw[c].sum())
        out[klass] = {
            "plants": len(codes), "starts": starts, "online_h": online,
            "twh": round(energy / 1e6, 4),
            "median_run": float(np.median(runs)) if runs else 0.0,
            "mean_run": round(float(np.mean(runs)), 2) if runs else 0.0,
        }
    return out


def measured_ct(year: int) -> dict[str, dict]:
    """Return the measured CAMPD-bench CT statistics on the same bar."""
    pure, _hr, _vom = model_fleet_view(year)
    bench = load_bench(REPO, "NYISO", year)
    agg: dict[int, np.ndarray] = collections.defaultdict(lambda: np.zeros(8760))
    caps: dict[int, float] = collections.defaultdict(float)
    for pid, rec in bench.items():
        code = int(str(pid).split(":")[0])
        if rec["group"] not in CT_CLASSES:
            continue
        agg[code] += np.asarray(rec["mw"], dtype=float)[:8760]
        caps[code] += float(rec["npl"] or 0.0)
    out: dict[str, dict] = {}
    for klass in CT_CLASSES:
        codes = [c for c, k in pure.items() if k == klass and c in agg]
        starts = 0
        runs: list[int] = []
        energy = 0.0
        online = 0
        for c in codes:
            on = _online(agg[c], caps[c])
            starts += len(_starts(on))
            runs += _run_lengths(on)
            online += int(on.sum())
            energy += float(agg[c].sum())
        out[klass] = {
            "plants": len(codes), "starts": starts, "online_h": online,
            "twh": round(energy / 1e6, 4),
            "median_run": float(np.median(runs)) if runs else 0.0,
            "mean_run": round(float(np.mean(runs)), 2) if runs else 0.0,
        }
    return out


def main(argv: list[str] | None = None) -> int:
    """Print the A/B comparison for every year both bundles carry."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--control", type=Path,
                   default=REPO / "results/calibration/nyiso96_ctrl_zerodelta")
    p.add_argument("--arm", type=Path,
                   default=REPO / "results/calibration/nyiso96_ctamort")
    p.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    p.add_argument("--json-out", type=Path)
    args = p.parse_args(argv)

    out: dict = {"control": str(args.control), "arm": str(args.arm), "years": {}}
    for year in args.years:
        if not (args.arm / "hourly" / f"class_hourly_{year}.parquet").exists():
            print(f"{year}: arm sidecar missing — skipped")
            continue
        delta, who = class_max_delta(args.arm, args.control, year)
        ce_c, ce_a = class_energy(args.control, year), class_energy(args.arm, year)
        ct_c, ct_a = ct_stats(args.control, year), ct_stats(args.arm, year)
        ct_m = measured_ct(year)
        t_c, t_a = tail_hours(args.control, year), tail_hours(args.arm, year)

        rec = {
            "liveness_max_abs_class_delta_mw": round(delta, 4),
            "liveness_class": who,
            "class_energy_twh": {"control": ce_c, "arm": ce_a},
            "ct": {"control": ct_c, "arm": ct_a, "measured": ct_m},
            "tail_hours_gt300": {"control": t_c, "arm": t_a},
        }
        out["years"][str(year)] = rec

        print(f"\n{'=' * 74}\n{year}\n{'=' * 74}")
        flag = "LIVE" if delta > 1e-6 else "*** BYTE-IDENTICAL — MECHANISM INERT ***"
        print(f"liveness: max |Δ| class MW = {delta:.4f} ({who})   {flag}")
        for klass in CT_CLASSES:
            c, a, m = ct_c[klass], ct_a[klass], ct_m.get(klass, {})
            print(f"  [{klass}] TWh ctl {c['twh']:.4f} -> arm {a['twh']:.4f} "
                  f"(Δ {a['twh'] - c['twh']:+.4f})   measured {m.get('twh')}")
            print(f"      starts ctl {c['starts']:5d} -> arm {a['starts']:5d}   "
                  f"measured {m.get('starts')}    "
                  f"median run ctl {c['median_run']} -> arm {a['median_run']} "
                  f"(measured {m.get('median_run')})")
        print(f"  C3c hours >${TAIL_THRESHOLD:.0f}: ctl {t_c} -> arm {t_a}")
        print("  class energy deltas (TWh, |Δ| > 0.001):")
        for k in sorted(set(ce_c) | set(ce_a)):
            d = ce_a.get(k, 0.0) - ce_c.get(k, 0.0)
            if abs(d) > 0.001:
                star = "   <-- C1 knife edge" if (year == 2023 and k == "CC_REGULAR") else ""
                print(f"      {k:16s} {ce_c.get(k, 0.0):8.3f} -> "
                      f"{ce_a.get(k, 0.0):8.3f}  ({d:+.3f}){star}")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(out, indent=2))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
