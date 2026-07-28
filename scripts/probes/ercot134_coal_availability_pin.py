#!/usr/bin/env python
"""ERCOT-134 — the coal availability PIN, made reproducible.

``DIAGNOSIS-ercot130-minconfig-capoff-2026-07-28.md`` §4 established that the
model's legacy statistical coal availability sits below what the real ERCOT
coal fleet measurably delivered in 1,200-6,700 hours per plant-year — but its
table was produced ad hoc: ``scripts/probes/ercot130_capoff_phase1.py``
contains no CAMPD comparison at all (its ``score()`` is model-vs-model), so
the evidence behind a pending owner decision (ERCOT-116 adoption) existed
only in prose. This probe makes it a committed, re-runnable measurement.

Per plant and per year it reports:

* **model availability** — the keeper's own fleet-array coal
  ``availability x pmax`` summed per plant (captured by
  ``ercot130_capoff_phase1.capture_availability``, the exact array the
  ERCOT-129 conditional consults), as a mean fraction of fleet pmax and as a
  ratio to the COP declaration over online hours;
* **COP declared** — the 60-Day DAM accepted COP ``live_mw`` (an ERCOT HSL,
  NET), the fleet's own filed availability;
* **actual** — CAMPD unit-level gross load over the coal-fuelled units of the
  ten ERCOT coal plants, converted to NET by the per-year anchor below, with
  its p95 over the plant's own running hours;
* **impossible hours** — hours in which the actual plant output exceeds the
  model's ENTIRE available capacity for that plant (the §4 statistic: in such
  an hour no offer curve can reproduce reality, whatever the price);
* **ceiling-pin share** — the share of the model's online plant-hours
  dispatched AT the availability ceiling (the ERCOT-127 §1 SUSTAIN pin at
  plant grain): in a pinned hour the binding constraint is the availability
  bound, so the offer price is irrelevant and merit order is untested.

Dispatch sources
----------------
* default — the CURRENT KEEPER's committed dashboard run payload
  (``2026-07-28-ercot129-conditional-coal-min``), rule 15 ``[R-DASHBOARD]``.
  The payload is uint8-quantized at ``npl/100`` MW resolution, so the pin
  comparison carries a half-quantization-step tolerance (``npl/200``) per the
  ERCOT-130 §1 correction; without it the count is a phantom.
* ``--bundle DIR`` — a solved bundle's ``hourly/unit_hourly_<year>.parquet``
  (per-LP-unit ``mw`` + ``cap_mw``, P1 pass), for scoring fresh Phase-2 arms
  whose payloads are not yet registered. Availability comes from the same
  frame (``cap_mw`` IS ``pmax x availability``), so no monkeypatch capture is
  needed and the probe sees exactly the availability that bundle solved on.
  The bundle's LP dispatch is exact, so the pin tolerance is 0.5 MW.

The gross->net anchor — the trap, stated loudly
-----------------------------------------------
``actual`` is CAMPD GROSS; the model and the COP are NET. The anchor is
``bench EIA-923 coal net TWh / CAMPD coal gross TWh`` computed over the
**ERCOT ``COAL_PLANTS`` set only** (coal-fuelled units of the ten plants,
``primaryFuelInfo`` filtered — the convention of ``ercot126``/``ercot127``,
giving 0.8972 / 0.9051 / 0.9069 by year). Computing it over ALL Texas coal
facilities in the CAMPD extract (which includes non-ERCOT plants: Pirkey,
Martin Lake's SPP neighbours, etc.) gives ~0.8037 and deflates every actual
by a further ~11 %, making the §4 impossible-hours table look ~50 % inflated.
``--audit`` demonstrates both failure modes; the main path asserts the anchor
stays in a sane coal-net band (0.85-0.95).

W A Parish (3470) is dual-fuel: CAMPD reports its four coal units AND its gas
steamers under one facilityId. The ``primaryFuelInfo`` Coal|Lignite filter
(via ``ercot127_coal_dispatch_band.campd_coal_gross``) keeps the comparison
coal-vs-coal; ``--audit`` shows the whole-facility contamination.

No LP is built, no year is solved, nothing is registered, and no
``ScenarioConfig`` field, cache-key surface or solve path is touched.

Usage
-----
    python scripts/probes/ercot134_coal_availability_pin.py
    python scripts/probes/ercot134_coal_availability_pin.py --bundle DIR
    python scripts/probes/ercot134_coal_availability_pin.py --audit
    python scripts/probes/ercot134_coal_availability_pin.py --json-out PATH
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for _p in (str(_REPO), str(_REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.config import paths  # noqa: E402
from scripts.probes.ercot127_coal_dispatch_band import (  # noqa: E402
    COAL_PLANTS,
    bench_coal_actual_twh,
    campd_coal_gross,
    dam_declared,
    hour_index,
)
from scripts.probes.ercot130_capoff_phase1 import (  # noqa: E402
    CACHE,
    capture_availability,
    load_payload_dispatch,
)

YEARS: tuple[int, ...] = (2023, 2024, 2025)
ONLINE_MW = 1.0          # a plant counts as online above this dispatch level
BUNDLE_PIN_TOL_MW = 0.5  # LP dispatch is exact; payload mode uses npl/200
ANCHOR_BAND = (0.85, 0.95)  # sane gross->net band for a coal fleet


def _keeper_avail(year: int) -> tuple[dict[int, np.ndarray], dict[int, float]]:
    """Per-plant hourly ``availability x pmax`` (MW) from the ercot130 cache.

    Regenerates the cache from the keeper's own fleet-array path if absent
    (fresh container; ~2 min per year, no LP).
    """
    f = CACHE / f"avail_{year}.npz"
    if not f.exists():
        capture_availability(year)
    npz = np.load(f)
    plants = [int(c) for c in npz["plants"]]
    stack = npz["avail_cap"].astype(float)
    pmax = npz["pmax_total"].astype(float)
    return (
        {c: stack[i] for i, c in enumerate(plants)},
        {c: float(pmax[i]) for i, c in enumerate(plants)},
    )


def _bundle_series(
    bundle: Path, year: int
) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray], dict[int, float]]:
    """Per-plant hourly (dispatch MW, avail-cap MW, pmax) from ``unit_hourly``.

    ``cap_mw`` is the LP's own ``pmax x availability`` bound (P1 pass), so the
    availability scored here is exactly what that bundle's solve saw —
    including any config delta such as ``ercot_thermal_dam_availability_coal``.
    """
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "plant_group", "hour", "mw", "cap_mw"],
    )
    df = df[
        (df["pass"] == "P1")
        & df.plant_group.astype(str).str.startswith("COAL")
        & df.plant_code.astype(int).isin(COAL_PLANTS)
    ]
    g = df.groupby(["plant_code", "hour"], observed=True)[["mw", "cap_mw"]].sum()
    mw: dict[int, np.ndarray] = {}
    ac: dict[int, np.ndarray] = {}
    pmax: dict[int, float] = {}
    for code, sub in g.groupby(level=0):
        code = int(code)
        sub = sub.droplevel(0).sort_index()
        mw[code] = sub.mw.to_numpy(dtype=float)
        ac[code] = sub.cap_mw.to_numpy(dtype=float)
        pmax[code] = float(sub.cap_mw.max())
    return mw, ac, pmax


def _actuals(year: int) -> tuple[dict[int, np.ndarray], float]:
    """Per-plant actual NET MW and the COAL_PLANTS-scoped gross->net anchor."""
    gross = campd_coal_gross(year)
    gn = bench_coal_actual_twh(year) / (gross.to_numpy().sum() / 1e6)
    if not (ANCHOR_BAND[0] <= gn <= ANCHOR_BAND[1]):
        raise AssertionError(
            f"gross->net anchor {gn:.4f} outside {ANCHOR_BAND} — the anchor "
            "must be scoped to the ERCOT COAL_PLANTS set (all-TX-facilities "
            "scoping gives ~0.8037 and inflates the impossible-hours table)"
        )
    return {int(c): gross[c].to_numpy() * gn for c in gross.columns}, float(gn)


def score_year(
    year: int,
    mw: dict[int, np.ndarray],
    avail: dict[int, np.ndarray],
    pin_tol: dict[int, float],
) -> dict:
    """One year's per-plant and fleet table (see module docstring)."""
    act, gn = _actuals(year)
    live = dam_declared(year)
    rows = []
    fleet_online = fleet_pin = fleet_impossible = 0
    for code in sorted(COAL_PLANTS):
        name = COAL_PLANTS[code]
        disp = mw.get(code)
        ac = avail.get(code)
        if disp is None or ac is None:
            continue
        n = min(disp.size, ac.size, 8760)
        disp, ac = disp[:n], ac[:n]
        a = act.get(code, np.zeros(n))[:n]
        dec = (live[code].to_numpy() if code in live else np.zeros(n))[:n]

        online = disp > ONLINE_MW
        pin = online & (disp >= ac - pin_tol[code])
        act_on = a > ONLINE_MW
        impossible = act_on & (a > ac + 1e-6)
        seldec = online & (dec > ONLINE_MW)
        ratio = (
            float(ac[seldec].mean() / dec[seldec].mean()) if seldec.any() else None
        )
        fleet_online += int(online.sum())
        fleet_pin += int(pin.sum())
        fleet_impossible += int(impossible.sum())
        rows.append(
            {
                "plant": code,
                "name": name,
                "online_h": int(online.sum()),
                "pin_h": int(pin.sum()),
                "pin_share": round(float(pin.sum() / online.sum()), 3)
                if online.any()
                else None,
                "model_avail_mean_frac": round(float(ac.mean() / max(ac.max(), 1.0)), 3),
                "model_over_declared": round(ratio, 3) if ratio is not None else None,
                "model_avail_mean_online_mw": round(float(ac[seldec].mean()), 0)
                if seldec.any()
                else None,
                "actual_p95_mw": round(float(np.percentile(a[act_on], 95)), 0)
                if act_on.any()
                else None,
                "impossible_h": int(impossible.sum()),
                "actual_running_h": int(act_on.sum()),
            }
        )
    return {
        "gross_to_net_anchor": round(gn, 4),
        "plants": rows,
        "fleet_online_plant_hours": fleet_online,
        "fleet_pin_plant_hours": fleet_pin,
        "fleet_pin_share": round(fleet_pin / max(fleet_online, 1), 4),
        "fleet_impossible_plant_hours": fleet_impossible,
    }


def audit(year: int = 2025) -> dict:
    """§4-audit: demonstrate the two artifacts the fuel filter and anchor kill.

    (a) dual-fuel contamination — W A Parish is the only dual-fuel plant in the
        set; scored whole-facility on the raw GROSS basis (both artifacts
        stacked) its impossible count reads ~6,213 instead of the correct
        coal-only net-converted count.
    (b) gross-vs-net — Oak Grove scored on unconverted gross reads ~6,325.
    (c) the anchor trap — the all-TX-coal-facilities anchor is ~0.8037 against
        the correctly COAL_PLANTS-scoped 0.9069 (2025).
    """
    avail, _ = _keeper_avail(year)
    act, gn = _actuals(year)
    df = pd.read_parquet(
        paths.RAW_DIR / "campd-unit-level" / f"TX_{year}.parquet",
        columns=["facilityId", "date", "hour", "grossLoad", "primaryFuelInfo"],
    )
    df["facilityId"] = df.facilityId.astype(int)
    df["ts"] = pd.to_datetime(df.date) + pd.to_timedelta(df.hour, unit="h")

    def _imposs(series: np.ndarray, ac: np.ndarray) -> int:
        return int(((series > ONLINE_MW) & (series > ac + 1e-6)).sum())

    par = (
        df[df.facilityId == 3470]
        .groupby("ts")
        .grossLoad.sum()
        .reindex(hour_index(year))
        .fillna(0.0)
        .to_numpy()
    )
    coal_all_tx = df[
        df.primaryFuelInfo.astype(str).str.contains("Coal|Lignite", case=False, na=False)
    ].grossLoad.sum() / 1e6
    gross = campd_coal_gross(year)
    return {
        "year": year,
        "parish_whole_facility_gross_impossible_h": _imposs(par, avail[3470]),
        "parish_coal_only_net_impossible_h": _imposs(act[3470], avail[3470]),
        "oak_grove_gross_basis_impossible_h": _imposs(
            gross[6180].to_numpy(), avail[6180]
        ),
        "oak_grove_net_converted_impossible_h": _imposs(act[6180], avail[6180]),
        "anchor_coal_plants_scoped": round(gn, 4),
        "anchor_all_tx_coal_facilities": round(
            bench_coal_actual_twh(year) / coal_all_tx, 4
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "ERCOT-134 — reproduce, per plant and per year: model coal "
            "availability vs COP declared vs CAMPD actual; the "
            "impossible-hours count; and the availability-ceiling pin share."
        )
    )
    ap.add_argument(
        "--bundle",
        type=Path,
        default=None,
        help=(
            "score a solved bundle's hourly/unit_hourly_<year>.parquet "
            "instead of the keeper's committed dashboard payload"
        ),
    )
    ap.add_argument("--audit", action="store_true",
                    help="run the ERCOT-130 section-4 artifact audit and exit")
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    if args.audit:
        res = audit()
        print(json.dumps(res, indent=2))
        if args.json_out:
            args.json_out.write_text(json.dumps(res, indent=2))
        return

    out: dict = {
        "lane": "ercot134-coal-availability-pin",
        "source": str(args.bundle) if args.bundle else "keeper payload",
        "years": {},
    }
    for year in YEARS:
        if args.bundle:
            mw, avail, pmax = _bundle_series(args.bundle, year)
            tol = {c: BUNDLE_PIN_TOL_MW for c in mw}
        else:
            mw, npl = load_payload_dispatch(year)
            avail, _ = _keeper_avail(year)
            tol = {c: npl.get(c, 0.0) / 200.0 for c in mw}
        out["years"][str(year)] = score_year(year, mw, avail, tol)

    for year in YEARS:
        y = out["years"][str(year)]
        print(
            f"\n=== {year}  (anchor {y['gross_to_net_anchor']})  fleet pin "
            f"{y['fleet_pin_plant_hours']:,}/{y['fleet_online_plant_hours']:,} "
            f"= {y['fleet_pin_share']:.1%}  impossible "
            f"{y['fleet_impossible_plant_hours']:,} ==="
        )
        print(
            f"{'plant':13s} {'online':>7s} {'pin':>7s} {'pin_sh':>7s} "
            f"{'avail_f':>8s} {'mdl/dec':>8s} {'avail_MW':>9s} "
            f"{'act_p95':>8s} {'imposs':>7s}"
        )
        for r in y["plants"]:
            print(
                f"{r['name']:13s} {r['online_h']:7d} {r['pin_h']:7d} "
                f"{(r['pin_share'] if r['pin_share'] is not None else float('nan')):7.3f} "
                f"{r['model_avail_mean_frac']:8.3f} "
                f"{(r['model_over_declared'] if r['model_over_declared'] is not None else float('nan')):8.3f} "
                f"{(r['model_avail_mean_online_mw'] if r['model_avail_mean_online_mw'] is not None else float('nan')):9.0f} "
                f"{(r['actual_p95_mw'] if r['actual_p95_mw'] is not None else float('nan')):8.0f} "
                f"{r['impossible_h']:7d}"
            )
    if args.json_out:
        args.json_out.write_text(json.dumps(out, indent=1))
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
