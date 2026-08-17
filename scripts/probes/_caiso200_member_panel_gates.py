"""caiso-200 — G-MEMBER + G-DELTA legs (a)–(d) + G-ENGAGE on the fleet-member panel scope.

`PRECHECK-caiso200-panel-membership-2026-08-17.md` §4. Two stages, both
writing into the single committed record `_caiso200_member_panel_gates.json`:

``--stage baseline`` (run BEFORE anything lands; **NO LP**)
    * **G-MEMBER** — the derived member map (the deriver's own
      ``_merit_member_facilities`` over the real fleet registry and the
      committed detection list) resolves to EXACTLY ``{"NV": (55077,)}``.
      Anything else ⇒ STOP.
    * **G-DELTA (a)** — with the member scope DISABLED
      (``campd.MERIT_PANEL_FLEET_MEMBER_ISOS`` patched empty in-process), the
      committed recipe reproduces the COMMITTED pair byte-identically: main
      `da33e509…`, layup `1475a577…`. The narrowing's own baseline-inertness
      proof: the implementation changes nothing when unarmed.
    * **G-DELTA (b)** — with the member scope ARMED (as committed), the recipe
      reproduces the caiso-198 run-Y product byte-identically: main
      `cf156483…` (4,710 rows), layup `4ccae12e…` (819 rows). Cross-construction
      check: run Y scoped the panel DIRECTORY at the caiso-198 head; this
      scopes MEMBERSHIP at this head.
    * **Movement accounting + mover census** on the leg-(b) product vs the
      committed pair (window-key grained — the layup schema adds
      ``out_of_merit_share``): ALL 158 facility-55077 rows retained in main;
      EXACTLY 9 pre-existing CA-facility windows leave main and the SAME 9
      enter layup; zero additions; zero other movement. This is the §0a
      record-correction measurement (the movers are NOT Desert Star windows).
    * **factors_pre** — shipped-loader derate factors for every mover
      (facility, plant_group) in the solve years, measured on the committed
      bytes BEFORE landing (the loader is lru-cached and path-blind, so the
      pre side must be taken pre-landing — the caiso-192 disclosed defect).

    Both derives write to a scratch dir. Landing is a separate, explicit step
    (`--land`), taken only when every baseline gate passes.

``--stage arm`` (run after the h1 arm solve)
    * **G-DELTA (c)** — the LANDED pair vs the committed bytes from git:
      kept main rows byte-identical and in order; the 9 mover keys are the
      exact main→layup movement; layup's committed rows all retained.
    * **G-DELTA (d)** — the h0-vs-h1 ``scenario_config`` diff is EMPTY.
    * **G-ENGAGE** — loader half: factors_post (cache-cleared) differ from
      factors_pre for ≥ 1 mover key in ≥ 1 solve year (direction: availability
      RISES — windows were removed); LP half: the arm's hourly sidecars differ
      from the control's. A bit-identical arm is an INERT arm — reported as
      such, the intake kept on correctness.

Any byte outside the pinned shas ⇒ STOP; no sha in the PRECHECK may be edited
after the fact. Usage::

    python scripts/probes/_caiso200_member_panel_gates.py --stage baseline
    python scripts/probes/_caiso200_member_panel_gates.py --stage baseline --land
    python scripts/probes/_caiso200_member_panel_gates.py --stage arm
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
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

CONTROL = REPO / "results" / "calibration" / "caiso200_h0_control"
ARM = REPO / "results" / "calibration" / "caiso200_h1_memberpanel"
OUT = REPO / "results" / "calibration" / "_caiso200_member_panel_gates.json"
EXTRACT = "data/raw/campd-unit-outages-CAISO.csv"
LAYUP = "data/raw/campd-unit-outages-layup-CAISO.csv"
YEARS = [2023, 2024, 2025]
DERIVE_YEARS = [str(y) for y in range(2018, 2027)]
FACILITY = 55077
KEY = ["facility_id", "unit_id", "outage_start", "outage_end"]

# Pinned in PRECHECK-caiso200 §4 BEFORE any derive ran. Sources: the committed
# caiso-199 extract pair, and _caiso198_extract_delta.json runY_panel_ca_plus_ds.
SHA_COMMITTED_MAIN = "da33e509465911341ba0867aefe02214f2e8ccb666ef86747e0e7ad8b47c86bb"
SHA_COMMITTED_LAYUP = "1475a57738c6de656938c65eebdd0f197013cac9a435cd09571a72c735b7bd43"
SHA_RUNY_MAIN = "cf156483e08dcd701bd89898ca14670d3c797eb09d9ad30efc7f51cb381390b5"
SHA_RUNY_LAYUP = "4ccae12ebcfada3d6b716d02f25d81faaa4cfd49fedb22685449581cc6d9ed37"
EXPECTED_MEMBERS = {"NV": (55077,)}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _group_by_code() -> dict[int, str]:
    """The deriver's own non-ERCOT plant→group map, reproduced exactly."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv, load_retired_within_window

    cfg = get_iso_config("CAISO")
    fleet = load_fleet_from_csv("CAISO", cfg) + load_retired_within_window(
        "CAISO", cfg
    )
    return {
        int(g.plant_code): g.plant_group
        for g in fleet
        if int(g.plant_code) > 0 and g.plant_group
    }


def _derive(out_csv: Path, member_scope_on: bool) -> tuple[Path, Path]:
    """One committed-recipe derive with the member scope armed or disabled."""
    import importlib

    from market_sim.data import campd

    import scripts.data.derive_campd_unit_outages as d

    importlib.reload(d)
    saved = campd.MERIT_PANEL_FLEET_MEMBER_ISOS
    argv_save = sys.argv
    if not member_scope_on:
        campd.MERIT_PANEL_FLEET_MEMBER_ISOS = frozenset()
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
        campd.MERIT_PANEL_FLEET_MEMBER_ISOS = saved
    layup = out_csv.with_name(
        out_csv.name.replace("campd-unit-outages", "campd-unit-outages-layup", 1)
    )
    return out_csv, layup


def _keyset(df: pd.DataFrame) -> set[tuple]:
    return set(map(tuple, df[KEY].astype(str).values))


def _movement(cand_main: Path, cand_layup: Path, old_main: pd.DataFrame,
              old_layup: pd.DataFrame) -> dict:
    """Window-key movement of the candidate pair vs the committed pair."""
    new_m, new_l = pd.read_csv(cand_main), pd.read_csv(cand_layup)
    o_m, o_l = _keyset(old_main), _keyset(old_layup)
    n_m, n_l = _keyset(new_m), _keyset(new_l)
    left_main = o_m - n_m
    entered_layup = n_l - o_l
    movers = new_l[new_l[KEY].astype(str).apply(tuple, axis=1).isin(entered_layup)]
    ds_rows_main = int((new_m["facility_id"].astype(int) == FACILITY).sum())
    census = [
        {
            "facility_id": int(r.facility_id),
            "facility_name": str(r.facility_name),
            "unit_id": str(r.unit_id),
            "plant_group": str(r.plant_group),
            "outage_start": str(r.outage_start),
            "outage_end": str(r.outage_end),
            "duration_days": float(r.duration_days),
            "out_of_merit_share": float(r.out_of_merit_share),
        }
        for r in movers.itertuples(index=False)
    ]
    return {
        "main_rows": len(new_m),
        "layup_rows": len(new_l),
        "ds_rows_retained_in_main": ds_rows_main,
        "left_main": len(left_main),
        "entered_layup": len(entered_layup),
        "movement_key_symmetric": left_main == entered_layup,
        "added_to_main": len(n_m - o_m),
        "left_layup": len(o_l - n_l),
        "mover_census": census,
        "pass": (
            ds_rows_main == 158
            and len(left_main) == 9
            and left_main == entered_layup
            and not (n_m - o_m)
            and not (o_l - n_l)
            and all(c["facility_id"] != FACILITY for c in census)
        ),
    }


def _mover_factor_keys(census: list[dict]) -> list[tuple[int, str]]:
    return sorted({(c["facility_id"], c["plant_group"]) for c in census})


def _loader_factors(keys: list[tuple[int, str]]) -> dict:
    """Shipped-loader derate factors for the mover keys, solve years."""
    from market_sim.data.outages import unit_outage_derate_factors

    unit_outage_derate_factors.cache_clear()
    out: dict = {}
    for year in YEARS:
        factors = unit_outage_derate_factors(
            year, iso="CAISO", cc_steam_part_reclass=False, cc_nameplate_basis=True
        )
        yr = {}
        for fid, group in keys:
            arr = factors.get((fid, group))
            yr[f"{fid}:{group}"] = (
                {
                    "mean_multiplier": float(np.mean(arr)),
                    "hours_below_1": int((arr < 1.0).sum()),
                }
                if arr is not None
                else None
            )
        out[year] = yr
    return out


def _stage_baseline(land: bool) -> dict:
    """G-MEMBER + G-DELTA legs (a)/(b) + movement + factors_pre; optional landing."""
    from market_sim.data import campd

    import scripts.data.derive_campd_unit_outages as deriver

    live_main, live_layup = REPO / EXTRACT, REPO / LAYUP
    if _sha(live_main) != SHA_COMMITTED_MAIN or _sha(live_layup) != SHA_COMMITTED_LAYUP:
        raise SystemExit(
            "data/raw extract pair is not at the committed caiso-199 bytes — "
            "the baseline proof measures against them; restore first"
        )
    old_main, old_layup = pd.read_csv(live_main), pd.read_csv(live_layup)

    members = deriver._merit_member_facilities(
        campd.states_for_iso("CAISO"),
        campd.merit_panel_states_for_iso("CAISO"),
        DERIVE_YEARS,
        _group_by_code(),
    )
    g_member = {
        "derived": {k: list(v) for k, v in members.items()},
        "expected": {k: list(v) for k, v in EXPECTED_MEMBERS.items()},
        "pass": members == EXPECTED_MEMBERS,
    }
    if not g_member["pass"]:
        return {"g_member": g_member, "pass": False, "stopped": "G-MEMBER"}

    legs: dict = {}
    landed = None
    movement = None
    factors_pre = None
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for tag, scope_on, want_main, want_layup in (
            ("a_member_scope_off", False, SHA_COMMITTED_MAIN, SHA_COMMITTED_LAYUP),
            ("b_member_scope_armed", True, SHA_RUNY_MAIN, SHA_RUNY_LAYUP),
        ):
            main_p, layup_p = _derive(
                tmp / f"{tag}-campd-unit-outages-CAISO.csv", scope_on
            )
            got_main, got_layup = _sha(main_p), _sha(layup_p)
            legs[tag] = {
                "member_scope_on": scope_on,
                "expected_main_sha256": want_main,
                "measured_main_sha256": got_main,
                "expected_layup_sha256": want_layup,
                "measured_layup_sha256": got_layup,
                "main_rows": sum(1 for _ in main_p.open()) - 1,
                "layup_rows": sum(1 for _ in layup_p.open()) - 1,
                "pass": got_main == want_main and got_layup == want_layup,
            }
            if tag == "b_member_scope_armed" and legs[tag]["pass"]:
                movement = _movement(main_p, layup_p, old_main, old_layup)
                factors_pre = _loader_factors(
                    _mover_factor_keys(movement["mover_census"])
                )
                if land and movement["pass"]:
                    shutil.copyfile(main_p, live_main)
                    shutil.copyfile(layup_p, live_layup)
                    landed = {
                        "main_sha256": _sha(live_main),
                        "layup_sha256": _sha(live_layup),
                    }
    ok = (
        g_member["pass"]
        and all(v["pass"] for v in legs.values())
        and movement is not None
        and movement["pass"]
    )
    return {
        "g_member": g_member,
        "legs": legs,
        "movement": movement,
        "factors_pre_committed_bytes": factors_pre,
        "pass": ok,
        "landed": landed,
        "statement": (
            "Leg (a) proves the member-scope implementation is INERT when "
            "unarmed (committed bytes reproduce exactly) — the narrowing's own "
            "baseline byte-identity proof. Leg (b) proves MEMBERSHIP scoping "
            "at this head reproduces the caiso-198 run-Y DIRECTORY-scoped "
            "product byte-for-byte. The movement census is the §0a record "
            "correction, measured."
        ),
    }


def _committed_blob(ref: str, path: str, want_sha: str) -> bytes:
    """The committed file's bytes from git, sha-verified."""
    blob = subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=REPO, check=True, capture_output=True
    ).stdout
    digest = hashlib.sha256(blob).hexdigest()
    if digest != want_sha:
        raise SystemExit(
            f"baseline ref {ref!r} does not carry the PRECHECK-pinned bytes for "
            f"{path}: sha256 {digest} != {want_sha}"
        )
    return blob


def _stage_arm(ref: str) -> dict:
    """G-DELTA legs (c)/(d) + G-ENGAGE against the landed tree and the arms."""
    prior = json.loads(OUT.read_text())
    census = prior["baseline"]["movement"]["mover_census"]
    factors_pre = prior["baseline"]["factors_pre_committed_bytes"]
    mover_keys = {(c["facility_id"], c["unit_id"], c["outage_start"], c["outage_end"])
                  for c in census}

    old_main_blob = _committed_blob(ref, EXTRACT, SHA_COMMITTED_MAIN)
    old_layup_blob = _committed_blob(ref, LAYUP, SHA_COMMITTED_LAYUP)
    new_main_p, new_layup_p = REPO / EXTRACT, REPO / LAYUP

    # Kept-row byte identity, in order: new main lines == old main lines minus
    # the 9 mover lines; old layup lines form an in-order subsequence of new.
    old_lines = old_main_blob.decode().splitlines(keepends=True)
    new_lines = new_main_p.read_text().splitlines(keepends=True)
    fac_col = old_lines[0].rstrip("\n").split(",").index("facility_id")
    uid_col = old_lines[0].rstrip("\n").split(",").index("unit_id")
    start_col = old_lines[0].rstrip("\n").split(",").index("outage_start")
    end_col = old_lines[0].rstrip("\n").split(",").index("outage_end")

    def _linekey(ln: str) -> tuple:
        f = ln.split(",")
        return (int(f[fac_col]), f[uid_col], f[start_col], f[end_col])

    expected_kept = [
        ln for ln in old_lines[1:] if _linekey(ln) not in mover_keys
    ]
    main_kept_identical = new_lines[1:] == expected_kept
    header_identical = old_lines[0] == new_lines[0]

    old_l_lines = old_layup_blob.decode().splitlines(keepends=True)
    new_l_lines = new_layup_p.read_text().splitlines(keepends=True)
    it = iter(new_l_lines[1:])
    layup_subseq = all(any(o == n for n in it) for o in old_l_lines[1:])
    added_l = [ln for ln in new_l_lines[1:] if ln not in set(old_l_lines[1:])]
    layup_added_are_movers = (
        {_linekey(ln) for ln in added_l} == mover_keys and len(added_l) == 9
    )
    delta_c = {
        "landed_main_sha256": _sha(new_main_p),
        "landed_layup_sha256": _sha(new_layup_p),
        "header_identical": header_identical,
        "main_kept_rows_byte_identical_in_order": main_kept_identical,
        "layup_committed_rows_in_order_subsequence": layup_subseq,
        "layup_added_rows_are_exactly_the_movers": layup_added_are_movers,
        "pass": (
            _sha(new_main_p) == SHA_RUNY_MAIN
            and _sha(new_layup_p) == SHA_RUNY_LAYUP
            and header_identical
            and main_kept_identical
            and layup_subseq
            and layup_added_are_movers
        ),
    }

    c = json.loads((CONTROL / "run_config.json").read_text())["scenario_config"]
    a = json.loads((ARM / "run_config.json").read_text())["scenario_config"]
    cfg_diff = {
        k: {"control": c.get(k), "arm": a.get(k)}
        for k in sorted(set(c) | set(a))
        if c.get(k) != a.get(k)
    }

    factors_post = _loader_factors(
        sorted({(c_["facility_id"], c_["plant_group"]) for c_ in census})
    )
    # factors_pre round-trips through JSON, so its year keys are strings.
    loader_moved = any(
        (factors_post[y].get(k) or {}) != (factors_pre[str(y)].get(k) or {})
        for y in YEARS
        for k in factors_post[y]
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
        "g_delta_c": delta_c,
        "g_delta_d_config_diff": cfg_diff,
        "g_delta_pass": delta_c["pass"] and not cfg_diff,
        "g_engage_factors_post": factors_post,
        "g_engage_loader_moved": loader_moved,
        "g_engage_lp_differs": lp_differs,
        "g_engage_engagement": engagement,
        "g_engage_pass": lp_differs,
        "arm_inert": not lp_differs,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", choices=("baseline", "arm"), required=True)
    ap.add_argument(
        "--land",
        action="store_true",
        help="baseline stage only: copy the leg-(b) product into data/raw "
        "(taken only when every baseline gate passes)",
    )
    ap.add_argument(
        "--baseline-ref",
        default="45254f1",
        help="git ref carrying the committed (pre-landing) extract bytes "
        "(default: the PRECHECK-caiso200 commit; sha-verified either way)",
    )
    args = ap.parse_args()

    result = json.loads(OUT.read_text()) if OUT.exists() else {}
    result["precheck"] = "PRECHECK-caiso200-panel-membership-2026-08-17.md"
    result["pinned_shas"] = {
        "committed_main": SHA_COMMITTED_MAIN,
        "committed_layup": SHA_COMMITTED_LAYUP,
        "runY_main": SHA_RUNY_MAIN,
        "runY_layup": SHA_RUNY_LAYUP,
    }
    if args.stage == "baseline":
        result["baseline"] = _stage_baseline(args.land)
        ok = result["baseline"]["pass"]
    else:
        result["arm_stage"] = _stage_arm(args.baseline_ref)
        ok = result["arm_stage"]["g_delta_pass"]
    OUT.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
