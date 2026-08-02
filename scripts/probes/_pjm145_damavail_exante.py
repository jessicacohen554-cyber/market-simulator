#!/usr/bin/env python3
"""pjm-145 ex-ante (no-LP) measurement — the PREREG §3 instrument.

Measures, per PREREG-pjm145-dam-availability-2026-08-02.md §3, BEFORE any LP:

1. **Loader-level** (``data.pjm_outages``): per solve year the covered-day
   count (``lead_days == 0``, region "PJM RTO", non-leap clock), the measured
   unplanned-outage MW distribution, and the implied fleet-availability
   fraction distribution.
2. **Fleet-level**: per solve year, the keeper's fleet built twice through the
   real path — the bundle's own ``meta.json`` kwargs via
   ``replay_keeper.build_kwargs`` mapped onto
   ``run_calibration.run_year(fleet_only=True)`` (the same reconstruction
   ``legitimacy_diagnostics`` uses for D-2 floors), control vs
   ``prb_overrides + {"pjm_dam_availability": True}`` — and the per-class /
   pooled cap-weighted day-mean availability delta in MW.

Evaluates the three PREREG §4 kill rules (KILL-COVER / KILL-INERT /
KILL-DEGENERATE) and writes the JSON evidence to
``results/calibration/_pjm145_damavail_exante.json``.

No LP is constructed; ``fleet_only=True`` exits before the matrix builder.

    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm145_damavail_exante.py
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

KEEPER = REPO / "results/calibration/pjm143_hy_level_B"
OUT_PATH = REPO / "results/calibration/_pjm145_damavail_exante.json"

YEARS = (2023, 2024, 2025)

# PREREG §4 thresholds — restated here so the probe scores exactly what was
# pre-registered.
KILL_COVER_MIN_DAYS = 180
KILL_INERT_MEAN_MW = 150.0
KILL_INERT_P95_MW = 400.0
KILL_DEGEN_SATURATION = 0.30


def _pct(a: np.ndarray, qs=(5, 25, 50, 75, 95)) -> dict[str, float]:
    return {f"p{q}": round(float(np.percentile(a, q)), 4) for q in qs}


def loader_half() -> dict:
    """PREREG §3.1 — coverage + measured MW / fraction distributions."""
    from market_sim.data.pjm_outages import (
        pjm_dam_availability_series,
        pjm_outage_mw_series,
    )

    out: dict = {}
    for yr in YEARS:
        mw = pjm_outage_mw_series(yr)
        day_mw = mw.reshape(-1, 24)[:, 0]  # flat 24-h blocks by construction
        covered = np.isfinite(day_mw)
        avail = pjm_dam_availability_series(yr)
        # All covered classes carry the identical uniform series; take one.
        frac = next(iter(avail.values())) if avail else np.full_like(mw, np.nan)
        day_frac = frac.reshape(-1, 24)[:, 0]
        fin = day_frac[np.isfinite(day_frac)]
        out[str(yr)] = {
            "covered_days": int(covered.sum()),
            "total_days": int(day_mw.size),
            "outage_mw": _pct(day_mw[covered]) | {
                "mean": round(float(day_mw[covered].mean()), 1)
            },
            "avail_fraction": _pct(fin) | {"mean": round(float(fin.mean()), 4)},
            "frac_le_zero_days": int((fin <= 0.0).sum()),
        }
    return out


def _run_year_kwargs(meta: dict) -> dict:
    """Map the keeper meta onto ``run_calibration.run_year``'s signature.

    ``replay_keeper.build_kwargs`` performs the STRICT meta→solve kwargs
    mapping (refuses silent drops); the inner ``run_year`` signature differs
    from ``solve_and_persist``'s, so surplus keys are dropped HERE with an
    explicit printed record — the same lossy-but-logged reconstruction
    ``legitimacy_diagnostics._load_floor_arrays`` uses. Both probe arms share
    one mapping, so the arm-minus-control DELTA is exact even if a dropped key
    shifts the common base.
    """
    from scripts.replay_keeper import build_kwargs
    from scripts.run_calibration import run_year

    solve_kwargs = build_kwargs(meta)
    params = set(inspect.signature(run_year).parameters)
    rename = {"commitment": "commitment_enabled", "screen_coal": "commitment_screen_coal"}
    skip = {"year", "iso", "hours", "gas_price", "ttc_overrides", "fleet_only"}
    kwargs, dropped = {}, []
    for k, v in solve_kwargs.items():
        k2 = rename.get(k, k)
        if k2 in params and k2 not in skip:
            kwargs[k2] = v
        else:
            dropped.append(k)
    print(f"[map] {len(kwargs)} kwargs bound; dropped (not run_year params): {sorted(dropped)}")
    return kwargs


def fleet_half() -> dict:
    """PREREG §3.2 — arm-vs-control availability delta through the real path."""
    from market_sim.data.pjm_outages import PJM_OUTAGE_COVERED_GROUPS
    from scripts.run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
    base_kwargs = _run_year_kwargs(meta)
    gas_prices = meta.get("gas_prices", {})

    out: dict = {}
    for yr in YEARS:
        gas = float(gas_prices.get(str(yr), gas_prices.get(yr, 0.0)))
        per_arm: dict[str, dict] = {}
        for arm in ("control", "arm"):
            kw = dict(base_kwargs)
            if arm == "arm":
                prb = dict(kw.get("prb_overrides") or {})
                prb["pjm_dam_availability"] = True
                kw["prb_overrides"] = prb
            state = run_year(yr, "PJM", 8760, gas, {}, fleet_only=True, **kw)
            fa = state["fleet_arrays"]
            groups = np.array([str(g) for g in fa.plant_group])
            pmax = np.asarray(fa.pmax, dtype=float)
            av = np.asarray(fa.availability, dtype=float)
            n_days = av.shape[1] // 24
            cls_daymw: dict[str, np.ndarray] = {}
            for cls in sorted(PJM_OUTAGE_COVERED_GROUPS):
                idx = np.where(groups == cls)[0]
                if idx.size == 0:
                    continue
                # (n, days) day-mean availability x capacity, summed over units
                ad = av[idx, : n_days * 24].reshape(idx.size, n_days, 24).mean(axis=2)
                cls_daymw[cls] = (ad * pmax[idx, None]).sum(axis=0)
            per_arm[arm] = {
                "cls_daymw": cls_daymw,
                "cap_mw": {
                    cls: float(pmax[groups == cls].sum())
                    for cls in sorted(PJM_OUTAGE_COVERED_GROUPS)
                    if (groups == cls).any()
                },
            }
            del state, fa, av
        ctrl, armd = per_arm["control"], per_arm["arm"]
        classes = sorted(set(ctrl["cls_daymw"]) & set(armd["cls_daymw"]))
        pooled_delta = np.zeros_like(next(iter(ctrl["cls_daymw"].values())))
        cls_table = {}
        for cls in classes:
            d = armd["cls_daymw"][cls] - ctrl["cls_daymw"][cls]
            pooled_delta += d
            cap = ctrl["cap_mw"][cls]
            # Saturation: arm day-mean availability at the 1.0 cap.
            sat = float((armd["cls_daymw"][cls] >= cap * 0.9999).mean())
            cls_table[cls] = {
                "cap_mw": round(cap, 1),
                "mean_delta_mw": round(float(d.mean()), 1),
                "mean_abs_delta_mw": round(float(np.abs(d).mean()), 1),
                "p95_abs_delta_mw": round(float(np.percentile(np.abs(d), 95)), 1),
                "restore_days": int((d > 1.0).sum()),
                "remove_days": int((d < -1.0).sum()),
                "saturated_day_frac": round(sat, 4),
            }
        months = np.searchsorted(
            np.cumsum([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]),
            np.arange(pooled_delta.size),
            side="right",
        )
        out[str(yr)] = {
            "classes": cls_table,
            "pooled": {
                "mean_delta_mw": round(float(pooled_delta.mean()), 1),
                "mean_abs_delta_mw": round(float(np.abs(pooled_delta).mean()), 1),
                "p50_abs_delta_mw": round(float(np.percentile(np.abs(pooled_delta), 50)), 1),
                "p95_abs_delta_mw": round(float(np.percentile(np.abs(pooled_delta), 95)), 1),
                "max_abs_delta_mw": round(float(np.abs(pooled_delta).max()), 1),
                "restore_days": int((pooled_delta > 1.0).sum()),
                "remove_days": int((pooled_delta < -1.0).sum()),
                "monthly_mean_delta_mw": [
                    round(float(pooled_delta[months == m].mean()), 1) for m in range(12)
                ],
            },
        }
    return out


def main() -> None:
    loader = loader_half()
    fleet = fleet_half()

    cover_fail = [y for y in YEARS if loader[str(y)]["covered_days"] < KILL_COVER_MIN_DAYS]
    inert = all(
        fleet[str(y)]["pooled"]["mean_abs_delta_mw"] < KILL_INERT_MEAN_MW
        and fleet[str(y)]["pooled"]["p95_abs_delta_mw"] < KILL_INERT_P95_MW
        for y in YEARS
    )
    degen = []
    for y in YEARS:
        if loader[str(y)]["frac_le_zero_days"] > 0:
            degen.append(f"{y}: avail fraction <= 0 on covered days")
        sat = max(
            (c["saturated_day_frac"] for c in fleet[str(y)]["classes"].values()),
            default=0.0,
        )
        if sat > KILL_DEGEN_SATURATION:
            degen.append(f"{y}: restore saturation {sat:.2f} > {KILL_DEGEN_SATURATION}")

    verdict = {
        "KILL_COVER": {"fires": bool(cover_fail), "years": cover_fail},
        "KILL_INERT": {"fires": bool(inert)},
        "KILL_DEGENERATE": {"fires": bool(degen), "detail": degen},
        "any_kill": bool(cover_fail) or inert or bool(degen),
    }
    result = {"prereg": "PREREG-pjm145-dam-availability-2026-08-02.md",
              "loader": loader, "fleet": fleet, "kill": verdict}
    OUT_PATH.write_text(json.dumps(result, indent=1))
    print(json.dumps(verdict, indent=1))
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
