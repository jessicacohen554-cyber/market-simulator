#!/usr/bin/env python3
"""Derive partial (unit-level) outage derates from CAMPD capacity-factor ceilings.

For plants without unit-level data, a partial outage shows up as a sustained
*ceiling plateau*: the plant keeps running but its daily-max CF drops to a level
well below its normal capability (e.g. ~half capacity = half the units out),
then recovers. This detects those plateaus and emits a multiplicative
availability derate (ceiling / normal-ceiling) over the window, approximating
the lost capacity until unit-level data confirms it.

Restricted to plants where the signal is reliable: baseload units (annual mean
CF above :data:`_BASELOAD_CF`) that are COAL — all-or-nothing, so a depressed
ceiling is an outage, not economic part-load — plus a confirmed combined-cycle
allowlist. Economic single-train CC operation looks identical to a partial
outage from CF alone, so other CC plants are excluded until confirmed.

Writes ``data/raw/campd-partial-outages.csv``.

``--emit-units`` additionally writes the UNIT-ATTRIBUTED companion
``data/raw/campd-partial-outages-units.csv`` (ercot-174): the SAME plateaus,
the SAME ``derate_factor``s, now carrying **which CAMPD units carry each
plateau** and their capacities. The plant-grain file is unchanged — the
companion is emitted from the same detection pass, so the two come from one
in-memory row set and the plant-grain aggregation of the companion is
byte-identical to the committed extract by construction (the rule-23
`[R-FROZEN-DERIVE]` proof that only the GRAIN changed; the detector's frozen
identification constants are imported verbatim and never re-valued). The
attribution is consumed by the unit-scoped event-cap composition
(``ScenarioConfig.ercot_dam_availability_event_cap_unit_scoped``), which needs
to know whether the window and partial layers are measuring the SAME units'
downtime at an hour (``min()``, the layers double-count) or DIFFERENT units'
(the product stands). See
``docs/PRECOMMIT-ercot174-unit-attributed-partial-outage-2026-08-06.md`` §2.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent

from market_sim.config.paths import EIA_860_DIR, RAW_DATA_DIR  # noqa: E402
import sys

sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_campd_bins  # noqa: E402

# The plateau detector and its frozen plateau constants live in the shared
# outage-detection lib (formerly defined here); the unit-level deriver
# (scripts/data/derive_campd_unit_outages.py --partial-windows) reuses the same
# _detect verbatim from there.
from scripts.lib.outage_detect import (  # noqa: E402
    _CEILING_FRAC,
    _RUN_FLOOR_CF,
    _detect,
)

# Unit-attribution (--emit-units) reuses the unit-level deriver's CEMS loader,
# year-clock grid and EIA-860 capacity ladder VERBATIM, so the companion's unit
# ids and unit capacities are the SAME objects the window-outage extract
# (campd-unit-outages.csv) carries — which is what makes the two layers' unit
# sets comparable at all in the event-cap composition.
from scripts.data.derive_campd_unit_outages import (  # noqa: E402
    _load_unit_year,
    _unit_year_grid,
    build_capacity_index,
    unit_capacity_mw,
)

# Plant groups eligible for partial-outage detection: baseload COAL (all-or-
# nothing) and CC_REGULAR. The baseload-CF filter below excludes cyclic units
# where a depressed CF ceiling is economic part-load rather than an outage.
_DETECT_GROUPS: frozenset[str] = frozenset({"COAL", "CC_REGULAR"})
_BASELOAD_CF = 0.55  # only plants that normally run near their ceiling

# Columns of the plant-grain extract, in emission order. The unit-attributed
# companion carries these VERBATIM (plus its unit columns), so projecting the
# companion onto them and de-duplicating reproduces the plant-grain file
# exactly — the byte-equivalence proof of the grain change (rule 23).
_PLANT_COLUMNS: list[str] = [
    "oris_code",
    "plant_name",
    "plant_group",
    "year",
    "outage_start",
    "outage_stop",
    "derate_factor",
]
_SORT_KEY: list[str] = ["year", "oris_code", "outage_start"]


def _daily_ceiling_stats(cf: np.ndarray) -> tuple[np.ndarray, float]:
    """Return ``(daily_max, ref)`` for one unit's capacity factor.

    Both statistics are the PLANT detector's own, evaluated at unit grain and
    on the identical day grid (:func:`scripts.lib.outage_detect._detect`):
    ``daily_max`` is the per-day maximum CF, and ``ref`` is the 90th percentile
    of ``daily_max`` over the unit's RUNNING days (daily mean above the frozen
    :data:`~scripts.lib.outage_detect._RUN_FLOOR_CF`) — the unit's normal
    ceiling. ``ref`` is ``0.0`` when the unit never runs, which the caller
    treats as "carries nothing" (fail-safe).

    No new constant is introduced: ``_RUN_FLOOR_CF`` is imported from the
    frozen detector module (rule 23 `[R-FROZEN-DERIVE]`).
    """
    nd = cf.shape[0] // 24
    if nd == 0:
        return np.zeros(0, dtype=float), 0.0
    day = cf[: nd * 24].reshape(nd, 24)
    dmax, dmean = day.max(1), day.mean(1)
    running = dmean > _RUN_FLOOR_CF
    ref = float(np.percentile(dmax[running], 90)) if running.any() else 0.0
    return dmax, ref


def _unit_ceiling_index(
    unit_df: pd.DataFrame,
    code: int,
    year: int,
    end: pd.Timestamp,
    exact: dict,
    by_digits: dict,
) -> list[tuple[str, np.ndarray, float, float, str]]:
    """Return one entry per CAMPD unit at facility ``code``.

    Each entry is ``(unit_id, daily_max, ref, derate_capacity_mw, source)``.
    The capacity-factor denominator is the unit's own ``detect_mw`` (EIA-860
    nameplate, falling back to the observed CAMPD peak) — the same basis the
    window-outage detector thresholds on — while the emitted capacity is the
    block-share ``derate_mw`` the window extract writes, so the two layers'
    unit capacities agree. ``end`` is the year's CAMPD publication horizon, so
    the unit clock is the same clock the plant detector's plateau day indices
    address.
    """
    out: list[tuple[str, np.ndarray, float, float, str]] = []
    fac = unit_df[unit_df["facilityId"] == int(code)]
    for uid, sub in fac.groupby("unitId", observed=True):
        gross = _unit_year_grid(sub, year, end=end)
        peak = float(gross.max())
        detect_cap, derate_cap, source = unit_capacity_mw(
            int(code), uid, exact, by_digits, peak
        )
        if detect_cap <= 0.0:
            continue
        dmax, ref = _daily_ceiling_stats(gross / detect_cap)
        out.append((str(uid), dmax, ref, derate_cap, source))
    return out


def _carrying_units(
    units: list[tuple[str, np.ndarray, float, float, str]],
    s_day: int,
    e_day: int,
) -> list[tuple[str, float, str]]:
    """Return the units that CARRY a plateau spanning days ``[s_day, e_day)``.

    A unit carries the plateau iff, over the plateau window, its own median
    daily-max ceiling sits below the frozen :data:`_CEILING_FRAC` fraction of
    its own normal ceiling ``ref`` — the plant detector's own depressed-ceiling
    test, applied to the unit's own series. Both constants come from the frozen
    detector module and are never re-valued here (rule 23), so the attribution
    introduces **zero** new fitted scalars.

    Each entry is ``(unit_id, derate_capacity_mw, capacity_source,
    ceiling_ratio)``, where ``ceiling_ratio`` is the unit's own measured
    ``median(daily-max over window) / ref`` — the quantity the frozen test
    thresholds. It is emitted so the extract is self-describing and a stricter
    attribution can be evaluated as a pure reprojection of the committed file
    (a REPORTED, non-selecting robustness band), with no re-derive and no
    second threshold anywhere in the production path.

    An empty result is a legitimate outcome (the plateau's cause is not
    resolvable to any single unit's ceiling); the consumer then sees an empty
    unit set and keeps the incumbent composition — fail-safe by construction.
    """
    carried: list[tuple[str, float, str, float]] = []
    for uid, dmax, ref, cap_mw, source in units:
        if ref <= 0.0 or e_day > dmax.shape[0] or e_day <= s_day:
            continue
        ratio = float(np.median(dmax[s_day:e_day])) / ref
        if ratio < _CEILING_FRAC:
            carried.append((uid, cap_mw, source, round(ratio, 4)))
    return carried


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument(
        # W1 collapsed inputs/raw-data into data/raw — this is the location
        # the historic-outage overlay actually reads (outages.py).
        "--out",
        default=str(RAW_DATA_DIR / "campd-partial-outages.csv"),
    )
    ap.add_argument(
        "--emit-units",
        action="store_true",
        help=(
            "also write the unit-attributed companion (ercot-174): the same "
            "plateaus and the same derate factors, carrying which CAMPD units "
            "carry each one. The plant-grain --out file is unchanged."
        ),
    )
    ap.add_argument(
        "--out-units",
        default=str(RAW_DATA_DIR / "campd-partial-outages-units.csv"),
    )
    ap.add_argument(
        "--eia860",
        default=str(EIA_860_DIR / "eia860_generators.parquet"),
        help="EIA-860 generator parquet backing the unit-capacity ladder.",
    )
    args = ap.parse_args()

    bins = load_campd_bins("data/raw/reference/custom-bin-assignments.csv")
    cap = dict(zip(bins["Plant_Code"].astype(int), bins["capacity_mw"]))
    name = dict(zip(bins["Plant_Code"].astype(int), bins["Plant_Name"]))
    group = dict(zip(bins["Plant_Code"].astype(int), bins["Plant_Group"]))
    candidates = [c for c in cap if group.get(c) in _DETECT_GROUPS]

    # Unit-attribution index (--emit-units only): the EIA-860 capacity ladder
    # the window-outage deriver uses, so both layers resolve the same unit to
    # the same capacity.
    exact: dict = {}
    by_digits: dict = {}
    if args.emit_units:
        exact, by_digits = build_capacity_index(Path(args.eia860))

    rows = []
    unit_rows: list[dict] = []
    for yr in args.years:
        df = campd.load_campd_hourly(campd.states_for_iso(args.iso), [yr])
        if df.empty:
            continue
        # Clip an in-progress year's clock at the CAMPD publication horizon so
        # unpublished months are not zero-filled into a phantom full outage
        # (same fix as derive_campd_unit_outages.py / derive_campd_outages.py).
        end = min(
            pd.Timestamp(f"{yr}-12-31 23:00"),
            df["date"].max() + pd.Timedelta(hours=23),
        )
        full = pd.date_range(f"{yr}-01-01", end, freq="h")
        # Per-unit CEMS for the whole ISO-year, loaded once and indexed per
        # plant on first use (only the ~20 plants that actually carry plateaus
        # are ever touched).
        unit_df = pd.DataFrame()
        if args.emit_units:
            frames = [
                f
                for f in (
                    _load_unit_year(st, yr) for st in campd.states_for_iso(args.iso)
                )
                if not f.empty
            ]
            unit_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        unit_index: dict[int, list] = {}
        for code in candidates:
            g = campd.plant_hourly_grid(df, code, yr)
            if g.empty or cap[code] <= 0:
                continue
            cf = (g["gross_mw"].reindex(full).fillna(0.0) / cap[code]).to_numpy(
                dtype=float
            )
            # Coal is all-or-nothing per unit, and a derate cap only binds when
            # the model wants to run above the observed ceiling, so it is safe
            # to detect even on cyclic coal. CC part-loads economically, so its
            # depressed ceilings are only trustworthy on baseload units.
            if group.get(code) == "CC_REGULAR" and cf.mean() < _BASELOAD_CF:
                continue
            for s, e, factor in _detect(cf):
                row = {
                    "oris_code": code,
                    "plant_name": name.get(code, code),
                    "plant_group": group.get(code, ""),
                    "year": yr,
                    "outage_start": full[s * 24].strftime("%Y-%m-%d %H:00:00"),
                    "outage_stop": (full[min(e * 24, len(full) - 1)]).strftime(
                        "%Y-%m-%d %H:00:00"
                    ),
                    "derate_factor": factor,
                }
                rows.append(row)
                if not args.emit_units:
                    continue
                # Attribute this plateau to the units that carry it. The
                # plant-grain row above is untouched: the companion repeats it
                # verbatim once per carrying unit (and once with an empty
                # unit_id when no unit's own ceiling resolves it), so the
                # companion aggregates back to the plant-grain file exactly.
                if code not in unit_index:
                    unit_index[code] = (
                        []
                        if unit_df.empty
                        else _unit_ceiling_index(
                            unit_df, code, yr, end, exact, by_digits
                        )
                    )
                carried = _carrying_units(unit_index[code], s, e)
                if not carried:
                    unit_rows.append(
                        {
                            **row,
                            "unit_id": "",
                            "unit_capacity_mw": None,
                            "capacity_source": "",
                            "n_units_carrying": 0,
                            "ceiling_ratio": None,
                        }
                    )
                    continue
                for uid, cap_mw, source, ratio in carried:
                    unit_rows.append(
                        {
                            **row,
                            "unit_id": uid,
                            "unit_capacity_mw": round(float(cap_mw), 1),
                            "capacity_source": source,
                            "n_units_carrying": len(carried),
                            "ceiling_ratio": ratio,
                        }
                    )
    out = pd.DataFrame(rows, columns=_PLANT_COLUMNS).sort_values(_SORT_KEY)
    out.to_csv(args.out, index=False)
    print(f"wrote {len(out)} partial-outage windows to {args.out}")
    for yr in args.years:
        print(
            f"  {yr}: {(out['year'] == yr).sum()} windows, "
            f"{out[out['year'] == yr]['oris_code'].nunique()} plants"
        )
    if not args.emit_units:
        return

    units = pd.DataFrame(
        unit_rows,
        columns=[
            *_PLANT_COLUMNS,
            "unit_id",
            "unit_capacity_mw",
            "capacity_source",
            "n_units_carrying",
            "ceiling_ratio",
        ],
    ).sort_values([*_SORT_KEY, "unit_id"])
    units.to_csv(args.out_units, index=False)

    # BE-3, asserted in the deriver itself: projecting the companion onto the
    # plant-grain columns and de-duplicating must reproduce the plant-grain
    # frame EXACTLY (same rows, same order, same values). This is the rule-23
    # proof that only the GRAIN changed — a failure means the attribution
    # perturbed the detection and is stop-the-line.
    back = (
        units[_PLANT_COLUMNS]
        .drop_duplicates()
        .sort_values(_SORT_KEY)
        .reset_index(drop=True)
    )
    if not back.equals(out.reset_index(drop=True)):
        raise SystemExit(
            "BE-3 FAILED: the unit-attributed companion does not aggregate "
            "back to the plant-grain extract — the grain is not the only change"
        )
    attributed = int((units["n_units_carrying"] > 0).sum())
    print(
        f"wrote {len(units)} unit-attributed rows to {args.out_units} "
        f"(BE-3 PASS: {len(back)} plateaus round-trip exactly)"
    )
    print(
        f"  plateaus with >= 1 carrying unit: "
        f"{units[units['n_units_carrying'] > 0][_SORT_KEY].drop_duplicates().shape[0]}"
        f" / {len(back)}; attributed rows {attributed}"
    )


if __name__ == "__main__":
    main()
