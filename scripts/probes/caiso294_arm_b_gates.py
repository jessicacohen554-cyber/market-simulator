"""caiso-294 ARM B: gates G-1/G-3/G-4/G-5 on the never-below-when-online level.

ZERO LP, and **zero committed artifact bytes move**: the new ``chp_pmin_on_cf``
column is read from a SCRATCH re-derive (``--armb-csv``), never from
``data/raw/_processed-legacy/``. Rule 23 ``[R-FROZEN-DERIVE]`` governs the
committed artifact; this probe measures so the owner's ruling on that artifact
can be made on numbers rather than blind.

ARM B, declared ex ante in
``docs/PRECOMMIT-caiso294-chp-steam-level-2026-09-20.md`` §3 BEFORE the
statistic was computed: the level is ``p2`` of the ONLINE sample — the existing
``_CHP_PMIN_PCTILE`` applied to ``on_cat`` instead of ``all_cat``. No percentile
is swept.

Reached without touching ``src/``, the same way ``caiso294_arm_a_energy.py``
reaches ARM A: ``fleet/assembly.py`` consumes the loader's
``(on_frac, level_on_cf)`` pair as ``chp_duty_on_frac, pmin_cf``, so the probe
patches that loader to return ``(on_frac_from_the_COMMITTED_identity,
chp_pmin_on_cf_from_the_SCRATCH_derive)``. The WINDOW half is therefore
byte-identical to the one caiso-293 validated and only the LEVEL moves.

Gates, inherited verbatim from PRECOMMIT caiso-293 §4 plus G-5:

* **G-1** identity ``|on_frac x median_cf - steam_level_cf| <= 0.05`` — measured
  by ``caiso293_gates.py``; unaffected by this arm and not recomputed here.
* **G-3** flat-host control forced energy moves < 2 %/yr.
* **G-4** cyclers forced energy moves < 10 %/yr.
* **G-5** *(new)* the re-derive is PURELY ADDITIVE: every pre-existing column of
  the scratch artifact is byte-identical to the committed one, and only
  ``chp_pmin_on_cf`` appears. This is the check that says whether the committed
  artifact is even reproducible at HEAD — a FAIL here is a finding about the
  derive, not about ARM B.

Run::

    PYTHONPATH=.:src python scripts/probes/caiso294_arm_b_gates.py \
        --armb-csv <scratch>/thermal_tranches_CAISO_armB.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes.caiso293_gates import (  # noqa: E402
    CYCLERS,
    FLAT,
    G3_BAR,
    G4_BAR,
    YEARS,
    compose,
    forced_by_plant,
)

COMMITTED = REPO / "data/raw/_processed-legacy/thermal_tranches_CAISO.csv"
OUT = REPO / "results/calibration/_caiso294_arm_b.json"
NEW_COL = "chp_pmin_on_cf"


def _rows(path: Path) -> tuple[list[str], dict[tuple[str, str], dict]]:
    with path.open() as fh:
        rd = csv.DictReader(fh)
        cols = list(rd.fieldnames or [])
        out = {(r["plant_code"], r["plant_group"]): r for r in rd}
    return cols, out


def gate_5(armb_csv: Path) -> dict:
    """Purely-additive check: only NEW_COL appears, every other byte holds."""
    old_cols, old = _rows(COMMITTED)
    new_cols, new = _rows(armb_csv)
    added = [c for c in new_cols if c not in old_cols]
    removed = [c for c in old_cols if c not in new_cols]
    key_diff = {
        "only_committed": sorted(str(k) for k in (old.keys() - new.keys()))[:20],
        "only_rederive": sorted(str(k) for k in (new.keys() - old.keys()))[:20],
    }
    moved: list[dict] = []
    for k in sorted(old.keys() & new.keys()):
        for c in old_cols:
            if old[k].get(c, "") != new[k].get(c, ""):
                moved.append(
                    {
                        "row": f"{k[0]}/{k[1]}",
                        "column": c,
                        "committed": old[k].get(c, ""),
                        "rederive": new[k].get(c, ""),
                    }
                )
    ok = (
        added == [NEW_COL]
        and not removed
        and not key_diff["only_committed"]
        and not key_diff["only_rederive"]
        and not moved
    )
    return {
        "pass": ok,
        "added_columns": added,
        "removed_columns": removed,
        "row_key_diff": key_diff,
        "n_moved_cells": len(moved),
        "moved_sample": moved[:40],
        "committed_rows": len(old),
        "rederive_rows": len(new),
    }


def arm_b_levels(armb_csv: Path) -> dict[tuple[int, str], float]:
    """``{(plant_code, group): chp_pmin_on_cf}`` from the SCRATCH artifact."""
    _, new = _rows(armb_csv)
    out: dict[tuple[int, str], float] = {}
    for (code, group), r in new.items():
        if str(r.get("status", "ok")) != "ok":
            continue
        try:
            lvl = float(r.get(NEW_COL, ""))
        except (TypeError, ValueError):
            continue
        out[(int(code), str(group))] = max(0.0, lvl)
    return out


def patch_arm_b(levels: dict[tuple[int, str], float]) -> None:
    """Swap the duty map's LEVEL for the never-below-when-online statistic."""
    import market_sim.data.fleet.assembly as assembly

    original = assembly.thermal_tranche_chp_steam_duty
    if getattr(original, "_arm_b", False):
        return

    def never_below(iso: str, per_unit: bool = False, merit_guard: bool = False):
        out = original(iso, per_unit, merit_guard)
        # on_frac stays the COMMITTED identity (steam_level_cf / median_cf), so
        # the window half is bit-identical to the one caiso-293 validated.
        return {k: (v[0], levels.get(k, 0.0)) for k, v in out.items()}

    never_below._arm_b = True  # type: ignore[attr-defined]
    assembly.thermal_tranche_chp_steam_duty = never_below  # type: ignore[assignment]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--armb-csv", required=True)
    args = ap.parse_args()
    armb_csv = Path(args.armb_csv)

    report: dict = {
        "arm": "B — chp_pmin_on_cf (p2 of the ONLINE sample), duty window unchanged",
        "level_source": str(armb_csv),
        "precommit": "docs/PRECOMMIT-caiso294-chp-steam-level-2026-09-20.md",
    }
    g5 = gate_5(armb_csv)
    report["G5"] = g5
    print(
        f"G-5 purely-additive: {'PASS' if g5['pass'] else 'FAIL'}  "
        f"(added {g5['added_columns']}, removed {g5['removed_columns']}, "
        f"moved cells {g5['n_moved_cells']}, rows {g5['committed_rows']} -> "
        f"{g5['rederive_rows']})"
    )
    for m in g5["moved_sample"][:10]:
        print(f"   moved {m['row']:<22} {m['column']:<18} {m['committed']} -> {m['rederive']}")

    levels = arm_b_levels(armb_csv)
    report["n_levels"] = len(levels)
    zero = sorted(k for k in levels if levels[k] <= 0.0)
    report["zero_level_rows"] = [f"{c}/{g}" for c, g in zero]
    print(
        f"\nARM B levels: {len(levels)} ok CHP rows carry {NEW_COL}; "
        f"{len(zero)} read 0.0 (those plants fall through assembly's "
        f"'_duty[1] > 0' guard and KEEP today's all-hours diluted level)"
    )

    patch_arm_b(levels)
    g3 = g4 = True
    per_year = {}
    for year in YEARS:
        gens_off, arr_off, _ = compose(year, armed=False)
        off_by_plant = forced_by_plant(gens_off, arr_off)
        gens_on, arr_on, _ = compose(year, armed=True)
        on_by_plant = forced_by_plant(gens_on, arr_on)

        def grp(d, keys):
            return sum(v for k, v in d.items() if k in keys)

        f_off, f_on = grp(off_by_plant, FLAT), grp(on_by_plant, FLAT)
        c_off, c_on = grp(off_by_plant, CYCLERS), grp(on_by_plant, CYCLERS)
        d_flat = abs(f_on - f_off) / f_off if f_off else 0.0
        d_cyc = abs(c_on - c_off) / c_off if c_off else 0.0
        g3 &= d_flat < G3_BAR
        g4 &= d_cyc < G4_BAR
        per_year[str(year)] = {
            "flat_off_twh": round(f_off / 1e6, 6),
            "flat_armB_twh": round(f_on / 1e6, 6),
            "flat_delta_pct": round(100 * d_flat, 4),
            "G3_pass": bool(d_flat < G3_BAR),
            "cyc_off_twh": round(c_off / 1e6, 6),
            "cyc_armB_twh": round(c_on / 1e6, 6),
            "cyc_delta_pct": round(100 * d_cyc, 4),
            "G4_pass": bool(d_cyc < G4_BAR),
            "plants": {
                str(code): {
                    "forced_mwh_off": round(off_by_plant.get(code, 0.0), 1),
                    "forced_mwh_armB": round(on_by_plant.get(code, 0.0), 1),
                }
                for code in sorted(CYCLERS)
            },
        }
        signed = (100 * d_cyc) if c_on >= c_off else (-100 * d_cyc)
        print(
            f"{year}: flat {f_off/1e6:.4f} -> {f_on/1e6:.4f} TWh "
            f"({100*d_flat:+.3f} %) G-3 {'PASS' if d_flat < G3_BAR else 'FAIL'} | "
            f"cyclers {c_off/1e6:.4f} -> {c_on/1e6:.4f} TWh ({signed:+.3f} %) "
            f"G-4 {'PASS' if d_cyc < G4_BAR else 'FAIL'}"
        )

    report["G3"] = g3
    report["G4"] = g4
    report["per_year"] = per_year
    OUT.write_text(json.dumps(report, indent=1))
    print(
        f"\nG-3 {g3} · G-4 {g4} · G-5 {g5['pass']}  =>  "
        f"{'ARM B CLEARS its zero-LP gates' if (g3 and g4 and g5['pass']) else 'ARM B does NOT clear'}"
    )
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
