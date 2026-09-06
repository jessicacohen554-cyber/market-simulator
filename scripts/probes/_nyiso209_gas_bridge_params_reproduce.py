"""nyiso-209 — does the NYISO gas-commitment-bridge parameter artifact reproduce at HEAD?

Zero LP. Reads ``data/raw`` only. Pre-registered in
``results/calibration/PREREG-nyiso209-gas-bridge-params-reproduce.md`` §4.

The instrument is the SHIPPED ``scripts/data/derive_campd_gas_commitment_params.py``,
run as a subprocess with its own defaults (``--iso NYISO --detail``, and ``--ct`` for
the control) and ``--out`` pointed at the scratchpad, so the committed artifact is
never overwritten. This probe then diffs:

* **M1** — the four keeper-live values (CC / ST_GAS ``min_load_frac`` and
  ``run_hours_p50_capwtd``) at full float precision and at the live 3-dp /
  integer seam ``ScenarioConfig`` consumes them at.
* **M2** — every other column of the 2-row class summary.
* **M3** — the HEAD ``class_plant_codes("NYISO")`` roster (imported from the shipped
  script by file path, never re-implemented) vs the plant set implied by the
  committed per-unit table.
* **M4** — the per-unit table: key set and per-key statistics.
* **M5** — the CT sibling artifact as instrument control.

Writes ``results/calibration/_nyiso209_gas_bridge_params_reproduce.json``.

Run:  PYTHONPATH=. uv run python scripts/probes/_nyiso209_gas_bridge_params_reproduce.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import PROCESSED_DIR, REPO_ROOT

SCRIPT = REPO_ROOT / "scripts" / "data" / "derive_campd_gas_commitment_params.py"
COMMITTED = PROCESSED_DIR / "campd_gas_commitment_params_NYISO.csv"
COMMITTED_UNITS = PROCESSED_DIR / "campd_gas_commitment_params_NYISO_units.csv"
COMMITTED_CT = PROCESSED_DIR / "campd_ct_commitment_params_NYISO.csv"
OUT_JSON = REPO_ROOT / "results" / "calibration" / "_nyiso209_gas_bridge_params_reproduce.json"

# Live seam (PREREG §1): ScenarioConfig carries the fractions at 3 dp and the
# run hours as integers.
LIVE = {
    "CC_REGULAR": {"min_load_frac": 0.523, "run_hours_p50_capwtd": 21.0},
    "ST_GAS": {"min_load_frac": 0.239, "run_hours_p50_capwtd": 13.0},
}
CT_LIVE = {"min_load_frac": 0.238, "run_hours_p25_capwtd": 2.0, "n_units": 80, "n_runs": 34024}
EXACT = 1e-9
UNIT_KEYS = ("hsl_mw", "lsl_mw", "lsl_frac", "online_hours", "n_runs", "median_run_hours")


def _scratch() -> Path:
    base = os.environ.get("NYISO209_SCRATCH")
    if base:
        p = Path(base)
    else:
        p = REPO_ROOT / "results" / "calibration" / "_nyiso209_scratch"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _run_shipped(args: list[str], out: Path) -> str:
    """Run the shipped derive script as a subprocess, its own defaults, --out to scratch."""
    cmd = [sys.executable, str(SCRIPT), "--iso", "NYISO", "--out", str(out), *args]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT, check=True)
    return res.stdout


def _load_shipped_module():
    spec = importlib.util.spec_from_file_location("_gas_commit_derive", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _f(x) -> float:
    return float(x)


def main() -> None:
    scratch = _scratch()
    rec: dict = {"prereg": "PREREG-nyiso209-gas-bridge-params-reproduce.md", "lp_spent": 0}

    # ---- run the shipped script (default classes, --detail) ---------------
    head_csv = scratch / "campd_gas_commitment_params_NYISO.csv"
    stdout = _run_shipped(["--detail"], head_csv)
    rec["shipped_stdout"] = stdout
    head = pd.read_csv(head_csv).set_index("plant_class")
    head_units = pd.read_csv(head_csv.with_name(head_csv.stem + "_units.csv"))
    comm = pd.read_csv(COMMITTED).set_index("plant_class")
    comm_units = pd.read_csv(COMMITTED_UNITS)

    # ---- M1: the four live values -----------------------------------------
    m1 = {}
    for klass, fields in LIVE.items():
        for col, live in fields.items():
            h = _f(head.loc[klass, col])
            c = _f(comm.loc[klass, col])
            seam = round(h, 3) if col == "min_load_frac" else float(h)
            m1[f"{klass}.{col}"] = {
                "committed": c,
                "head": h,
                "delta": h - c,
                "exact_1e-9": bool(abs(h - c) <= EXACT),
                "live_value": live,
                "head_at_live_seam": seam,
                "live_seam_holds": bool(abs(seam - live) <= EXACT),
            }
    rec["M1_live_values"] = m1
    rec["M1a_all_exact"] = all(v["exact_1e-9"] for v in m1.values())
    rec["M1b_all_live_seam"] = all(v["live_seam_holds"] for v in m1.values())

    # ---- M2: every other column ------------------------------------------
    m2 = {}
    skip = {"source", "years", "iso"}
    for klass in ("CC_REGULAR", "ST_GAS"):
        for col in comm.columns:
            if col in skip:
                continue
            h, c = _f(head.loc[klass, col]), _f(comm.loc[klass, col])
            m2[f"{klass}.{col}"] = {"committed": c, "head": h, "equal": bool(abs(h - c) <= EXACT)}
    rec["M2_other_columns"] = m2
    rec["M2_n_unequal"] = sum(0 if v["equal"] else 1 for v in m2.values())
    rec["M2_source_prose_identical"] = {
        k: bool(head.loc[k, "source"] == comm.loc[k, "source"]) for k in ("CC_REGULAR", "ST_GAS")
    }

    # ---- M3: roster -------------------------------------------------------
    mod = _load_shipped_module()
    mapping, ambiguous = mod.class_plant_codes("NYISO")
    comm_plants = (
        comm_units.groupby("plant_code")
        .agg(plant_class=("plant_class", "first"), plant_name=("plant_name", "first"))
        .reset_index()
    )
    comm_map = {int(r.plant_code): r.plant_class for r in comm_plants.itertuples()}
    names = {int(r.plant_code): r.plant_name for r in comm_plants.itertuples()}
    head_codes = set(mapping)
    comm_codes = set(comm_map)
    # Plants in the HEAD roster that contributed no committed unit row: either
    # genuinely new to the class, or present on 07-27 but with no CEMS hours
    # (the script silently drops those). Distinguish by whether HEAD produced
    # a unit row for them.
    head_unit_codes = set(int(c) for c in head_units["plant_code"].unique())
    m3 = {
        "head_n_target_plants": len(mapping),
        "head_by_class": {k: int(sum(1 for v in mapping.values() if v == k)) for k in ("CC_REGULAR", "ST_GAS")},
        "head_ambiguous_codes": [int(c) for c in ambiguous],
        "committed_unit_plants": {"CC_REGULAR": int((comm_plants.plant_class == "CC_REGULAR").sum()),
                                   "ST_GAS": int((comm_plants.plant_class == "ST_GAS").sum())},
        "committed_plant_absent_from_head_roster": [
            {"plant_code": c, "name": names[c], "committed_class": comm_map[c]}
            for c in sorted(comm_codes - head_codes)
        ],
        "committed_plant_reclassed_at_head": [
            {"plant_code": c, "name": names[c], "committed_class": comm_map[c], "head_class": mapping[c]}
            for c in sorted(comm_codes & head_codes)
            if mapping[c] != comm_map[c]
        ],
        "head_roster_plant_with_no_committed_units": [
            {"plant_code": c, "head_class": mapping[c], "has_head_unit_rows": bool(c in head_unit_codes)}
            for c in sorted(head_codes - comm_codes)
        ],
    }
    rec["M3_roster"] = m3

    # ---- M4: per-unit table ----------------------------------------------
    key = ["plant_code", "unit_id"]
    hu = head_units.assign(unit_id=head_units["unit_id"].astype(str)).set_index(key)
    cu = comm_units.assign(unit_id=comm_units["unit_id"].astype(str)).set_index(key)
    hk, ck = set(hu.index), set(cu.index)
    common = sorted(hk & ck)
    diffs = []
    for k in common:
        for col in UNIT_KEYS:
            h, c = _f(hu.loc[k, col]), _f(cu.loc[k, col])
            if not (abs(h - c) <= EXACT or (np.isnan(h) and np.isnan(c))):
                diffs.append({"plant_code": int(k[0]), "unit_id": k[1], "col": col, "committed": c, "head": h})
    m4 = {
        "committed_n_units": len(ck),
        "head_n_units": len(hk),
        "key_set_identical": bool(hk == ck),
        "only_committed": [{"plant_code": int(a), "unit_id": b, "plant_name": str(cu.loc[(a, b), "plant_name"]),
                            "class": str(cu.loc[(a, b), "plant_class"])} for a, b in sorted(ck - hk)],
        "only_head": [{"plant_code": int(a), "unit_id": b, "plant_name": str(hu.loc[(a, b), "plant_name"]),
                       "class": str(hu.loc[(a, b), "plant_class"])} for a, b in sorted(hk - ck)],
        "n_common": len(common),
        "n_common_stat_diffs": len(diffs),
        "common_stat_diffs": diffs[:50],
    }
    rec["M4_units"] = m4

    # ---- M5: CT control ---------------------------------------------------
    ct_csv = scratch / "campd_ct_commitment_params_NYISO.csv"
    rec["ct_stdout"] = _run_shipped(["--ct"], ct_csv)
    ct_head = pd.read_csv(ct_csv).iloc[0]
    ct_comm = pd.read_csv(COMMITTED_CT).iloc[0]
    m5 = {}
    for col, live in CT_LIVE.items():
        h, c = _f(ct_head[col]), _f(ct_comm[col])
        m5[col] = {"committed": c, "head": h, "exact_1e-9": bool(abs(h - c) <= EXACT), "live_value": live}
    m5["min_load_frac"]["live_seam_holds"] = bool(abs(round(_f(ct_head["min_load_frac"]), 3) - 0.238) <= EXACT)
    m5["n_columns_unequal"] = int(sum(
        0 if (abs(_f(ct_head[c]) - _f(ct_comm[c])) <= EXACT) else 1
        for c in ct_comm.index if c not in ("iso", "plant_class", "years", "source")
    ))
    rec["M5_ct_control"] = m5
    rec["P3_ct_reproduces"] = all(v["exact_1e-9"] for k, v in m5.items() if isinstance(v, dict))

    # ---- verdict (PREREG §6) ---------------------------------------------
    p1 = rec["M1a_all_exact"] and m4["key_set_identical"] and m4["n_common_stat_diffs"] == 0
    p3 = rec["P3_ct_reproduces"]
    if p1 and p3:
        verdict = "R — REPRODUCES"
    elif not p3 or (m4["key_set_identical"] and not rec["M1a_all_exact"]):
        verdict = "X — INSTRUMENT"
    elif (not m4["key_set_identical"]) and rec["M1b_all_live_seam"]:
        verdict = "D — ROSTER DRIFT, LIVE VALUES INTACT"
    elif not m4["key_set_identical"]:
        verdict = "U — UNIDENTIFIED"
    else:
        verdict = "R — REPRODUCES (key set identical; per-unit stat diffs > 0 but live values exact — see M4)"
    rec["P1_full_reproduction"] = bool(p1)
    rec["VERDICT"] = verdict

    OUT_JSON.write_text(json.dumps(rec, indent=1, default=str))
    print(json.dumps({k: rec[k] for k in ("M1_live_values", "M1a_all_exact", "M1b_all_live_seam",
                                          "M2_n_unequal", "M3_roster", "M4_units", "M5_ct_control",
                                          "P1_full_reproduction", "P3_ct_reproduces", "VERDICT")},
                     indent=1, default=str))
    print(f"wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
