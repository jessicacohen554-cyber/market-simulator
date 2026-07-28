"""One-shot migration: split multi-class plants in committed bench artifacts.

Applies the nyiso-88 §5 attribution fix to the ALREADY-COMMITTED dashboard
artifacts without any re-solve (scorer-correctness lane, 2026-07-28):

* ``frontend/data/backcast/bench/<ISO>/<year>.json.gz`` — each multi-class
  plant's single collapsed entry is replaced by one entry per model class
  (key ``"<code>:<KLASS>"``), its measured CAMPD series split on the
  ``scripts/lib/bench_multiclass`` basis ladder (CAMPD unit-level hourly →
  EIA-923 monthly → EIA-860 nameplate proration) and its EIA-923 annual /
  monthly assigned per (plant, prime-mover) class. Part-level derived anchors
  that sum plant groups (``e930.coal_cems``, the CAISO CEMS gas anchors) are
  recomputed from the corrected entries. Single-class plants and untouched
  ISO-years are BYTE-IDENTICAL by construction (asserted).

* the six current keeper run payloads (``runs/<id>.js``) — a multi-class
  plant's payload entry holds exactly the alphabetically-LAST class's model
  dispatch (the defect dropped the rest), so the entry is RE-KEYED to that
  class's slice key and its r/NRMSE/capture recomputed against its own
  measured slice. The other classes' model dispatch is not recoverable from
  committed artifacts; those slices carry a bench entry but no payload entry
  until the ISO's next registration re-renders with the fixed builder.

The whole-plant CHP add-back embedded in a re-keyed CHP entry's ``m`` series
is releveled to the slice's own EIA-923 (a flat shift — correlation
invariant, same as the original add-back).

Usage::

    python scripts/migrate_bench_multiclass.py [--iso NYISO ...] [--dry-run]
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.lib import backcast_artifacts as ba  # noqa: E402
from scripts.lib import bench_multiclass as bm  # noqa: E402

_T = 8760

#: keeper id -> bundle dir (frontend/data/backcast/keepers/<ISO>.json)
KEEPERS: dict[str, tuple[str, str]] = {
    "CAISO": (
        "2026-07-27-caiso-130-nameplate-aware",
        "results/calibration/caiso130_nameplate_B",
    ),
    "ERCOT": (
        "2026-07-26-ercot115-coal-marginal-hr",
        "results/calibration/ercot115_coal_floor_only",
    ),
    "MISO": (
        "2026-07-27-miso-98b-sectormeasured",
        "results/calibration/miso98_chp_sector_B",
    ),
    "NEISO": (
        "2026-07-23-neiso-61-netrev-margin",
        "results/calibration/neiso61_netrev_margin",
    ),
    "NYISO": (
        "2026-07-27-nyiso-89-ctmeas-hrloaded",
        "results/calibration/nyiso89_hrmeas_ctloaded",
    ),
    "PJM": (
        "2026-07-27-pjm-133-nameplate",
        "results/calibration/pjm133_nameplate_B",
    ),
}

YEARS = (2023, 2024, 2025)  # training years only (rule 22 [R-HOLDOUT])

_GAS_GROUPS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")


def _rch():
    """Import the render module lazily (heavy model imports)."""
    from scripts import render_calibration_html as rch

    return rch


def _decode(b64: str, annual_twh: float | None, npl: float) -> np.ndarray:
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    tot = raw.sum()
    if annual_twh is not None and tot > 0.0:
        return raw * (annual_twh * 1e6 / tot)
    return raw / 100.0 * npl


def split_bench_plants(
    iso: str,
    year: int,
    bplants: dict,
    comp: dict[int, dict[str, float]],
) -> tuple[dict, dict[int, str], dict[int, dict[str, dict]]]:
    """Return (new plants dict, old collapsed group per plant, slice info).

    ``slice info``: plant -> klass -> the new entry (for payload re-pairing).
    """
    rch = _rch()
    multi = bm.multi_class_plants(comp)
    pop = {
        int(k): multi[int(k)]
        for k in bplants
        if bm.KEY_SEP not in k and int(k) in multi
    }
    if not pop:
        return bplants, {}, {}
    unit_hr, _unres = bm.unit_class_hourly(iso, year, pop)
    e923_mon = bm.e923_class_monthly(iso, year)
    npl_fam = bm.plant_class_nameplates(set(pop))

    old_group: dict[int, str] = {}
    slices: dict[int, dict[str, dict]] = {}
    out: dict = {}
    for key, entry in bplants.items():
        if bm.KEY_SEP in key or int(key) not in pop:
            out[key] = entry
            continue
        code = int(key)
        klasses = pop[code]
        old_group[code] = str(entry["group"])
        c_ann = float(entry.get("c_ann") or 0.0)
        e_ann = float(entry.get("e_ann") or 0.0)
        e_mon = np.asarray(entry.get("e_mon") or [0.0] * 12, dtype=float)
        npl_plant = float(entry.get("npl") or 1.0)
        net = (
            _decode(entry["campd"], c_ann, npl_plant)
            if entry.get("campd") and not entry.get("nodata")
            else np.zeros(_T)
        )
        # --- CAMPD hourly split (basis ladder) ---
        uh = unit_hr.get(code)
        covered = (
            [k for k in klasses if uh.get(k) is not None and uh[k].sum() > 0]
            if uh
            else []
        )
        caps = bm.class_nameplate_split(npl_fam.get(code, {}), klasses)
        e923_by_cls = bm.map_e923_to_model_classes(
            e923_mon.get(code, {}), klasses, caps
        )
        if covered:
            series, basis = bm.split_measured_series(
                net,
                covered,
                {k: caps.get(k, 0.0) for k in covered},
                {k: uh[k] for k in covered},
                None,
            )
            for k in klasses:
                series.setdefault(k, np.zeros(_T))
            if len(covered) < len(klasses):
                basis += ":partial-cems"
        else:
            series, basis = bm.split_measured_series(
                net, klasses, caps, None, e923_by_cls
            )
        # --- EIA-923 split: class shares applied to the COMMITTED plant
        # totals (which can carry the CAMPD backfill for prelim vintages) ---
        ann_by_cls = {k: float(np.sum(v)) for k, v in e923_by_cls.items()}
        ann_tot = sum(ann_by_cls.values())
        npl_shares = bm.nameplate_shares(caps, klasses, npl_plant)
        for k in klasses:
            share_ann = (
                ann_by_cls.get(k, 0.0) / ann_tot
                if ann_tot > 0
                else npl_shares[k] / max(npl_plant, 1.0)
            )
            e_ann_k = e_ann * share_ann
            e_mon_k = np.zeros(12)
            for m in range(12):
                mtot = sum(float(v[m]) for v in e923_by_cls.values())
                mshare = (
                    float(e923_by_cls.get(k, np.zeros(12))[m]) / mtot
                    if mtot > 0
                    else share_ann
                )
                e_mon_k[m] = e_mon[m] * mshare
            cnk = series[k]
            capk = float(npl_shares[k]) or 1.0
            new = {
                "name": entry.get("name", str(code)),
                "zone": entry.get("zone", "?"),
                "group": k,
                "npl": round(capk),
                "nodata": bool(cnk.sum() <= 0.0),
                "campd": rch._b64(100.0 * cnk / capk),
                "c_ann": round(float(cnk.sum()) / 1e6, 4),
                "c_mon": rch._monthly_gwh(cnk),
                "e_ann": round(e_ann_k, 4),
                "btm": round(e_ann_k * rch._btm_share(code, k, iso), 4),
                "e_mon": [round(x, 2) for x in e_mon_k],
                "split": basis,
            }
            skey = bm.slice_key(code, k)
            out[skey] = new
            slices.setdefault(code, {})[k] = new
    return out, old_group, slices


def migrate_part(iso: str, year: int, comp, dry_run: bool) -> dict | None:
    """Rewrite one bench part; returns the migration report (None = absent)."""
    rch = _rch()
    path = ba.BENCH / iso / f"{year}.json.gz"
    if not path.exists():
        return None
    before = path.read_bytes()
    part = ba.load_bench_part(path)
    bench = part["bench"]
    plants, old_group, slices = split_bench_plants(iso, year, bench["plants"], comp)
    if not old_group:
        # No multi-class plants: the part must round-trip byte-identically.
        if not dry_run:
            ba.write_bench_part(ba.BENCH, iso, year, part["meta"], part["bench"])
        after = path.read_bytes() if not dry_run else before
        assert after == before, f"{iso} {year}: untouched part changed bytes"
        return {"iso": iso, "year": year, "migrated": 0}
    bench["plants"] = plants
    # ctOnly provenance: drop migrated plants' old rows, re-flag their slices.
    if "ctOnly" in bench:
        bench["ctOnly"] = [
            r
            for r in bench["ctOnly"]
            if bm.plant_code_of_key(str(r["code"])) not in old_group
        ]
    new_rows = rch._flag_ct_only_reporters(
        {bm.slice_key(c, k): e for c, by in slices.items() for k, e in by.items()}
    )
    if new_rows:
        bench["ctOnly"] = sorted(
            bench.get("ctOnly", []) + new_rows,
            key=lambda r: r["ratio"],
            reverse=True,
        )
    if "ctOnly" in bench and not bench["ctOnly"]:
        del bench["ctOnly"]
    # Part-level anchors summed over plant groups.
    e930 = bench.get("e930") or {}
    if "coal_cems" in e930:
        e930["coal_cems"] = round(
            sum(
                (
                    float(p.get("c_ann") or 0.0)
                    for p in plants.values()
                    if str(p.get("group", "")).startswith("COAL")
                ),
                0.0,
            ),
            3,
        )
    if "gas_cems_grid" in e930:
        gas = [
            p
            for p in plants.values()
            if p.get("group") in _GAS_GROUPS and not p.get("nodata")
        ]
        _full = sum(float(p["c_ann"]) for p in gas)
        _grid = _full - sum(float(p.get("btm") or 0.0) for p in gas)
        e930["gas_cems_grid"] = round(_grid, 3)
        # gas_cogen_grid is plant-level non-CEMS mass — unchanged by the
        # split (coverage set is per plant either way).
        e930["fossil_cems_grid"] = round(
            _grid
            + float(e930.get("gas_cogen_grid") or 0.0)
            + sum(
                float(v)
                for g, v in (bench.get("classFull") or {}).items()
                if str(g).startswith("COAL")
            ),
            3,
        )
    if not dry_run:
        ba.write_bench_part(ba.BENCH, iso, year, part["meta"], part["bench"])
    return {
        "iso": iso,
        "year": year,
        "migrated": len(old_group),
        "old_group": {str(c): g for c, g in old_group.items()},
        "bytes_before": len(before),
        "bytes_after": (len(path.read_bytes()) if not dry_run else None),
    }


def migrate_payload(
    iso: str, run_id: str, old_groups: dict[int, dict[int, str]], dry_run: bool
) -> dict:
    """Re-key the keeper payload's multi-class plant entries to slice keys."""
    rch = _rch()
    path = ba.RUNS / f"{run_id}.js"
    txt = path.read_text()
    run = ba.decode_run_js(txt)
    changed = 0
    for ystr, ypay in run.get("years", {}).items():
        year = int(ystr)
        og = old_groups.get(year) or {}
        if not og:
            continue
        bench_part = ba.load_bench_part(ba.BENCH / iso / f"{year}.json.gz")
        bplants = bench_part["bench"]["plants"]
        plants = ypay.get("plants") or {}
        new_plants: dict = {}
        for key, p in plants.items():
            if bm.KEY_SEP in key or int(key) not in og:
                new_plants[key] = p
                continue
            code = int(key)
            klass = og[code]  # the class whose dispatch the entry holds
            skey = bm.slice_key(code, klass)
            b = bplants.get(skey)
            if b is None:
                new_plants[key] = p
                continue
            npl_k = float(b.get("npl") or 1.0)
            m_ann = p.get("m_ann")
            mw = _decode(p["m"], m_ann, npl_k) if p.get("m") else np.zeros(_T)
            # Relevel the whole-plant CHP add-back to the slice's own e923
            # (flat shift, correlation-invariant — mirrors the render).
            if klass in ("CC_CHP", "CT_CHP", "ST_CHP"):
                share = rch._btm_share(code, klass, iso)
                whole_e_ann = sum(
                    float(bp.get("e_ann") or 0.0)
                    for k2, bp in bplants.items()
                    if bm.plant_code_of_key(k2) == code
                )
                delta = (whole_e_ann - float(b.get("e_ann") or 0.0)) * share * 1e6
                if delta > 0:
                    mw = np.clip(mw - delta / _T, 0.0, None)
            cn = (
                _decode(b["campd"], b.get("c_ann"), npl_k)
                if b.get("campd") and not b.get("nodata")
                else None
            )
            r = nr = cap_pct = None
            if b.get("ct_only"):
                r, nr, cap_pct = rch._capture_on_923(
                    mw,
                    np.asarray(b.get("e_mon") or [0.0] * 12, dtype=float),
                    float(mw.sum()) / 1e6,
                    float(b.get("e_ann") or 0.0),
                )
            elif cn is not None and cn.sum() > 0 and mw.std() > 0:
                r = round(rch._pearson(mw, cn), 3)
                nr = round(rch._nrmse(mw, cn), 3)
                dev = (mw.sum() - cn.sum()) / cn.sum()
                cap_pct = rch._capture(r, nr, dev)
            newp = dict(p)
            newp["m"] = rch._b64(100.0 * mw / (npl_k or 1.0))
            newp["m_ann"] = round(float(mw.sum()) / 1e6, 4)
            newp["m_mon"] = rch._monthly_gwh(mw)
            newp["r"] = r
            newp["nrmse"] = nr
            newp["cap"] = cap_pct
            if b.get("ct_only"):
                newp["b923"] = True
            elif "b923" in newp:
                del newp["b923"]
            new_plants[skey] = newp
            changed += 1
        ypay["plants"] = new_plants
    if not dry_run and changed:
        path.write_text(ba.encode_run_js(run_id, run))
    return {"run": run_id, "rekeyed": changed}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="*", default=sorted(KEEPERS))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cache-dir", default=str(REPO / ".comp_cache"))
    args = ap.parse_args(argv)
    reports = []
    for iso in args.iso:
        run_id, bundle = KEEPERS[iso]
        old_groups: dict[int, dict[int, str]] = {}
        for year in YEARS:
            comp = bm.scored_class_composition(
                REPO / bundle, iso, year, cache_dir=Path(args.cache_dir)
            )
            rep = migrate_part(iso, year, comp, args.dry_run)
            if rep is None:
                continue
            reports.append(rep)
            old_groups[year] = {
                int(c): g for c, g in (rep.get("old_group") or {}).items()
            }
            print(f"{iso} {year}: migrated {rep['migrated']} plant(s)")
        if any(old_groups.values()):
            prep = migrate_payload(iso, run_id, old_groups, args.dry_run)
            reports.append(prep)
            print(f"{iso} payload {run_id}: re-keyed {prep['rekeyed']} entries")
    out = REPO / "results/calibration/bench_multiclass_migration_report.json"
    if not args.dry_run:
        out.write_text(json.dumps(reports, indent=1))
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
