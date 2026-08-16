"""caiso-198 — G-DELTA legs (b)/(c) + G-ENGAGE on the Desert Star extract A/B.

`PRECHECK-caiso198-desertstar-extract-2026-08-16.md` §4:

* **G-DELTA (b)** — the re-derived ``data/raw/campd-unit-outages-CAISO.csv``
  (and its layup companion) is STRICTLY ADDITIVE against the committed bytes
  (read from git, ``<baseline_ref>:<path>``): the sequence of rows with
  ``facility_id != 55077`` must equal the committed row sequence exactly
  (byte-identical, in order), the header identical, and every remaining row
  must carry ``facility_id == 55077``. Any other change ⇒ FAIL (void).
* **G-DELTA (c)** — the f0-vs-f1 ``scenario_config`` diff is EMPTY over the
  FULL config of the two bundles' committed ``run_config.json``.
* **G-ENGAGE** — loader half: the shipped
  ``outages.unit_outage_derate_factors`` (keeper-faithful flags:
  ``cc_steam_part_reclass=False``, ``cc_nameplate_basis=True`` =
  ``unit_outage_lp_capacity_basis``) resolves ``(55077, "CC_REGULAR")`` with
  mean multiplier < 1 in ≥ 1 solve year; LP half: the two bundles' hourly
  sidecars differ (zone-hours with changed prices; class-hour dispatch
  deltas). Model artifacts only — no actuals, no fit statistic (the
  direction-hazard regime stays intact).

Usage (run AFTER the repair lands on disk and both arms are solved)::

    python scripts/probes/_caiso198_ab_gates.py [--baseline-ref <git-ref>]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

CONTROL = REPO / "results" / "calibration" / "caiso198_f0_control"
ARM = REPO / "results" / "calibration" / "caiso198_f1_desertstar"
YEARS = [2023, 2024, 2025]
OUT = REPO / "results" / "calibration" / "_caiso198_ab_gates.json"
FACILITY = 55077
EXTRACT = "data/raw/campd-unit-outages-CAISO.csv"
LAYUP = "data/raw/campd-unit-outages-layup-CAISO.csv"
# The committed-extract baseline the PRECHECK §1 pins (sha256 5f3e35c5… /
# 1475a577…). The default ref is the PRECHECK commit itself, which predates
# the repair commit by construction; any ref carrying those bytes verifies
# identically (the sha check below is what actually binds).
COMMITTED_SHA = {
    EXTRACT: "5f3e35c5dad88da76be8f684973fd7c78009f63e84d3f5b23a609e93d45fb4ce",
    LAYUP: "1475a57738c6de656938c65eebdd0f197013cac9a435cd09571a72c735b7bd43",
}


def _committed_lines(ref: str, path: str) -> list[str]:
    """The committed file's lines from git (keepends), sha-verified."""
    import hashlib

    blob = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout
    digest = hashlib.sha256(blob).hexdigest()
    if digest != COMMITTED_SHA[path]:
        raise SystemExit(
            f"baseline ref {ref!r} does not carry the PRECHECK-pinned bytes for "
            f"{path}: sha256 {digest} != {COMMITTED_SHA[path]}"
        )
    return blob.decode().splitlines(keepends=True)


def _facility_of(line: str, fac_col: int) -> str:
    return line.split(",")[fac_col].strip()


def _additive_check(ref: str, path: str) -> dict:
    """Strictly-additive row check for one CSV: non-55077 rows == committed."""
    old = _committed_lines(ref, path)
    new = (REPO / path).read_text().splitlines(keepends=True)
    header_old, header_new = old[0], new[0]
    fac_col = header_old.rstrip("\n").split(",").index("facility_id")
    kept = [ln for ln in new[1:] if _facility_of(ln, fac_col) != str(FACILITY)]
    added = [ln for ln in new[1:] if _facility_of(ln, fac_col) == str(FACILITY)]
    ok = header_old == header_new and kept == old[1:]
    return {
        "path": path,
        "header_identical": header_old == header_new,
        "committed_rows": len(old) - 1,
        "rederived_rows": len(new) - 1,
        "added_55077_rows": len(added),
        "non_55077_rows_byte_identical_in_order": kept == old[1:],
        "pass": ok,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--baseline-ref",
        default="ddebbfd94",
        help="git ref carrying the committed (pre-repair) extract bytes "
        "(default: the PRECHECK-caiso198 commit; sha-verified either way)",
    )
    args = ap.parse_args()

    delta_extract = _additive_check(args.baseline_ref, EXTRACT)
    delta_layup = _additive_check(args.baseline_ref, LAYUP)

    c = json.loads((CONTROL / "run_config.json").read_text())["scenario_config"]
    a = json.loads((ARM / "run_config.json").read_text())["scenario_config"]
    cfg_diff = {
        k: {"control": c.get(k), "arm": a.get(k)}
        for k in sorted(set(c) | set(a))
        if c.get(k) != a.get(k)
    }

    from market_sim.data.outages import unit_outage_derate_factors

    loader = {}
    for year in YEARS:
        factors = unit_outage_derate_factors(
            year,
            iso="CAISO",
            cc_steam_part_reclass=False,
            cc_nameplate_basis=True,
        )
        arr = factors.get((FACILITY, "CC_REGULAR"))
        loader[year] = (
            {
                "resolved": True,
                "mean_multiplier": float(np.mean(arr)),
                "hours_below_1": int((arr < 1.0).sum()),
                "hours_total": int(arr.size),
            }
            if arr is not None
            else {"resolved": False}
        )
    loader_engaged = any(
        y["resolved"] and y["mean_multiplier"] < 1.0 for y in loader.values()
    )

    engagement = {}
    for year in YEARS:
        sys_c = pq.read_table(CONTROL / "hourly" / f"system_{year}.parquet")
        sys_a = pq.read_table(ARM / "hourly" / f"system_{year}.parquet")
        pc = sys_c.column("price").to_numpy(zero_copy_only=False).astype(float)
        pa = sys_a.column("price").to_numpy(zero_copy_only=False).astype(float)
        cls_c = pq.read_table(CONTROL / "hourly" / f"class_hourly_{year}.parquet")
        cls_a = pq.read_table(ARM / "hourly" / f"class_hourly_{year}.parquet")
        mc = cls_c.column("mw").to_numpy(zero_copy_only=False).astype(float)
        ma = cls_a.column("mw").to_numpy(zero_copy_only=False).astype(float)
        engagement[year] = {
            "zone_hours_price_changed": int((pc != pa).sum()),
            "zone_hours_total": int(len(pc)),
            "max_abs_price_delta": float(np.max(np.abs(pc - pa))),
            "class_hours_mw_changed": int((mc != ma).sum()),
            "max_abs_mw_delta": float(np.max(np.abs(mc - ma))),
        }
    lp_differs = any(
        e["zone_hours_price_changed"] > 0 or e["class_hours_mw_changed"] > 0
        for e in engagement.values()
    )

    out = {
        "control": CONTROL.name,
        "arm": ARM.name,
        "precheck": "PRECHECK-caiso198-desertstar-extract-2026-08-16.md",
        "g_delta_extract": delta_extract,
        "g_delta_layup": delta_layup,
        "g_delta_config_diff": cfg_diff,
        "g_delta_pass": (
            delta_extract["pass"] and delta_layup["pass"] and not cfg_diff
        ),
        "g_engage_loader": loader,
        "g_engage_loader_resolves_lt1": loader_engaged,
        "g_engage_lp_differs": lp_differs,
        "g_engage_pass": loader_engaged and lp_differs,
        "arm_inert": not lp_differs,
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    sys.exit(0 if out["g_delta_pass"] else 2)


if __name__ == "__main__":
    main()
