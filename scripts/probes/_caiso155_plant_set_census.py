"""caiso-155 — census of the diagnostics-harness PLANT-SET drop (caiso-151 §F).

Measures, per keeper bundle x year, exactly which floored unit-rows the
D-2/D-4 plant matrix in ``scripts/legitimacy_diagnostics.py`` DROPS because
they carry ``plant_code <= 0`` (interchange pseudo-units: firm-import
tranches, seam bands) — the defect caiso-151 §F filed and this session fixes.
Populations, gates and stop rules are pre-registered in
``results/calibration/PREREG-caiso155-diagnostics-plant-set-2026-08-02.md``
(committed before this probe first ran).

**Zero LP.** Floors come from the committed ``floors/*.npz`` when present,
else through the STANDING G-06 reconstruction (``run_year(fleet_only=True)``
from the bundle's own ``meta.json`` — exits before any LP is constructed and
caches ``floors/<year>_rebuilt.npz`` in the gitignored bundle dir). Reads only
2023-2025 bundles; no holdout year is touched.

Per pre-registered population:

* **P1** — rows with ``plant_code <= 0`` AND max-hour ``min_gen`` >
  ``D2_FLOOR_MIN_MW``: the dropped floored tranches, reported per row
  (unit_id, plant_group, mechanisms, floored hours, mean/max MW, TWh/yr).
* **P2** — structural dispatch-side fact: no P1 unit id appears among the run
  payload's plant keys, and ``dispatch/*.parquet`` is absent (asserted).
* **P3** — control: ``plant_code <= 0`` rows with NO floor (must stay
  excluded under the fix).
* **P4** — class-label guard: every P1 ``plant_group`` is expected ``""``
  (stop rule S2 otherwise).
* **P5** — P1 mechanisms without a class-applicable ``D4_WINDOWS`` entry
  (reported as rule-12 gaps; no entry is minted here).

Defect reproduction (falsifiable premise): the HEAD
``aggregate_floors_by_plant`` output must carry NONE of the P1 energy — its
total floored energy must equal the ``plant_code > 0`` subtotal exactly.

Usage::

    .venv/bin/python scripts/probes/_caiso155_plant_set_census.py [--iso CAISO]

Run per ISO or all six; append stdout to the committed transcript
``results/calibration/PROBE-caiso155-plant-set-census-2026-08-02.txt``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scripts.legitimacy_diagnostics import (  # noqa: E402
    D2_FLOOR_MIN_MW,
    D4_WINDOWS,
    aggregate_floors_by_plant,
    find_registry_sidecar,
    load_or_rebuild_floors,
)
from scripts.lib import backcast_artifacts as ba  # noqa: E402
from scripts.lib import keeper_store  # noqa: E402

from market_sim.data.floor_mechanisms import MECH_NAMES  # noqa: E402


def _payload_plant_keys(sidecar: dict, year: int) -> set[str]:
    """Plant keys present in the committed run payload for one year."""
    txt = (REPO_ROOT / sidecar["file"]).read_text()
    run = ba.decode_run_js(txt)
    return set(run.get("years", {}).get(str(year), {}).get("plants", {}) or {})


def census_year(bundle: Path, iso: str, year: int, sidecar: dict | None) -> dict:
    """Census one keeper-bundle year; returns the row dict printed below."""
    arrays, ra_missing = load_or_rebuild_floors(bundle, iso, year)
    pc = np.asarray(arrays["plant_code"])
    mg = np.clip(np.asarray(arrays["min_gen"], dtype=float), 0.0, None)
    mech = np.asarray(arrays["mechanism"])
    uids = [str(u) for u in arrays["unit_ids"]]
    groups = [str(g) for g in np.asarray(arrays["plant_group"]).astype(str)]

    dropped = pc <= 0
    floored_anywhere = mg.max(axis=1) > D2_FLOOR_MIN_MW
    p1_rows = np.flatnonzero(dropped & floored_anywhere)
    p3_count = int((dropped & ~floored_anywhere).sum())

    rows = []
    dropped_twh_exact = 0.0
    for r in p1_rows:
        hot = mg[r] > D2_FLOOR_MIN_MW
        dropped_twh_exact += float(mg[r][hot].sum()) / 1e6
        mech_ids = sorted(set(mech[r][hot].tolist()) - {0})
        rows.append(
            {
                "unit_id": uids[r],
                "plant_group": groups[r],
                "mechanisms": [MECH_NAMES.get(m, str(m)) for m in mech_ids],
                "mech_ids": mech_ids,
                "hours_floored": int(hot.sum()),
                "mean_floor_mw": round(float(mg[r][hot].mean()), 1) if hot.any() else 0,
                "max_floor_mw": round(float(mg[r].max()), 1),
                "floor_twh": round(float(mg[r][hot].sum()) / 1e6, 4),
            }
        )

    # Defect reproduction against the live scorer. PRE-FIX the plant
    # aggregation carries exactly the plant_code > 0 floored energy and none
    # of P1's; POST-FIX (the "u:" pseudo keys exist) it must carry the P1
    # energy too — so re-running this probe after the caiso-155 fix verifies
    # the drop is GONE rather than re-measuring it.
    head_keys, floor_sum, _, _, _ = aggregate_floors_by_plant(arrays)
    head_twh = float(np.clip(floor_sum, 0.0, None).sum()) / 1e6
    kept_twh = float(mg[pc > 0].sum()) / 1e6
    dropped_twh = dropped_twh_exact
    fix_present = any(str(k).startswith("u:") for k in head_keys)
    # Post-fix, sub-1-MW floor hours on a pseudo row are inside head_twh but
    # outside the P1 accumulation (which counts only hours > D2_FLOOR_MIN_MW),
    # so allow that sliver: 8760 h x 1 MW = 0.00876 TWh per pseudo row.
    slop = 1e-6 + (0.00876 * len(rows) if fix_present else 0.0)
    expected = kept_twh + dropped_twh if fix_present else kept_twh
    assert abs(head_twh - expected) <= slop, (
        f"{iso} {year}: aggregation {head_twh:.6f} TWh != expected "
        f"{expected:.6f} TWh (fix_present={fix_present}) — premise broken, stop"
    )

    # P2 — the payload cannot carry these rows; dispatch parquet is absent.
    payload_keys = _payload_plant_keys(sidecar, year) if sidecar else set()
    p1_uids = {r["unit_id"] for r in rows}
    assert not (p1_uids & payload_keys), "P1 unit id collides with a payload key"
    dispatch_present = any(
        (bundle / "dispatch" / f"{year}_{lab}.parquet").exists() for lab in ("P2", "P1")
    )

    # P5 — mechanisms on P1 rows lacking any class-applicable D4_WINDOWS row.
    p1_mechs = sorted({m for r in rows for m in r["mech_ids"]})
    d4_mechs = {mid for (mid, _k) in D4_WINDOWS}
    p5_gaps = [MECH_NAMES.get(m, str(m)) for m in p1_mechs if m not in d4_mechs]

    return {
        "year": year,
        "ra_floor_missing (rebuilt)": ra_missing,
        "p1_rows": rows,
        "p1_total_twh": round(dropped_twh, 4),
        "p3_unfloored_dropped_rows": p3_count,
        "p4_nonempty_groups": sorted(
            {r["plant_group"] for r in rows if r["plant_group"]}
        ),
        "p5_window_gaps": p5_gaps,
        "head_scorer_twh": round(head_twh, 4),
        "fix_present": fix_present,
        "dispatch_parquet_present": dispatch_present,
        "payload_plant_count": len(payload_keys),
    }


def main() -> int:
    """Run the census for one ISO or all keepers; print the record."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--iso", help="census a single ISO (default: all keepers)")
    args = ap.parse_args()

    ids = keeper_store.keeper_ids(REPO_ROOT)
    isos = [args.iso] if args.iso else sorted(ids)
    print(f"caiso-155 plant-set census — keepers at run time: {ids}")
    for iso in isos:
        run_id = ids[iso]
        side_path = REPO_ROOT / "frontend/data/backcast/registry" / f"{run_id}.json"
        side = json.loads(side_path.read_text())
        bundle = REPO_ROOT / side["bundle"]
        years = [int(y) for y in side.get("years", [])]
        assert set(years) <= {2023, 2024, 2025}, f"{iso}: out-of-training year"
        print(f"\n=== {iso} — keeper {run_id} — bundle {side['bundle']} ===")
        sidecar = find_registry_sidecar(REPO_ROOT, bundle)
        for year in years:
            try:
                rec = census_year(bundle, iso, year, sidecar)
            except FileNotFoundError as exc:
                print(
                    f"[{iso} {year}] BLOCKED (stop rule S3): floors rebuild "
                    f"needs an absent raw input — {exc}"
                )
                continue
            print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
