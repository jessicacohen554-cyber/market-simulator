"""pjm-149 — census of the D-2/D-4 DISPATCH-PATH attribution drop.

Measures, per keeper bundle x year, exactly which FLOORED REAL PLANTS the
D-2/D-4 plant matrix in ``scripts/legitimacy_diagnostics.py`` drops because
they carry no series in the active dispatch source. Populations, the dispatch
contract, gates and stop rules are pre-registered in
``results/calibration/PREREG-pjm149-d2-floor-attribution-path-2026-08-03.md``
(committed and pushed before this probe first ran).

The defect (PREREG §1): ``diagnose_bundle`` builds the D-2/D-4 row set as
``[p for p in model_plants_plant if p in klass_by_pid or p in pid_strs]`` —
a comprehension over the DISPATCH map, so a plant that is floored but absent
from that map is silently dropped. The dispatch map is the solve's unit-hour
``dispatch/<year>_<pass>.parquet`` (every model plant; gitignored, so absent
from every committed bundle) or, failing that, the CAMPD-bench-keyed dashboard
run payload. On the payload path every floored plant with no CAMPD bench entry
loses all D-2/D-4 attribution. caiso-155's ``pseudo_pids`` re-admits only the
``plant_code <= 0`` (``u:``) interchange family; real plants stay dropped.

**Zero LP.** Floors come from the committed ``floors/*.npz`` when present, else
through the standing G-06 reconstruction (``run_year(fleet_only=True)`` from the
bundle's own ``meta.json`` — exits before any LP is constructed and caches
``floors/<year>_rebuilt.npz`` in the gitignored bundle dir). 2023-2025 only; no
holdout year is touched.

Per pre-registered population:

* **C1** — payload-absent floored REAL plants: numeric keys (``plant_code > 0``,
  i.e. not the ``u:`` pseudo-unit family) with max-hour ``min_gen`` >
  ``D2_FLOOR_MIN_MW`` that are ABSENT from the dispatch map. Reported per row:
  plant code, class, mechanisms, floored hours, mean/max MW, TWh/yr.
* **C2** — the lost rows: the (class, mechanism) D-2 attribution the drop
  destroys, aggregated over C1 under the §3.2 floor-energy convention.
* **C3** — NON-EXEMPT exposure (escalation trigger): the C1 subset whose class
  is neither in ``D2_EXEMPT_CLASSES`` nor the unclassified ``""`` bucket, i.e.
  a class ``run_d2`` actually gates. Non-empty ⇒ live scoring error (stop rule
  S2).
* **C4** — control: payload-PRESENT plants (count + floored count); must be
  bit-identical pre/post fix.
* **C5** — complement: model plants absent from the dispatch map AND unfloored;
  must stay excluded.
* **C6** — committed-corpus path census: whether each keeper's COMMITTED
  ``legitimacy_diagnostics.json`` was born on the parquet path or the payload
  path, inferred from D-2 rows the payload path cannot produce.

Usage::

    .venv/bin/python scripts/probes/_pjm149_d2_path_census.py \
        [--iso PJM] [--json-out results/calibration/_pjm149_census.json]
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
    D2_EXEMPT_CLASSES,
    D2_FLOOR_MIN_MW,
    PSEUDO_PLANT_KEY_PREFIX,
    aggregate_floors_by_plant,
    aggregate_model_plants,
    load_bench,
    load_dispatch_parquet,
    load_or_rebuild_floors,
    load_payload_plants,
)
from scripts.lib import keeper_store  # noqa: E402

from market_sim.data.floor_mechanisms import (  # noqa: E402
    D2_EXEMPT_MECHS,
    MECH_NAMES,
    NON_THERMAL_MECHS,
)

YEARS = (2023, 2024, 2025)


def _gated_class(klass: str) -> bool:
    """True when ``run_d2`` emits a GATED summary row for this class.

    ``run_d2`` skips the unclassified ``""`` bucket and ``D2_EXEMPT_CLASSES``
    outright, so only the complement can ever produce a C8 breach.
    """
    return klass != "" and klass not in D2_EXEMPT_CLASSES


def _gated_mech(mech_id: int) -> bool:
    """True when a mechanism's forced MWh enters ``forced_gated`` (the C8
    numerator). ``D2_EXEMPT_MECHS`` (nuclear / chp_steam / coal take-or-pay)
    and ``NON_THERMAL_MECHS`` (firm import, self-supply, hydro min-flow and
    RoR) are reported as detail rows but never gated."""
    return mech_id not in D2_EXEMPT_MECHS and mech_id not in NON_THERMAL_MECHS


def census_year(bundle: Path, iso: str, year: int, sidecar: dict | None) -> dict:
    """Census one keeper-bundle year. Returns the record printed/serialized."""
    arrays, ra_missing = load_or_rebuild_floors(bundle, iso, year)
    pids, floor_sum, mech_plant, groups, _fk = aggregate_floors_by_plant(arrays)
    pid_strs = [str(p) for p in pids]
    klass_by_pid = dict(zip(pid_strs, groups))

    # Resolve the dispatch map EXACTLY as diagnose_bundle does: parquet first,
    # payload second. No committed bundle carries dispatch/, so in practice
    # every keeper resolves to the payload (asserted in the record).
    frame, pass_label = load_dispatch_parquet(bundle, year)
    if frame is not None:
        sub = frame[frame["plant_code"] > 0]
        wide = (
            sub.groupby(["plant_code", "hour"], observed=True)["mw"]
            .sum()
            .unstack("hour", fill_value=0.0)
        )
        model_plants_plant = {str(int(pc)): None for pc in wide.index}
        source = f"dispatch/{year}_{pass_label}.parquet"
    elif sidecar is not None:
        bench = load_bench(REPO_ROOT, iso, year)
        model_plants_plant = aggregate_model_plants(
            load_payload_plants(REPO_ROOT, sidecar, year, bench)
        )
        source = f"payload {Path(sidecar['file']).name}"
    else:
        raise SystemExit(f"{iso} {year}: no dispatch parquet and no sidecar")

    present = set(model_plants_plant)

    # --- C1: floored REAL plants absent from the dispatch map ---------------
    c1: list[dict] = []
    for j, p in enumerate(pid_strs):
        if p.startswith(PSEUDO_PLANT_KEY_PREFIX):
            continue  # caiso-155's family; already re-admitted
        fl = floor_sum[j]
        if fl.max() <= D2_FLOOR_MIN_MW or p in present:
            continue
        on = fl > D2_FLOOR_MIN_MW
        mechs = sorted({int(m) for m in np.unique(mech_plant[j][on]) if int(m) != 0})
        c1.append(
            {
                "plant": p,
                "klass": klass_by_pid.get(p, ""),
                "mechanisms": [MECH_NAMES.get(m, str(m)) for m in mechs],
                "mech_ids": mechs,
                "hours_floored": int(on.sum()),
                "mean_mw": round(float(fl[on].mean()), 2) if on.any() else 0.0,
                "max_mw": round(float(fl.max()), 2),
                "floor_twh": round(float(fl[on].sum()) / 1e6, 5),
                # C3a: the class is one run_d2 gates, so re-admitting the plant
                # moves that class's DENOMINATOR (class_total_twh).
                "gated_class": _gated_class(klass_by_pid.get(p, "")),
                # C3b: ... and it carries a mechanism that enters forced_gated,
                # so it moves the C8 NUMERATOR too — the real escalation.
                "gated_mech": any(_gated_mech(m) for m in mechs),
            }
        )

    # --- C2: the D-2 rows the drop destroys ---------------------------------
    # Under the PREREG §3.2 convention disp := floor, so every floored hour is
    # at-floor and the row's forced energy is its floor energy, attributed to
    # that hour's binding mechanism.
    c2: dict[str, float] = {}
    for j, p in enumerate(pid_strs):
        if p.startswith(PSEUDO_PLANT_KEY_PREFIX) or p in present:
            continue
        fl = floor_sum[j]
        if fl.max() <= D2_FLOOR_MIN_MW:
            continue
        k = klass_by_pid.get(p, "")
        on = fl > D2_FLOOR_MIN_MW
        for m in {int(x) for x in np.unique(mech_plant[j][on]) if int(x) != 0}:
            sel = on & (mech_plant[j] == m)
            key = f"{k or '(unclassified)'}|{MECH_NAMES.get(m, str(m))}"
            c2[key] = c2.get(key, 0.0) + float(fl[sel].sum()) / 1e6

    # --- C3 / C4 / C5 -------------------------------------------------------
    c3a = [r for r in c1 if r["gated_class"]]
    c3b = [r for r in c3a if r["gated_mech"]]
    real_floored = [
        p
        for j, p in enumerate(pid_strs)
        if not p.startswith(PSEUDO_PLANT_KEY_PREFIX)
        and floor_sum[j].max() > D2_FLOOR_MIN_MW
    ]
    c5 = sum(
        1
        for j, p in enumerate(pid_strs)
        if not p.startswith(PSEUDO_PLANT_KEY_PREFIX)
        and p not in present
        and floor_sum[j].max() <= D2_FLOOR_MIN_MW
    )
    return {
        "iso": iso,
        "year": year,
        "dispatch_source": source,
        "floors_rebuilt": bool(ra_missing),
        "n_dispatch_plants": len(present),
        "n_fleet_plants": sum(
            1 for p in pid_strs if not p.startswith(PSEUDO_PLANT_KEY_PREFIX)
        ),
        "n_floored_real_plants": len(real_floored),
        "C1_absent_floored": c1,
        "C1_n": len(c1),
        "C1_twh": round(sum(r["floor_twh"] for r in c1), 5),
        "C2_lost_rows": {k: round(v, 5) for k, v in sorted(c2.items())},
        "C3a_gated_class_rows": c3a,
        "C3a_n": len(c3a),
        "C3a_twh": round(sum(r["floor_twh"] for r in c3a), 5),
        "C3b_gated_mech_rows": c3b,
        "C3b_n": len(c3b),
        "C3b_twh": round(sum(r["floor_twh"] for r in c3b), 5),
        "C4_present_plants": len(present),
        "C4_present_floored": sum(1 for p in real_floored if p in present),
        "C5_absent_unfloored": c5,
    }


def census_committed_artifact(bundle: Path, iso: str) -> dict:
    """C6 — which path the bundle's COMMITTED artifact was born on.

    The payload path can only ever emit rows for CAMPD-bench-keyed plants, so a
    committed D-2 row whose class carries no bench plant at all (the ``''``
    unclassified bucket — nuclear/hydro/renewable must-run — or a CHP class
    whose plants are CEMS-invisible) is a fingerprint of the parquet path.
    """
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return {"iso": iso, "committed_artifact": None}
    art = json.loads(path.read_text())
    diags = art.get("diagnostics") or {}
    rows = (diags.get("D2") or {}).get("rows") or []
    classes = sorted({str(r.get("class", "")) for r in rows})
    unclassified = [r for r in rows if str(r.get("class", "")) == ""]
    chp = [r for r in rows if str(r.get("class", "")).endswith("_CHP")]
    return {
        "iso": iso,
        "committed_artifact": str(path.relative_to(REPO_ROOT)),
        "d2_row_count": len(rows),
        "d2_classes": classes,
        "unclassified_rows": len(unclassified),
        "unclassified_twh": round(
            sum(float(r.get("forced_twh") or 0.0) for r in unclassified), 4
        ),
        "chp_rows": len(chp),
        "chp_twh": round(sum(float(r.get("forced_twh") or 0.0) for r in chp), 4),
        # Fingerprint: the payload path can only emit rows for bench-keyed
        # plants, and the '' (unclassified: nuclear / hydro / renewable
        # must-run) bucket has no bench entry at any ISO — so an '' row is a
        # positive fingerprint of the parquet path. Its ABSENCE is consistent
        # with the payload path but is not by itself proof (an ISO could carry
        # no '' floor at all), so the value is reported as
        # "payload-or-no-''-floor" rather than asserted.
        "path_fingerprint": (
            "parquet" if unclassified else "payload-or-no-unclassified-floor"
        ),
        "d2_notes": (diags.get("D2") or {}).get("notes") or [],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="*", default=None, help="default: all keepers")
    ap.add_argument("--years", nargs="*", type=int, default=list(YEARS))
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    keepers = keeper_store.keeper_ids(REPO_ROOT)
    isos = args.iso or sorted(keepers)
    out: list[dict] = []
    for iso in isos:
        kid = keepers[iso]
        side = json.loads(
            (REPO_ROOT / "frontend/data/backcast/registry" / f"{kid}.json").read_text()
        )
        bundle = REPO_ROOT / side["bundle"]
        print(f"\n===== {iso}  keeper={kid}  bundle={side['bundle']}")
        c6 = census_committed_artifact(bundle, iso)
        print(f"  C6 committed artifact: {json.dumps(c6, default=str)}")
        out.append({"kind": "C6", **c6, "keeper": kid})
        for year in args.years:
            rec = census_year(bundle, iso, int(year), side)
            rec["keeper"] = kid
            rec["kind"] = "year"
            out.append(rec)
            print(
                f"  {iso} {year}: source={rec['dispatch_source']} "
                f"fleet={rec['n_fleet_plants']} dispatch={rec['n_dispatch_plants']} "
                f"floored={rec['n_floored_real_plants']} "
                f"| C1={rec['C1_n']} ({rec['C1_twh']} TWh) "
                f"C3a(gated class)={rec['C3a_n']} ({rec['C3a_twh']} TWh) "
                f"C3b(gated MECH)={rec['C3b_n']} ({rec['C3b_twh']} TWh) "
                f"C5={rec['C5_absent_unfloored']}"
            )
            for k, v in rec["C2_lost_rows"].items():
                print(f"      lost D-2 row  {k:48s} {v:10.5f} TWh")
            # C3a is a denominator-only effect; only C3b can move the C8
            # numerator, so they are surfaced at different volumes.
            by_class: dict[str, list] = {}
            for r in rec["C3a_gated_class_rows"]:
                by_class.setdefault(f"{r['klass']} {r['mechanisms']}", []).append(r)
            for k, rs in sorted(by_class.items()):
                print(
                    f"      C3a denominator-only: {k} — {len(rs)} plant(s), "
                    f"{sum(x['floor_twh'] for x in rs):.5f} TWh"
                )
            for r in rec["C3b_gated_mech_rows"]:
                print(
                    f"      *** C3b GATED MECHANISM DROPPED: plant {r['plant']} "
                    f"{r['klass']} {r['mechanisms']} {r['floor_twh']} TWh"
                )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(out, indent=1, default=str))
        print(f"\nwrote {args.json_out}")

    # Headline: the escalation trigger. C3b is the one that can move a C8
    # verdict; C3a moves only a gated class's denominator.
    for limb, label in (
        ("C3a_n", "C3a (gated CLASS — denominator)"),
        ("C3b_n", "C3b (gated MECHANISM — C8 numerator)"),
    ):
        hit = [r for r in out if r.get("kind") == "year" and r.get(limb)]
        print(
            f"\n{label}: "
            + (
                "EMPTY at every ISO-year"
                if not hit
                else f"NON-EMPTY at {len(hit)} ISO-year(s): "
                + ", ".join(f"{r['iso']} {r['year']}" for r in hit)
            )
        )
    print(
        "  (exempt sets: D2_EXEMPT_CLASSES="
        f"{list(D2_EXEMPT_CLASSES)}, D2_EXEMPT_MECHS="
        f"{sorted(MECH_NAMES.get(m, m) for m in D2_EXEMPT_MECHS)}, "
        f"NON_THERMAL_MECHS={sorted(MECH_NAMES.get(m, m) for m in NON_THERMAL_MECHS)})"
    )


if __name__ == "__main__":
    main()
