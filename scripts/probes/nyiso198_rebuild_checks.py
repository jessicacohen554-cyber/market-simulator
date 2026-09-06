"""nyiso-198 F-1 / F-2 PRE-SOLVE GATES (NO LP) — rebuild the keeper's fleet
with ``cc_duct_peaking_row_scoped`` OFF (the keeper recipe) and ON (the arm),
and evaluate the footprint and identity gates of
``PREREG-nyiso198-duct-peaking-row-scope-screen.md`` §6 before an LP is spent.

* **F-1 footprint** — the peak band falls by 647.9 +/- 0.5 MW in total; the
  change is confined to exactly the 11 ``pct_peaking``-governed plants of the
  PREREG §4 table, each within 0.5 MW of its tabled value; ZERO change at the
  override plants (``chp_layup_duty_*`` / ``cc_reserve_duty_split``) and at the
  non-duct CC plants; and no non-combined-cycle fleet row changes at all.
* **F-2 identity** — every plant's TOTAL LP ``pmax`` is unchanged
  (sum of |delta| < 0.5 MW fleet-wide): the repair moves capacity between
  bands, it neither creates nor destroys any.

Writes ``results/calibration/_nyiso198_rebuild_checks_<year>.json``.

Usage::

    python scripts/probes/nyiso198_rebuild_checks.py [--year 2024]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    sys.path.insert(0, str(p))
from scripts.lib.bundle_fleet import (  # noqa: E402
    bundle_gas_price,
    clear_fleet_caches,
    ensure_probe_path,
    full_run_year_kwargs,
)

BUNDLE = ROOT / "results/calibration/nyiso196_extract_basis"
FLAG = "cc_duct_peaking_row_scoped"
CC_PREFIX = ("CC_REGULAR_", "CC_CHP_")
TOL_MW = 0.5
#: PREREG §4: the plants whose peak band pct_peaking actually governs, with the
#: MW each is expected to move (peak -> econ; negative = gains peak band).
EXPECTED = {
    57185: 168.47, 56940: 100.24, 54547: 87.98, 57664: 87.79, 2539: 75.91,
    56259: 48.38, 50292: 45.37, 54574: 32.96, 55375: 10.44, 56234: 9.03,
    56188: 3.03, 10190: -19.77, 54114: -1.84,
}
EXPECTED_TOTAL = 647.95


def rebuild(year: int, arm: bool):
    """On-recipe ``run_year(fleet_only=True)`` rebuild — the keeper's own
    recipe, with the arm adding EXACTLY the one flag through the generic
    ScenarioConfig override channel (the nyiso-196 construction)."""
    import pickle

    cache = ROOT / ".cache" / "nyiso198" / f"rebuild_{year}_{'arm' if arm else 'keeper'}.pkl"
    if cache.exists():
        return pickle.load(open(cache, "rb"))
    ensure_probe_path()
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = full_run_year_kwargs(meta)
    if arm:
        bag = dict(kwargs.get("prb_overrides") or {})
        bag[FLAG] = True
        kwargs["prb_overrides"] = bag
    clear_fleet_caches()
    state = run_year(
        year, meta["iso"], int(meta["hours"]), bundle_gas_price(meta, year), **kwargs
    )
    cfg = state["config"]
    fa_ref = state["fleet_arrays"]
    seen = {
        k: getattr(cfg, k)
        for k in dir(cfg)
        if not k.startswith("_") and isinstance(getattr(cfg, k, None), (bool, int, float, str, type(None)))
    }
    slim = {
        "unit_ids": list(fa_ref.unit_ids),
        "plant_code": [int(x) for x in fa_ref.plant_code],
        "pmax": [float(x) for x in fa_ref.pmax],
        "heat_rate": [float(x) for x in fa_ref.heat_rate],
    }
    cache.parent.mkdir(parents=True, exist_ok=True)
    pickle.dump((slim, seen), open(cache, "wb"))
    return slim, seen


def _bands(state):
    """Return per-plant {peak_mw, total_mw} and the non-CC row fingerprint."""
    pmax = np.asarray(state["pmax"])
    pcode = np.asarray(state["plant_code"])
    uids = list(state["unit_ids"])
    peak = defaultdict(float)
    total = defaultdict(float)
    noncc = {}
    for i, uid in enumerate(uids):
        if uid.startswith(CC_PREFIX):
            code = int(pcode[i])
            total[code] += float(pmax[i])
            if uid.endswith("_peak"):
                peak[code] += float(pmax[i])
        else:
            noncc[uid] = round(float(pmax[i]), 6)
    return dict(peak), dict(total), noncc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2024)
    a = ap.parse_args()
    yr = a.year

    off, meta_off = rebuild(yr, arm=False)
    on, meta_on = rebuild(yr, arm=True)
    pk_off, tot_off, noncc_off = _bands(off)
    pk_on, tot_on, noncc_on = _bands(on)

    codes = sorted(set(pk_off) | set(pk_on) | set(tot_off) | set(tot_on))
    moved, unexpected, mismatched = {}, [], []
    for c in codes:
        d = round(pk_off.get(c, 0.0) - pk_on.get(c, 0.0), 2)
        if abs(d) < 1e-6:
            continue
        moved[c] = d
        if c not in EXPECTED:
            unexpected.append({"plant": c, "delta_mw": d})
        elif abs(d - EXPECTED[c]) > TOL_MW:
            mismatched.append(
                {"plant": c, "delta_mw": d, "expected_mw": EXPECTED[c]}
            )
    missing = [c for c in EXPECTED if c not in moved and abs(EXPECTED[c]) > TOL_MW]
    total_moved = round(sum(moved.values()), 2)

    pmax_drift = {
        c: round(tot_on.get(c, 0.0) - tot_off.get(c, 0.0), 4)
        for c in codes
        if abs(tot_on.get(c, 0.0) - tot_off.get(c, 0.0)) > 1e-6
    }
    noncc_changed = [
        u for u in set(noncc_off) | set(noncc_on)
        if noncc_off.get(u) != noncc_on.get(u)
    ]

    f1 = {
        "total_peak_band_moved_mw": total_moved,
        "expected_total_mw": EXPECTED_TOTAL,
        "total_within_tol": abs(total_moved - EXPECTED_TOTAL) <= TOL_MW,
        "n_plants_moved": len(moved),
        "unexpected_movers": unexpected,
        "mismatched_movers": mismatched,
        "expected_movers_missing": missing,
        "noncc_rows_changed": sorted(noncc_changed),
        "PASS": bool(
            abs(total_moved - EXPECTED_TOTAL) <= TOL_MW
            and not unexpected
            and not mismatched
            and not missing
            and not noncc_changed
        ),
    }
    f2 = {
        "plants_with_total_pmax_drift": pmax_drift,
        "sum_abs_pmax_drift_mw": round(sum(abs(v) for v in pmax_drift.values()), 4),
        "g_delta": {
            k: [meta_off.get(k), meta_on.get(k)]
            for k in set(meta_off) | set(meta_on)
            if meta_off.get(k) != meta_on.get(k)
        },
        "PASS": bool(sum(abs(v) for v in pmax_drift.values()) < TOL_MW),
    }
    f2["g_delta_is_exactly_the_flag"] = list(f2["g_delta"]) == [FLAG]
    f2["PASS"] = bool(f2["PASS"] and f2["g_delta_is_exactly_the_flag"])

    out = {
        "session": "nyiso-198",
        "status": "F-1 / F-2 PRE-SOLVE GATES — NO LP",
        "year": yr,
        "flag": FLAG,
        "bundle": str(BUNDLE.relative_to(ROOT)),
        "moved_plants_mw": {str(k): v for k, v in sorted(moved.items())},
        "F1_footprint": f1,
        "F2_identity": f2,
        "VERDICT": "PASS" if (f1["PASS"] and f2["PASS"]) else "STOP",
    }
    dest = ROOT / f"results/calibration/_nyiso198_rebuild_checks_{yr}.json"
    dest.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "moved_plants_mw"}, indent=1))
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
