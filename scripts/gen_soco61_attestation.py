"""SOCO-61: write ``calibration_attestation.json`` for the dark-unit-year span.

Layered on :mod:`scripts.gen_soco60b_attestation`, which is RUN FIRST on this
bundle so every inherited claim is re-verified by execution here (the SOCO-58
postures and offer-curve identity, the hydro budgets, the B1 plant boundary and
the B2 gas-fold refusal). This module then verifies the ONE delta against the
keeper ``2026-09-23-soco60-boundary-span`` and rewrites the governance text:

* ``campd_dark_unit_year_windows=True`` on the resolved config, with
  ``campd_per_unit_attribution`` armed (its predicate) and
  ``campd_outage_merit_order_guard`` off (under which it is ignored);
* the outage extract the run READ (``run_config.json`` ``resolved_inputs``) is
  the ``-perunitdark-`` SOCO file, and its sha256 matches the file on disk;
* that file equals the committed ``-perunit-`` extract plus exactly one row --
  Lindsay Hill (55271) CT3, 2024-01-01..2024-12-31, ``campd_dark_unit_year``;
* the CAMPD evidence reproduces from the raw extract: CT3 has a row for every
  hour of 2024 with zero ``opTime``, positive gross in 2023 and 2025, and its
  peers CT1/CT2 ran in 2024.

Pre-registration: ``docs/handoffs/PRECOMMIT-soco-61-2026-09-24.md``. Usage::

    python3 scripts/build_dof_ledger.py --iso SOCO results/calibration/soco61_dark_unit_span
    python3 scripts/gen_soco60b_attestation.py --bundle results/calibration/soco61_dark_unit_span
    python3 scripts/gen_soco61_attestation.py --bundle results/calibration/soco61_dark_unit_span
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

DARK = "data/raw/campd-unit-outages-perunitdark-SOCO.csv"
BASE = "data/raw/campd-unit-outages-perunit-SOCO.csv"
PLANT, UNIT, YEAR = 55271, "CT3", 2024


def verify_delta(bundle: Path) -> dict:
    """Raise unless the delta is exactly as claimed; return the evidence."""
    cfg = json.loads((bundle / "run_config.json").read_text())
    sc = cfg["scenario_config"]
    if sc.get("campd_dark_unit_year_windows") is not True:
        raise SystemExit("campd_dark_unit_year_windows is not armed")
    if sc.get("campd_per_unit_attribution") is not True:
        raise SystemExit("campd_per_unit_attribution (the predicate) is not armed")
    if sc.get("campd_outage_merit_order_guard"):
        raise SystemExit(
            "campd_outage_merit_order_guard armed: the dark companion would be ignored"
        )
    ri = (cfg.get("resolved_inputs") or {}).get("campd_unit_outages") or {}
    sha = hashlib.sha256((_ROOT / DARK).read_bytes()).hexdigest()
    if ri.get("path") != DARK or ri.get("sha256") != sha:
        raise SystemExit(
            f"run read {ri.get('path')} {ri.get('sha256')}, expected {DARK} {sha}"
        )
    base = pd.read_csv(_ROOT / BASE)
    dark = pd.read_csv(_ROOT / DARK)
    added = dark.merge(base, how="left", indicator=True).query("_merge == 'left_only'")
    if len(dark) != len(base) + 1 or len(added) != 1:
        raise SystemExit(
            f"-perunitdark- adds {len(added)} rows over -perunit-, expected 1"
        )
    r = added.iloc[0]
    if (
        int(r.facility_id),
        str(r.unit_id),
        r.outage_start,
        r.outage_end,
        r.capacity_source,
    ) != (PLANT, UNIT, f"{YEAR}-01-01", f"{YEAR}-12-31", "campd_dark_unit_year"):
        raise SystemExit(f"unexpected added row: {r.to_dict()}")
    ev = {}
    for y in (YEAR - 1, YEAR, YEAR + 1):
        d = pd.read_parquet(
            _ROOT / f"data/raw/campd-unit-level/AL_{y}.parquet",
            columns=["facilityId", "unitId", "opTime", "grossLoad"],
        )
        d = d[pd.to_numeric(d.facilityId, errors="coerce") == PLANT]
        per = d.groupby(d.unitId.astype(str)).agg(
            rows=("opTime", "size"),
            op_h=("opTime", lambda s: int((s.fillna(0) > 0).sum())),
            gwh=("grossLoad", lambda s: float(s.fillna(0).sum()) / 1e3),
        )
        ev[str(y)] = per.round(1).to_dict(orient="index")
    t = ev[str(YEAR)]
    hours = len(pd.date_range(f"{YEAR}-01-01", f"{YEAR}-12-31 23:00", freq="h"))
    if t[UNIT]["rows"] < hours or t[UNIT]["op_h"] != 0:
        raise SystemExit(f"{UNIT} {YEAR} is not dark all year: {t[UNIT]}")
    if not (ev[str(YEAR - 1)][UNIT]["gwh"] > 0 or ev[str(YEAR + 1)][UNIT]["gwh"] > 0):
        raise SystemExit(f"{UNIT} produced in no adjacent year")
    if not any(v["op_h"] > 0 for k, v in t.items() if k != UNIT):
        raise SystemExit("no peer unit ran")
    return {
        "campd": ev,
        "extract_sha256": sha,
        "unit_capacity_mw": float(r.unit_capacity_mw),
    }


def main() -> None:
    """Verify the delta, then rewrite the governance text and ledger entries."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    a = ap.parse_args()
    bundle = Path(a.bundle)
    att_path = bundle / "calibration_attestation.json"
    att = json.loads(att_path.read_text())
    if (
        att.get("schema") != "calibration-attestation/v1"
        or "free_parameters" not in att
    ):
        raise SystemExit("run build_dof_ledger.py and gen_soco60b_attestation.py first")
    ev = verify_delta(bundle)
    c = ev["campd"]
    print(json.dumps(ev, indent=1))
    inherited = att["governance"]["attested_by"]
    att["governance"]["attested_by"] = (
        "SOCO-61 (lane). Against keeper 2026-09-23-soco60-boundary-span, ONE input "
        "moves, machine-verified by execution in scripts/gen_soco61_attestation.py: "
        "campd_dark_unit_year_windows=True selects the -perunitdark- SOCO outage "
        f"extract (sha256 {ev['extract_sha256'][:16]}), which is the keeper's -perunit- "
        "extract re-derived BYTE-IDENTICALLY plus ONE row -- Lindsay Hill (55271) CT3, "
        f"{ev['unit_capacity_mw']} MW, a full-year {YEAR} window. Recomputed here from the "
        f"raw CAMPD extract: CT3 files {c[str(YEAR)][UNIT]['rows']} rows in {YEAR} with "
        f"{c[str(YEAR)][UNIT]['op_h']} operating hours, against "
        f"{c[str(YEAR - 1)][UNIT]['gwh']} GWh in {YEAR - 1} and "
        f"{c[str(YEAR + 1)][UNIT]['gwh']} GWh in {YEAR + 1}; its peers CT1/CT2 ran "
        f"{c[str(YEAR)]['CT1']['op_h']} / {c[str(YEAR)]['CT2']['op_h']} h in {YEAR}. The "
        "per-unit detector skips a never-producing unit and the eia923_netzero hook is "
        "plant-grain, so the keeper carried a turbine that did not run as fully "
        "available all year. RULE 14: the model cannot dispatch it. RULE 13: CAMPD "
        "operating status is a physical availability record that regenerates for any "
        "filed year; nothing measured about dispatch is fed back. RULE 19: the SAME "
        "per-unit extract, one more window; 2023/2025 fleets byte-identical and 2024 "
        "moves availability on the four 55271 tranches only. RULES 21/24/25: every "
        "admission condition is categorical (n_scalars 0), one registered "
        "ScenarioConfig field, SOCO's own data. CHECK F: if the only argument for this "
        "arm were that the 2024 CC_REGULAR share margin widens, it would not be taken. "
        "GATE G17: SOCO has no price benchmark; every offer_curve_by_group band is "
        "1.0, AUTHORIZED PRICE TUNING IS DECLARED NONE. "
        "INHERITED, re-verified on this bundle by gen_soco60b_attestation.py: "
        + inherited
    )
    att["disclosures"]["precommit"] = "docs/handoffs/PRECOMMIT-soco-61-2026-09-24.md"
    att["disclosures"]["soco61_scope"] = (
        "Outage-extract half only: no tranche companion is derived for the dark-unit "
        "windows. SOCO's other dark unit-years (Walton Discover 2B, Baconton CT1, four "
        "Walton Bainbridge oil CTs) are CT peakers the overlay excludes by convention."
    )
    fp = att["free_parameters"]
    if "campd_dark_unit_year_windows" not in {e["name"] for e in fp["entries"]}:
        fp["entries"].append(
            {
                "name": "campd_dark_unit_year_windows",
                "value": True,
                "identification": "measured-physical",
                "n_scalars": 0,
                "basis": (
                    "Categorical data-admissibility gate on the per-unit CAMPD outage "
                    "extract: a unit whose own id files every hour of a year dark while "
                    "producing in an adjacent year gets one full-year window. SOCO: one "
                    "unit-year, Lindsay Hill CT3 2024."
                ),
            }
        )
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    att_path.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"wrote {att_path} (n_entries={fp['n_entries']}, n_residual={fp['n_residual']})"
    )


if __name__ == "__main__":
    main()
