"""caiso-198 — the G-DELTA kill-criterion investigation, reproducible. **NO LP.**

`PRECHECK-caiso198-desertstar-extract-2026-08-16.md` §4 G-DELTA / §5: the
in-place re-derive of `data/raw/campd-unit-outages-CAISO.csv` on the committed
CA+NV state list was NOT strictly additive — the pre-registered kill criterion
fired and the arm never ran. This probe reproduces the full investigation from
the committed tree (three scoped derives to a temp dir; `data/raw` untouched):

* **in-place shape** (detection CA+NV, panel CA+NV — the committed recipe as
  shipped): +158 facility-55077 rows PLUS 188 layup→mechanical and 87
  mechanical→layup reclassifications of CA-facility windows.
* **run X** (detection CA+NV, panel pinned to the committed CA scope): EXACTLY
  the committed extract + the identical 158 facility-55077 rows, layup
  companion byte-identical — the strictly-additive candidate.
* **run Y** (detection CA+NV, panel CA + facility 55077 only): Desert Star's
  own panel entry alone moves 9 windows mechanical→layup.

Attribution: the Desert Star DETECTION content (158 windows) is invariant to
panel scope; 100 % of the churn is the merit-order panel — a rank statistic
built from ALL CEMS units in the LOADED STATE FILES (`build_merit_order_panel`
is deliberately fleet-blind), so the NV widening put the 13–14 non-CAISO NV
Energy facilities (59–64 units) into CAISO's revealed-clearing-cost panel and
moved the RCC in 87–97 % of hours (mean +3.45 $/MWh in 2024). The panel-scope
question is escalated to the owner (FINDING-caiso198 §5); nothing here edits
the recipe.

Usage::

    python scripts/probes/_caiso198_extract_delta.py

Writes `results/calibration/_caiso198_extract_delta.json`. Runtime ~15 min
(three 9-year derives). The committed record in the repo was produced by this
construction at the caiso-198 session head; re-running verifies it.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "results" / "calibration" / "_caiso198_extract_delta.json"
EXTRACT = REPO / "data" / "raw" / "campd-unit-outages-CAISO.csv"
LAYUP = REPO / "data" / "raw" / "campd-unit-outages-layup-CAISO.csv"
UNIT_DIR = REPO / "data" / "raw" / "campd-unit-level"
YEARS = [str(y) for y in range(2018, 2027)]
FACILITY = 55077
COMMITTED_SHA_MAIN = "5f3e35c5dad88da76be8f684973fd7c78009f63e84d3f5b23a609e93d45fb4ce"
COMMITTED_SHA_LAYUP = "1475a57738c6de656938c65eebdd0f197013cac9a435cd09571a72c735b7bd43"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _derive(out_csv: Path, panel_dir: Path | None) -> None:
    """One committed-recipe derive; panel dir optionally scoped (panel only)."""
    import importlib

    import scripts.lib.outage_detect as od

    importlib.reload(od)  # reset any prior panel-dir override
    if panel_dir is not None:
        od._MERIT_UNIT_LEVEL_DIR = panel_dir
    import scripts.data.derive_campd_unit_outages as d

    importlib.reload(d)  # rebind the (possibly patched) outage_detect names
    argv_save = sys.argv
    sys.argv = [
        "derive_campd_unit_outages.py",
        "--iso", "CAISO",
        "--years", *YEARS,
        "--merit-order-guard",
        "--hour-grain",
        "--out", str(out_csv),
    ]
    try:
        d.main()
    finally:
        sys.argv = argv_save


def _accounting(candidate_main: Path, candidate_layup: Path) -> dict:
    """Window-set movement of one candidate vs the committed extract pair."""
    key = ["facility_id", "unit_id", "outage_start", "outage_end"]
    old_m, old_l = pd.read_csv(EXTRACT), pd.read_csv(LAYUP)
    new_m, new_l = pd.read_csv(candidate_main), pd.read_csv(candidate_layup)
    o_m = set(map(tuple, old_m[key].values))
    o_l = set(map(tuple, old_l[key].values))
    n_m = set(map(tuple, new_m[key].values))
    n_l = set(map(tuple, new_l[key].values))
    kept_rows_identical = [
        ln
        for ln in candidate_main.read_text().splitlines(keepends=True)[1:]
        if ln.split(",")[old_m.columns.get_loc("facility_id")].strip()
        != str(FACILITY)
    ] == EXTRACT.read_text().splitlines(keepends=True)[1:]
    return {
        "main_rows": len(new_m),
        "layup_rows": len(new_l),
        "added_55077": sum(1 for k in n_m - o_m if k[0] == FACILITY),
        "added_non_55077": sum(1 for k in n_m - o_m if k[0] != FACILITY),
        "removed_from_main": len(o_m - n_m),
        "left_layup": len(o_l - n_l),
        "entered_layup": len(n_l - o_l),
        "non_55077_rows_byte_identical_in_order": kept_rows_identical,
        "layup_byte_identical": candidate_layup.read_bytes() == LAYUP.read_bytes(),
        "sha256_main": _sha(candidate_main),
        "sha256_layup": _sha(candidate_layup),
    }


def main() -> None:
    if _sha(EXTRACT) != COMMITTED_SHA_MAIN or _sha(LAYUP) != COMMITTED_SHA_LAYUP:
        raise SystemExit(
            "data/raw extract pair is not at the committed caiso-197 bytes — "
            "this probe measures candidates AGAINST that baseline; restore first"
        )
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        panel_ca = tmp / "panel_ca_only"
        panel_ca_ds = tmp / "panel_ca_plus_ds"
        for p in (panel_ca, panel_ca_ds):
            p.mkdir()
        for f in sorted(UNIT_DIR.glob("CA_*.parquet")):
            (panel_ca / f.name).symlink_to(f)
            (panel_ca_ds / f.name).symlink_to(f)
        for f in sorted(UNIT_DIR.glob("NV_*.parquet")):
            df = pd.read_parquet(f)
            df[df["facilityId"] == str(FACILITY)].to_parquet(
                panel_ca_ds / f.name, index=False
            )
        runs = {}
        for tag, panel_dir in (
            ("inplace_recipe_ca_nv_panel", None),
            ("runX_panel_ca_only", panel_ca),
            ("runY_panel_ca_plus_ds", panel_ca_ds),
        ):
            out_csv = tmp / f"{tag}-campd-unit-outages-CAISO.csv"
            _derive(out_csv, panel_dir)
            runs[tag] = _accounting(
                out_csv, out_csv.with_name(f"{tag}-campd-unit-outages-layup-CAISO.csv")
            )
    result = {
        "precheck": "PRECHECK-caiso198-desertstar-extract-2026-08-16.md",
        "committed_sha_main": COMMITTED_SHA_MAIN,
        "committed_sha_layup": COMMITTED_SHA_LAYUP,
        "kill_criterion": "G-DELTA leg (b): any non-55077 byte => arm void",
        "runs": runs,
        "attribution": (
            "Desert Star detection content (158 windows) invariant to panel "
            "scope; all non-55077 movement is merit-panel composition "
            "(build_merit_order_panel is fleet-blind over the loaded state "
            "files, so the NV widening adds the non-CAISO NV fleet to the "
            "RCC panel)."
        ),
    }
    OUT.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
