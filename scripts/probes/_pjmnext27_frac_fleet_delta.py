"""PJM-NEXT-27 phase 0 (zero LP): what do the per-year coal ``online_frac`` rows add to the coal rows?

Three fleet builds per year of the keeper recipe (``pjmnext16_A_span``) at the W0 posture
(the ten W0 ``--set`` fields of ``ADDENDUM-pjm-next-26-w0-posture-2026-10-02.md``), via
``run_calibration.run_year(..., fleet_only=True)``; nothing is solved:

- ``main``: the artifacts on ``main`` (no coal-coverage rows, no per-year rows);
- ``rows``: the PJM-NEXT-25 ``thermal_tranches_PJM.csv`` append only (the PJM-NEXT-26 candidate);
- ``rows_frac``: the append plus the per-year ``online_frac`` rows for the 18 plants (this lane).

Per year: units moved ``rows -> rows_frac`` (confinement: only the 18 plants' units may move),
and floored TWh at the 18 plants under each build, per plant.

The candidate artifacts are swapped into ``data/raw/_processed-legacy/`` per build and the
on-disk bytes restored in ``finally`` (each build is its own process).

Run: ``python3 scripts/probes/_pjmnext27_frac_fleet_delta.py <main_tranches.csv>
<main_by_year.csv> <year> ...`` from a tree whose ``_processed-legacy`` holds the CANDIDATE
(rows + per-year) artifacts.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/pjmnext16_A_span"
LEG = REPO / "data/raw/_processed-legacy"
TRANCHE = LEG / "thermal_tranches_PJM.csv"
BY_YEAR = LEG / "thermal_tranches_online_frac_by_year_PJM.csv"
OUT = REPO / "results/phase0/pjm/_pjmnext27_frac_fleet_delta.json"
PLANTS = (594, 883, 884, 1554, 1571, 1572, 1573, 2836, 2840, 2866, 3122, 3140, 3149)
PLANTS += (3797, 6019, 8226, 10678, 54304)
W0_FIELDS = (
    "seasonal_capacity_basis",
    "backcast_actual_retirement_only",
    "commission_year_cod_fallback",
    "cc_block_summer_rating",
    "cc_steam_part_capacity",
    "retiree_vintage_status_scope",
    "admit_standby_units",
    "partial_plant_exit_carry",
    "mid_vintage_exit_carry",
    "unit_outage_dispatched_bin_denominator",
)


def build(year: int, npz: Path) -> None:
    """Child process: rebuild the W0 keeper fleet for ``year`` and save its arrays."""
    import inspect

    sys.path.insert(0, str(REPO))
    from scripts.lib import bundle_fleet as BF

    logging.disable(logging.CRITICAL)
    BF.ensure_probe_path()
    from scripts.replay_keeper import derived_run_year_inputs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = BF.full_run_year_kwargs(meta)
    kw["pjm_da_virtual_bids"] = False  # virtual units carry no floor (NEXT-25 probe)
    # Both channels, as replay_keeper's --set does (the ERCOT-65 defect class).
    kw["prb_overrides"] = dict(kw.get("prb_overrides") or {})
    params = set(inspect.signature(run_year).parameters)
    for f in W0_FIELDS:
        kw["prb_overrides"][f] = True
        if f in params:
            kw[f] = True
    state = run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        BF.bundle_gas_price(meta, year),
        **kw,
        **derived_run_year_inputs(BUNDLE, year),
    )
    cfg = state["config"]
    assert all(getattr(cfg, f) is True for f in W0_FIELDS), "W0 posture not armed"
    fa = state["fleet_arrays"]
    np.savez(
        npz,
        unit=np.asarray(fa.unit_ids).astype(str),
        plant=np.asarray(fa.plant_code).astype(int),
        pmax=np.asarray(fa.pmax, float),
        min_gen=np.asarray(fa.min_gen, float).sum(axis=1),
    )


def _run(year: int, tag: str, swaps: dict[Path, bytes]) -> dict:
    """Spawn one build with ``swaps`` written over the artifacts; restore after."""
    keep = {p: p.read_bytes() for p in swaps}
    npz = REPO / f"results/phase0/pjm/_pjmnext27_fleet_{tag}_{year}.npz"
    try:
        for p, b in swaps.items():
            p.write_bytes(b)
        subprocess.run(
            [sys.executable, __file__, "--child", str(year), str(npz)],
            check=True,
            cwd=REPO,
        )
    finally:
        for p, b in keep.items():
            p.write_bytes(b)
    d = dict(np.load(npz))
    npz.unlink()
    return d


def _floors(d: dict) -> dict[str, float]:
    """Floored GWh per appended plant (coal units only)."""
    out: dict[str, float] = {}
    for i, u in enumerate(d["unit"]):
        pc = int(d["plant"][i])
        if pc in PLANTS and "COAL" in u:
            out[str(pc)] = out.get(str(pc), 0.0) + float(d["min_gen"][i]) / 1e3
    return {k: round(v, 1) for k, v in sorted(out.items(), key=lambda kv: int(kv[0]))}


def compare(year: int, main_tr: bytes, main_by: bytes) -> dict:
    """Three builds for one year."""
    cand_tr, cand_by = TRANCHE.read_bytes(), BY_YEAR.read_bytes()
    builds = {
        "main": _run(year, "main", {TRANCHE: main_tr, BY_YEAR: main_by}),
        "rows": _run(year, "rows", {TRANCHE: cand_tr, BY_YEAR: main_by}),
        "rows_frac": _run(year, "rows_frac", {TRANCHE: cand_tr, BY_YEAR: cand_by}),
    }
    a, b = builds["rows"], builds["rows_frac"]
    ia = {u: i for i, u in enumerate(a["unit"])}
    moved, foreign = [], []
    for j, u in enumerate(b["unit"]):
        i = ia.get(u)
        if (
            i is None
            or not np.isclose(a["pmax"][i], b["pmax"][j])
            or not np.isclose(a["min_gen"][i], b["min_gen"][j])
        ):
            moved.append(str(u))
            if int(b["plant"][j]) not in PLANTS:
                foreign.append(str(u))
    floors = {k: _floors(v) for k, v in builds.items()}
    return {
        "units_moved_rows_to_rows_frac": len(moved),
        "foreign_units_moved": foreign,
        "floor_twh_18_plants": {
            k: round(sum(v.values()) / 1e3, 3) for k, v in floors.items()
        },
        "floor_gwh_by_plant": floors,
    }


def main() -> None:
    """Every requested year; write the JSON artifact."""
    if sys.argv[1] == "--child":
        build(int(sys.argv[2]), Path(sys.argv[3]))
        return
    main_tr, main_by = Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes()
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    res["plants"] = list(PLANTS)
    res["w0_fields"] = list(W0_FIELDS)
    for year in (int(a) for a in sys.argv[3:]):
        rec = compare(year, main_tr, main_by)
        res[str(year)] = rec
        print(
            year,
            rec["units_moved_rows_to_rows_frac"],
            "foreign:",
            len(rec["foreign_units_moved"]),
            rec["floor_twh_18_plants"],
            flush=True,
        )
        OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
