"""caiso-199 — G-DELTA legs (a)–(d) + G-ENGAGE on the merit-panel scope pin.

`PRECHECK-caiso199-merit-panel-scope-2026-08-16.md` §4. Two stages, both
writing into the single committed record `_caiso199_panel_pin_gates.json`:

``--stage baseline`` (run BEFORE anything lands; **NO LP**)
    * **G-DELTA (a)** — with the DETECTION list temporarily `("CA",)` (patched
      in-process; no file is edited), the PINNED recipe must reproduce the
      committed extract byte-identically: main `5f3e35c5…`, layup `1475a577…`.
      This proves the pin is inert when the two scopes coincide, i.e. it
      changes nothing about the committed baseline.
    * **G-DELTA (b)** — with the committed `("CA","NV")` detection list, the
      PINNED recipe must reproduce the caiso-198 strictly-additive candidate
      byte-identically: main `da33e509…`, layup `1475a577…` (byte-identical to
      the committed companion). This is the cross-construction check: the
      caiso-198 candidate was produced by scoping the panel's DIRECTORY, this
      one by scoping its STATE LIST, which also narrows the coal-price table
      (PRECHECK §1b — a provable no-op, CA carries no CEMS coal in any year of
      the derive span; falsifiable here and gated as such).

    Both derives write to a scratch dir. Landing is a separate, explicit step
    (`--land`), taken only when both legs pass.

``--stage arm`` (run after the arm solve)
    * **G-DELTA (c)** — the landed diff is STRICTLY ADDITIVE: every added row
      is `facility_id == 55077`, every pre-existing row byte-identical and in
      order, layup companion byte-identical.
    * **G-DELTA (d)** — the g0-vs-g1 ``scenario_config`` diff is EMPTY over the
      full config.
    * **G-ENGAGE** — loader half: the shipped
      ``outages.unit_outage_derate_factors`` (keeper-faithful flags) resolves
      `(55077, "CC_REGULAR")` with mean multiplier < 1 in ≥ 1 solve year; LP
      half: the arm's hourly sidecars differ from the control's. A bit-identical
      arm is an INERT arm — reported as such, the intake kept on correctness.

Any byte outside the pinned shas ⇒ STOP; no sha in the PRECHECK may be edited
after the fact. Usage::

    python scripts/probes/_caiso199_panel_pin_gates.py --stage baseline
    python scripts/probes/_caiso199_panel_pin_gates.py --stage baseline --land
    python scripts/probes/_caiso199_panel_pin_gates.py --stage arm
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

CONTROL = REPO / "results" / "calibration" / "caiso199_g0_control"
ARM = REPO / "results" / "calibration" / "caiso199_g1_meritpin"
OUT = REPO / "results" / "calibration" / "_caiso199_panel_pin_gates.json"
EXTRACT = "data/raw/campd-unit-outages-CAISO.csv"
LAYUP = "data/raw/campd-unit-outages-layup-CAISO.csv"
YEARS = [2023, 2024, 2025]
DERIVE_YEARS = [str(y) for y in range(2018, 2027)]
FACILITY = 55077

# Pinned in PRECHECK-caiso199 §4 BEFORE any derive ran. Sources: the committed
# caiso-197 extract pair, and _caiso198_extract_delta.json runX_panel_ca_only.
SHA_COMMITTED_MAIN = "5f3e35c5dad88da76be8f684973fd7c78009f63e84d3f5b23a609e93d45fb4ce"
SHA_COMMITTED_LAYUP = "1475a57738c6de656938c65eebdd0f197013cac9a435cd09571a72c735b7bd43"
SHA_CANDIDATE_MAIN = "da33e509465911341ba0867aefe02214f2e8ccb666ef86747e0e7ad8b47c86bb"
SHA_CANDIDATE_LAYUP = SHA_COMMITTED_LAYUP  # strictly additive ⇒ layup untouched


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _derive(out_csv: Path, detection_states: tuple[str, ...]) -> tuple[Path, Path]:
    """One PINNED-recipe derive with the DETECTION list patched in-process.

    The panel scope always comes from ``campd.merit_panel_states_for_iso`` (the
    pin), never from ``detection_states`` — that separation is what is under
    test. Returns ``(main, layup)`` paths.
    """
    import importlib

    from market_sim.data import campd

    import scripts.data.derive_campd_unit_outages as d

    importlib.reload(d)
    saved_states = campd.ISO_STATES["CAISO"]
    argv_save = sys.argv
    campd.ISO_STATES["CAISO"] = detection_states
    sys.argv = [
        "derive_campd_unit_outages.py",
        "--iso", "CAISO",
        "--years", *DERIVE_YEARS,
        "--merit-order-guard",
        "--hour-grain",
        "--out", str(out_csv),
    ]
    try:
        d.main()
    finally:
        sys.argv = argv_save
        campd.ISO_STATES["CAISO"] = saved_states
    layup = out_csv.with_name(
        out_csv.name.replace("campd-unit-outages", "campd-unit-outages-layup", 1)
    )
    return out_csv, layup


def _stage_baseline(land: bool) -> dict:
    """G-DELTA legs (a) and (b); optionally land the leg-(b) product."""
    from market_sim.data import campd

    live_main, live_layup = REPO / EXTRACT, REPO / LAYUP
    if _sha(live_main) != SHA_COMMITTED_MAIN or _sha(live_layup) != SHA_COMMITTED_LAYUP:
        raise SystemExit(
            "data/raw extract pair is not at the committed caiso-197 bytes — "
            "the baseline proof measures against them; restore first"
        )
    legs: dict = {}
    landed = None
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for tag, detection, want_main, want_layup in (
            ("a_nv_excluded", ("CA",), SHA_COMMITTED_MAIN, SHA_COMMITTED_LAYUP),
            (
                "b_nv_included",
                tuple(campd.ISO_STATES["CAISO"]),
                SHA_CANDIDATE_MAIN,
                SHA_CANDIDATE_LAYUP,
            ),
        ):
            main_p, layup_p = _derive(
                tmp / f"{tag}-campd-unit-outages-CAISO.csv", detection
            )
            got_main, got_layup = _sha(main_p), _sha(layup_p)
            legs[tag] = {
                "detection_states": list(detection),
                "panel_states": list(campd.merit_panel_states_for_iso("CAISO")),
                "expected_main_sha256": want_main,
                "measured_main_sha256": got_main,
                "expected_layup_sha256": want_layup,
                "measured_layup_sha256": got_layup,
                "main_rows": sum(1 for _ in main_p.open()) - 1,
                "layup_rows": sum(1 for _ in layup_p.open()) - 1,
                "pass": got_main == want_main and got_layup == want_layup,
            }
            if tag == "b_nv_included" and legs[tag]["pass"] and land:
                shutil.copyfile(main_p, live_main)
                shutil.copyfile(layup_p, live_layup)
                landed = {
                    "main_sha256": _sha(live_main),
                    "layup_sha256": _sha(live_layup),
                }
    return {
        "legs": legs,
        "pass": all(v["pass"] for v in legs.values()),
        "landed": landed,
        "statement": (
            "Leg (a) proves the pin is INERT on the committed baseline (the two "
            "scopes coincide ⇒ committed bytes reproduce exactly). Leg (b) "
            "proves the STATE-LIST pin reproduces the caiso-198 "
            "DIRECTORY-scoped candidate byte-for-byte, confirming the §1b "
            "coal-table no-op claim."
        ),
    }


def _committed_lines(ref: str, path: str, want_sha: str) -> list[str]:
    """The committed file's lines from git (keepends), sha-verified."""
    blob = subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=REPO, check=True, capture_output=True
    ).stdout
    digest = hashlib.sha256(blob).hexdigest()
    if digest != want_sha:
        raise SystemExit(
            f"baseline ref {ref!r} does not carry the PRECHECK-pinned bytes for "
            f"{path}: sha256 {digest} != {want_sha}"
        )
    return blob.decode().splitlines(keepends=True)


def _additive_check(ref: str, path: str, want_sha: str) -> dict:
    """Strictly-additive row check for one CSV: non-55077 rows == committed."""
    old = _committed_lines(ref, path, want_sha)
    new = (REPO / path).read_text().splitlines(keepends=True)
    header_old, header_new = old[0], new[0]
    fac_col = header_old.rstrip("\n").split(",").index("facility_id")
    kept = [ln for ln in new[1:] if ln.split(",")[fac_col].strip() != str(FACILITY)]
    added = [ln for ln in new[1:] if ln.split(",")[fac_col].strip() == str(FACILITY)]
    committed_55077 = sum(
        1 for ln in old[1:] if ln.split(",")[fac_col].strip() == str(FACILITY)
    )
    return {
        "path": path,
        "header_identical": header_old == header_new,
        "committed_rows": len(old) - 1,
        "landed_rows": len(new) - 1,
        "committed_55077_rows": committed_55077,
        "added_55077_rows": len(added) - committed_55077,
        "removed_rows": len([ln for ln in old[1:] if ln not in set(new[1:])]),
        "non_55077_rows_byte_identical_in_order": kept == old[1:],
        "landed_sha256": _sha(REPO / path),
        "pass": header_old == header_new and kept == old[1:],
    }


def _stage_arm(ref: str) -> dict:
    """G-DELTA legs (c)/(d) + G-ENGAGE against the landed tree and the arms."""
    from market_sim.data.outages import unit_outage_derate_factors

    delta_extract = _additive_check(ref, EXTRACT, SHA_COMMITTED_MAIN)
    delta_layup = _additive_check(ref, LAYUP, SHA_COMMITTED_LAYUP)

    c = json.loads((CONTROL / "run_config.json").read_text())["scenario_config"]
    a = json.loads((ARM / "run_config.json").read_text())["scenario_config"]
    cfg_diff = {
        k: {"control": c.get(k), "arm": a.get(k)}
        for k in sorted(set(c) | set(a))
        if c.get(k) != a.get(k)
    }

    loader = {}
    for year in YEARS:
        factors = unit_outage_derate_factors(
            year, iso="CAISO", cc_steam_part_reclass=False, cc_nameplate_basis=True
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
    return {
        "control": CONTROL.name,
        "arm": ARM.name,
        "g_delta_c_extract": delta_extract,
        "g_delta_c_layup": delta_layup,
        "g_delta_d_config_diff": cfg_diff,
        "g_delta_pass": delta_extract["pass"] and delta_layup["pass"] and not cfg_diff,
        "g_engage_loader": loader,
        "g_engage_loader_resolves_lt1": loader_engaged,
        "g_engage_lp_differs": lp_differs,
        "g_engage_engagement": engagement,
        "g_engage_pass": loader_engaged and lp_differs,
        "arm_inert": not lp_differs,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", choices=("baseline", "arm"), required=True)
    ap.add_argument(
        "--land",
        action="store_true",
        help="baseline stage only: copy the leg-(b) product into data/raw "
        "(taken only when both legs pass)",
    )
    ap.add_argument(
        "--baseline-ref",
        default="a4205d1",
        help="git ref carrying the committed (pre-landing) extract bytes "
        "(default: the PRECHECK-caiso199 commit; sha-verified either way)",
    )
    args = ap.parse_args()

    result = json.loads(OUT.read_text()) if OUT.exists() else {}
    result["precheck"] = "PRECHECK-caiso199-merit-panel-scope-2026-08-16.md"
    result["pinned_shas"] = {
        "committed_main": SHA_COMMITTED_MAIN,
        "committed_layup": SHA_COMMITTED_LAYUP,
        "candidate_main": SHA_CANDIDATE_MAIN,
        "candidate_layup": SHA_CANDIDATE_LAYUP,
    }
    if args.stage == "baseline":
        result["g_delta_baseline"] = _stage_baseline(args.land)
        ok = result["g_delta_baseline"]["pass"]
    else:
        result["arm_stage"] = _stage_arm(args.baseline_ref)
        ok = result["arm_stage"]["g_delta_pass"]
    OUT.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
