"""Characterize the bench multi-class plant collapse across all six ISOs.

Scorer-correctness lane (nyiso-88 §5 follow-up): the per-plant benchmark keyed
``mw_p`` / ``grp_p`` by ``plant_code`` while iterating ``(plant_code, klass)``,
so every multi-class plant's WHOLE measured series is attributed to its
alphabetically-last model class. This probe enumerates that population and
computes the correction table — per (ISO, year, class) TWh moved — from
committed artifacts only (old bench parts + a no-LP fleet reconstruction +
CAMPD unit-level + EIA-923), BEFORE the scorer is touched, so the fix's effect
is known in advance and cannot be chosen by what it does to any gate.

No LP is solved. Rules: 13 [R-MEASURED] (split bases are measured inputs, never
model outcomes), 14 [R-ACCURATE] (unit-level measured split preferred over
proration).

Usage::

    python scripts/probes/bench_multiclass_collapse.py [--iso NYISO ...] \
        [--out results/calibration/bench_multiclass_collapse.json]
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.lib import backcast_artifacts as ba  # noqa: E402
from scripts.lib import bench_multiclass as bm  # noqa: E402

#: Current keepers (frontend/data/backcast/keepers/<ISO>.json) — the bundles
#: whose fleet composition defines each ISO's scored classes.
KEEPER_BUNDLES: dict[str, str] = {
    "CAISO": "results/calibration/caiso130_nameplate_B",
    "ERCOT": "results/calibration/ercot115_coal_floor_only",
    "MISO": "results/calibration/miso98_chp_sector_B",
    "NEISO": "results/calibration/neiso61_netrev_margin",
    "NYISO": "results/calibration/nyiso89_hrmeas_ctloaded",
    "PJM": "results/calibration/pjm133_nameplate_B",
}

YEARS = (2023, 2024, 2025)  # training years only (rule 22 [R-HOLDOUT])

_T = 8760


def _decode(b64: str, annual_twh: float | None, npl: float) -> np.ndarray:
    """Bench CF%-byte series -> hourly MW, rescaled to the exact annual."""
    import base64

    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    tot = raw.sum()
    if annual_twh is not None and tot > 0.0:
        return raw * (annual_twh * 1e6 / tot)
    return raw / 100.0 * npl


def characterize_iso_year(
    iso: str, year: int, bundle: Path, cache_dir: Path
) -> dict:
    """Return the correction record for one (ISO, year)."""
    part = ba.load_bench_part(ba.BENCH / iso / f"{year}.json.gz")
    bplants = part["bench"]["plants"]
    comp = bm.scored_class_composition(bundle, iso, year, cache_dir=cache_dir)
    mc = bm.multi_class_plants(comp)
    # Only bare (pre-split) keys characterize; a part already migrated to
    # slice keys has no collapsed multi-class plants left to report.
    pop = {
        int(k): mc[int(k)]
        for k in bplants
        if bm.KEY_SEP not in k and int(k) in mc
    }
    unit_hr, unresolved = bm.unit_class_hourly(iso, year, pop)
    e923_mon = bm.e923_class_monthly(iso, year)

    plants_out = []
    delta_c = collections.defaultdict(float)  # class -> TWh moved (CEMS basis)
    delta_e = collections.defaultdict(float)  # class -> TWh moved (EIA-923)
    for code, classes in sorted(pop.items()):
        entry = bplants[str(code)]
        old_grp = str(entry["group"])
        c_ann = float(entry.get("c_ann") or 0.0)
        e_ann = float(entry.get("e_ann") or 0.0)
        net = (
            _decode(entry["campd"], c_ann, float(entry.get("npl") or 1.0))
            if entry.get("campd") and not entry.get("nodata")
            else np.zeros(_T)
        )
        uh = unit_hr.get(code)
        # Classes actually covered by CAMPD units: the facility net series is
        # the sum of REPORTING units only, so it splits across covered
        # classes; an uncovered class's CEMS slice is genuinely zero (its
        # actual lives in the EIA-923 slice — the ct_only pattern).
        covered = (
            [k for k in classes if uh.get(k) is not None and float(uh[k].sum()) > 0.0]
            if uh
            else []
        )
        e923_by_cls = bm.map_e923_to_model_classes(
            e923_mon.get(code, {}), classes, comp[code]
        )
        if covered:
            series, basis = bm.split_measured_series(
                net,
                covered,
                {k: comp[code][k] for k in covered},
                {k: uh[k] for k in covered},
                None,
            )
            if len(covered) < len(classes):
                basis += f" (CEMS covers {covered} of {classes})"
        else:
            series, basis = bm.split_measured_series(
                net, classes, comp[code], None, e923_by_cls
            )
            if code in unresolved:
                basis += f" [{unresolved[code]}]"
        c_slices = {k: float(s.sum()) / 1e6 for k, s in series.items()}
        e_slices = {k: float(np.sum(v)) / 1e6 for k, v in e923_by_cls.items()}
        # Rescale e923 slices to the entry's stored e_ann (the bench e_ann can
        # carry the CAMPD backfill for preliminary vintages).
        e_tot = sum(e_slices.values())
        if e_tot > 0 and e_ann > 0:
            e_slices = {k: v * e_ann / e_tot for k, v in e_slices.items()}
        for k in classes:
            c_new = c_slices.get(k, 0.0)
            e_new = e_slices.get(k, 0.0)
            delta_c[k] += c_new - (c_ann if k == old_grp else 0.0)
            delta_e[k] += e_new - (e_ann if k == old_grp else 0.0)
        plants_out.append(
            {
                "plant": code,
                "name": entry.get("name", str(code)),
                "old_group": old_grp,
                "classes": {k: round(comp[code][k], 1) for k in classes},
                "basis": basis,
                "c_ann": round(c_ann, 4),
                "c_slices": {k: round(v, 4) for k, v in c_slices.items()},
                "e_ann": round(e_ann, 4),
                "e_slices": {k: round(v, 4) for k, v in e_slices.items()},
                "ct_only": bool(entry.get("ct_only")),
            }
        )
    bench_total = sum(
        float(p.get("c_ann") or 0.0)
        for p in bplants.values()
        if not p.get("nodata")
    )
    affected = sum(p["c_ann"] for p in plants_out)
    return {
        "iso": iso,
        "year": year,
        "n_benched_plants": len(bplants),
        "n_multiclass": len(pop),
        "benched_cems_twh": round(bench_total, 3),
        "multiclass_cems_twh": round(affected, 3),
        "share_pct": round(100.0 * affected / bench_total, 1) if bench_total else 0.0,
        "delta_twh_cems": {
            k: round(v, 4) for k, v in sorted(delta_c.items()) if abs(v) > 5e-5
        },
        "delta_twh_e923": {
            k: round(v, 4) for k, v in sorted(delta_e.items()) if abs(v) > 5e-5
        },
        "plants": plants_out,
        "multiclass_not_benched": sorted(
            c for c in mc if str(c) not in bplants
        ),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="*", default=sorted(KEEPER_BUNDLES))
    ap.add_argument(
        "--out", default="results/calibration/bench_multiclass_collapse.json"
    )
    ap.add_argument("--cache-dir", default=None)
    args = ap.parse_args(argv)
    cache_dir = Path(args.cache_dir) if args.cache_dir else REPO / ".comp_cache"
    records = []
    for iso in args.iso:
        bundle = REPO / KEEPER_BUNDLES[iso]
        for year in YEARS:
            part_path = ba.BENCH / iso / f"{year}.json.gz"
            if not part_path.exists():
                continue
            rec = characterize_iso_year(iso, year, bundle, cache_dir)
            records.append(rec)
            print(
                f"\n== {iso} {year}: {rec['n_multiclass']} multi-class plants, "
                f"{rec['multiclass_cems_twh']:.2f} of {rec['benched_cems_twh']:.2f} "
                f"benched CEMS TWh ({rec['share_pct']}%)"
            )
            for k, v in rec["delta_twh_cems"].items():
                print(f"   CEMS {k:<14} {v:+.3f} TWh")
            for p in rec["plants"]:
                print(
                    f"   {p['plant']:>6} {p['name'][:34]:<34} {p['old_group']:<12}"
                    f" -> {'/'.join(p['classes'])} [{p['basis']}]"
                    f" c={p['c_ann']:.3f} {p['c_slices']}"
                )
    out = Path(args.out)
    out.write_text(json.dumps(records, indent=1))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
