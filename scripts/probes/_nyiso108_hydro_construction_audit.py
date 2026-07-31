"""nyiso-108 — measure the three hydro input-repair construction options.

Independently reproduces the nyiso-107 finding's NYISO hydro fleet numbers and
extends them where that finding only quoted 2025: the per-year effect of the
PJM/MISO posture (``--hydro-backfill-year 2024`` **without** the EIA-930 level
pin).

Three constructions, at the nyiso-105 keeper's exact remaining hydro settings:

* ``bare``     — the KEEPER: ``backfill_year=None``, ``eia930_monthly=False``
* ``backfill`` — option (ii), PJM/MISO posture
* ``pinned``   — option (i), CAISO/NEISO posture (backfill + 930 level pin)

For each it reports the LP hydro unit count, annual budget, MW envelope, the
monthly shape, and — because the pin scales the budget DOWN in 2023/2024 while
leaving the MW envelope and the treaty min-flow floors untouched — an explicit
**treaty min-flow feasibility** check on the two
:data:`~market_sim.config.constants.NYISO_HYDRO_TREATY_MIN_FLOW` plants.

Rule 13 [R-MEASURED] / rule 14 [R-ACCURATE] context: the level candidates are
scored against NYISO's own MIS P-63 Real-Time Fuel Mix telemetry, the
EIA-independent instrument nyiso-107 established.

Run:
    PYTHONPATH=.:src .venv/bin/python \
        scripts/probes/_nyiso108_hydro_construction_audit.py
"""

from __future__ import annotations

import json
import logging

import numpy as np

from market_sim.config.constants import (
    EIA930_PS_FOLDED_INTO_WAT,
    NYISO_HYDRO_TREATY_MIN_FLOW,
)
from market_sim.config.paths import REPO_ROOT
from market_sim.data.hydro import build_hydro_fleet, hours_per_month

FUELMIX = REPO_ROOT / "data" / "raw" / "NYISO" / "fuel-mix"

logging.basicConfig(level=logging.WARNING)

ISO = "NYISO"
YEARS = (2023, 2024, 2025)
ZONE_NAMES = [
    "Upstate_West",
    "Capital_Hudson",
    "Lower_Hudson",
    "NYC",
    "Long_Island",
]

# nyiso-107 §C.1: NYISO MIS P-63 Real-Time Fuel Mix, `Hydro` category — the
# EIA-independent instrument on the NYISO hydro level, TWh.
P63_HYDRO_TWH = {2023: 27.1845, 2024: 26.9763, 2025: 24.2489}

# nyiso-107 §A: the benchmark the scorer actually uses, after
# `_backfill_renewables_eia930`'s 0.90-completeness swap (2025 only), TWh.
AS_SCORED_BENCH_TWh = {2023: 28.0312, 2024: 27.4654, 2025: 24.1039}

CONSTRUCTIONS = {
    "bare": dict(backfill_year=None, eia930_monthly=False),
    "backfill": dict(backfill_year=2024, eia930_monthly=False),
    "pinned": dict(backfill_year=2024, eia930_monthly=True),
}


def _measure(year: int, backfill_year: int | None, eia930_monthly: bool) -> dict:
    """Build the NYISO hydro fleet for one year/construction and summarise it."""
    units, monthly = build_hydro_fleet(
        ISO,
        year,
        ZONE_NAMES,
        backfill_year=backfill_year,
        eia930_monthly=eia930_monthly,
        # The nyiso-105 keeper's own registered hydro gates, so every
        # construction is measured on the SAME remaining configuration and the
        # only delta is the backfill/pin pair (single-delta proof, rule 1).
        min_flow_floor=True,  # keeper `hydro_min_flow_floor` = True
        ror_split=False,  # keeper `hydro_ror_split` absent/False
        nameplate_aware_target=False,  # keeper flag False; INERT anyway (nyiso-107 §D)
    )
    if not units or monthly is None:
        return {"units": 0, "budget_twh": 0.0}
    energy = np.asarray(monthly, dtype=float)
    pmax = np.array([u.pmax_mw for u in units], dtype=float)
    hpm = hours_per_month().astype(float)

    # The armed min-flow floor is stamped per plant-month in MW. It is derived
    # from the EIA-930 Q95 level and then CLIPPED to the month's own budget
    # average power (allocate_min_flow_floor). On the bare keeper the budget is
    # the truncated vintage, so the clip can bite on the floor itself — measure
    # how much of the measured floor each construction can actually carry.
    floors = np.array(
        [
            u.hydro_min_flow_monthly_mw
            if u.hydro_min_flow_monthly_mw is not None
            else (0.0,) * 12
            for u in units
        ],
        dtype=float,
    )
    floor_twh = float((floors.sum(axis=0) * hpm).sum()) / 1e6
    # Feasibility of the two-sided hydro row: floor energy must fit the budget.
    floor_mwh = floors * hpm[None, :]
    infeasible = int((floor_mwh > energy + 1e-6).sum())

    # Physical headroom: can the fleet even deliver its budget?
    ceil_mwh = pmax[:, None] * hpm[None, :]
    over_ceiling = int((energy > ceil_mwh + 1e-6).sum())

    treaty = {}
    for pid, frac in NYISO_HYDRO_TREATY_MIN_FLOW.items():
        idx = [i for i, u in enumerate(units) if u.unit_id == f"{pid}_hydro"]
        if idx:
            i = idx[0]
            treaty[str(pid)] = {
                "treaty_frac": frac,
                "pmax_mw": round(float(pmax[i]), 1),
                "budget_twh": round(float(energy[i].sum()) / 1e6, 4),
                "cf": round(float(energy[i].sum()) / (float(pmax[i]) * 8760.0), 4),
            }

    return {
        "units": len(units),
        "budget_twh": round(float(energy.sum()) / 1e6, 4),
        "max_mw": round(float(pmax.sum()), 1),
        "largest_mw": round(float(pmax.max()), 1),
        "fleet_cf": round(float(energy.sum()) / (float(pmax.sum()) * 8760.0), 4),
        "monthly_twh": [round(float(v) / 1e6, 4) for v in energy.sum(axis=0)],
        "minflow_floor_twh": round(floor_twh, 4),
        "minflow_floor_pct_of_budget": round(
            100.0 * floor_twh / max(float(energy.sum()) / 1e6, 1e-9), 1
        ),
        "minflow_infeasible_plant_months": infeasible,
        "over_nameplate_plant_months": over_ceiling,
        "treaty_plants": treaty,
    }



def _p63_monthly_twh(year: int) -> np.ndarray:
    """NYISO MIS P-63 `Hydro` monthly totals (TWh) — the independent instrument.

    P-63 is NYISO's own real-time metered fuel mix, fully independent of EIA.
    It is the only NYISO hydro series that is neither the model's input nor the
    scorer's benchmark, so it is the one basis on which a 930-pinned run's
    seasonal shape is NOT tautological (rule 13: a validation target, never an
    input).
    """
    import pandas as pd

    fm = pd.read_csv(FUELMIX / f"NYISO_fuelmix_hourly_{year}.csv.gz")
    hyd = fm[fm["fuel_category"] == "Hydro"].copy()
    hyd["_m"] = pd.to_datetime(hyd["interval_start_local"]).dt.month
    # `gen_mw` is the hourly average MW, so summing it over an hour-indexed
    # frame gives MWh directly (the same reduction nyiso-107 used for the level).
    grp = hyd.groupby("_m")["gen_mw"].sum() / 1e6
    return np.array([float(grp.get(m, 0.0)) for m in range(1, 13)], dtype=float)


def section_shape(out: dict) -> dict:
    """Monthly seasonal shape of each construction vs the independent P-63."""
    print(f"\n{'=' * 78}\nSeasonal SHAPE vs NYISO P-63 (independent instrument)\n{'=' * 78}")
    print(f"{'construction':<11} {'year':<6} {'shape r':>9} {'share MAE':>11} {'peak mo':>9} {'P63 peak':>9}")
    res: dict = {}
    for name in CONSTRUCTIONS:
        res[name] = {}
        for y in YEARS:
            model = np.array(out["constructions"][name][str(y)]["monthly_twh"], float)
            p63 = _p63_monthly_twh(y)
            ms = model / max(model.sum(), 1e-9)
            ps = p63 / max(p63.sum(), 1e-9)
            r = float(np.corrcoef(ms, ps)[0, 1])
            mae = float(np.abs(ms - ps).mean())
            res[name][str(y)] = {
                "shape_r": round(r, 4),
                "share_mae": round(mae, 5),
                "peak_month": int(np.argmax(ms) + 1),
                "p63_peak_month": int(np.argmax(ps) + 1),
            }
            print(
                f"{name:<11} {y:<6} {r:>9.4f} {mae:>11.5f} "
                f"{int(np.argmax(ms) + 1):>9} {int(np.argmax(ps) + 1):>9}"
            )
    return res


def main() -> None:
    """Measure every (year, construction) pair and write the audit JSON."""
    assert ISO not in EIA930_PS_FOLDED_INTO_WAT, (
        "NYISO must stay absent from EIA930_PS_FOLDED_INTO_WAT — the 930 pin "
        "is only admissible because NYIS NG: WAT carries no PS fold (nyiso-107 C.2)"
    )

    out: dict = {"iso": ISO, "p63_twh": P63_HYDRO_TWH, "constructions": {}}
    for name, kwargs in CONSTRUCTIONS.items():
        out["constructions"][name] = {
            str(y): _measure(y, **kwargs) for y in YEARS  # type: ignore[arg-type]
        }

    print(f"\n{'=' * 78}\nNYISO hydro input constructions — LP fleet as built\n{'=' * 78}")
    hdr = f"{'construction':<11} {'year':<6} {'units':>6} {'budget TWh':>11} "
    hdr += f"{'maxMW':>9} {'fleetCF':>8} {'vs P-63':>9} {'vs bench':>9}"
    print(hdr)
    for name in CONSTRUCTIONS:
        for y in YEARS:
            m = out["constructions"][name][str(y)]
            b = m["budget_twh"]
            print(
                f"{name:<11} {y:<6} {m['units']:>6} {b:>11.4f} "
                f"{m['max_mw']:>9.1f} {m['fleet_cf']:>8.4f} "
                f"{100 * (b / P63_HYDRO_TWH[y] - 1):>8.2f}% "
                f"{100 * (b / AS_SCORED_BENCH_TWh[y] - 1):>8.2f}%"
            )

    print(f"\n{'=' * 78}\nArmed min-flow floor (hydro_min_flow_floor=True) — carried level\n{'=' * 78}")
    print(f"{'construction':<11} {'year':<6} {'floor TWh':>10} {'% budget':>9} {'infeasible':>11} {'>nameplate':>11}")
    for name in CONSTRUCTIONS:
        for y in YEARS:
            m = out["constructions"][name][str(y)]
            print(
                f"{name:<11} {y:<6} {m['minflow_floor_twh']:>10.4f} "
                f"{m['minflow_floor_pct_of_budget']:>8.1f}% "
                f"{m['minflow_infeasible_plant_months']:>11} "
                f"{m['over_nameplate_plant_months']:>11}"
            )

    print(f"\n{'=' * 78}\nMonthly shape, 2025 (TWh) — bare 3-unit vs repaired fleets\n{'=' * 78}")
    for name in CONSTRUCTIONS:
        mth = out["constructions"][name]["2025"]["monthly_twh"]
        print(f"{name:<11} " + " ".join(f"{v:5.2f}" for v in mth))

    out["shape_vs_p63"] = section_shape(out)

    dest = REPO_ROOT / "results/calibration/_nyiso108_hydro_construction_audit.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
