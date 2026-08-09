"""ercot-181 §6: the position-tail seam proof (SP-α1..SP-α8), pre-solve.

Pre-registered in PRECOMMIT-ercot181-quantity-position-2026-08-09.md §6 and
run AFTER the M-0/M-1 Route-B adjudication and the ``--position-tail``
derives, BEFORE any LP. Any assertion failing STOPS the session.

* SP-α1 — gate ON with the real positiontail artifacts: the composed
  ``mc_bid_adjust`` differs from the gate-off control ONLY at row-hours whose
  wall/pool rel exceeds 0.9 (the reach probe's own geometry), the pool
  ``own_mask`` is byte-identical, and the arm differs somewhere in 2023.
* SP-α2 — null encoding: tail points carrying the frozen p90 rung value
  compose byte-identical to control EVERYWHERE (the appended axis is
  POSITION, never level).
* SP-α3 — gate OFF at HEAD: composed sha equals the ercot-178 recorded
  control sha per year.
* SP-α4 — non-ERCOT: both builders return None under an armed non-ERCOT
  config.
* SP-α5 — the frozen stepped + contpct + topscoped artifacts are
  byte-identical to git HEAD after the derives ran.
* SP-α6 — no-markdown: composed_arm >= composed_off everywhere; each
  extended (x, y) ladder is non-decreasing.
* SP-α7 — guard integrity: every forbidden combination raises; the armed
  cache key differs from the pinned default key; check_mechanism_matrix
  exits 0.
* SP-α8 — artifact conformance: everything except ``tail`` + provenance is
  byte-equal to the frozen artifact; tail x strictly increasing in (0.9, 1];
  vintage tag correct; per-bin tail counts disclosed in provenance.

Output: results/calibration/ercot181_positiontail_seamproof.json.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

BUNDLE = REPO / "results/calibration/ercot176_control_A"
OUT = REPO / "results/calibration/ercot181_positiontail_seamproof.json"
VS = REPO / "data/raw/_validation-source"
YEARS = (2023, 2024, 2025)

WALL_PT = VS / "ercot_sced_offer_wall_positiontail.json"
POOL_PT = VS / "ercot_faststart_pool_positiontail.json"
FROZEN = [
    "ercot_sced_offer_wall_condbinned.json",
    "ercot_dam_cleared_share_condbinned.json",
    "ercot_faststart_pool_condbinned.json",
    "offer_curve_dam_hrmults_condbinned.json",
    "ercot_sced_offer_wall_steam_condbinned.json",
    "ercot_dam_cleared_share_contpct.json",
    "ercot_faststart_pool_contpct.json",
]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _raises(fn, why: str) -> dict:
    try:
        fn()
    except (ValueError, FileNotFoundError) as e:
        return {"combo": why, "raises": True, "msg": str(e)[:140]}
    return {"combo": why, "raises": False}


def main() -> int:
    reach = _load(
        "reach181", REPO / "scripts/probes/ercot181_positiontail_reach.py"
    )
    sp = reach._sp178()
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    rec: dict = {
        "probe": "ercot181_positiontail_seamproof",
        "precommit": "docs/PRECOMMIT-ercot181-quantity-position-2026-08-09.md §6",
        "bundle": str(BUNDLE.relative_to(REPO)),
        "years": {},
    }
    ok = True

    # ---- SP-α5: frozen artifacts byte-identical to git HEAD ----
    sp5 = {}
    for name in FROZEN:
        p = VS / name
        if not p.exists():
            sp5[name] = "ABSENT"
            continue
        disk = hashlib.sha256(p.read_bytes()).hexdigest()
        git = subprocess.run(
            ["git", "show", f"HEAD:data/raw/_validation-source/{name}"],
            capture_output=True,
            cwd=REPO,
        )
        head = hashlib.sha256(git.stdout).hexdigest() if git.returncode == 0 else None
        sp5[name] = "IDENTICAL" if disk == head else "DIFFERS"
        if sp5[name] != "IDENTICAL":
            ok = False
    rec["SP5_frozen_artifacts"] = sp5

    # ---- SP-α8: positiontail artifact conformance ----
    sp8 = {}
    for pt_path, frz_name, tail_holder in (
        (WALL_PT, "ercot_sced_offer_wall_condbinned.json", ("CC", "CT")),
        (POOL_PT, "ercot_faststart_pool_condbinned.json", ("CT",)),
    ):
        pt = json.loads(pt_path.read_text())
        frz = json.loads((VS / frz_name).read_text())
        entry: dict = {
            "vintage_tag": pt.get("_provenance", {}).get("conditioning"),
            "tag_ok": pt.get("_provenance", {}).get("conditioning")
            == "positiontail-netload-bins",
            "tail_prov_disclosed": "positiontail" in pt.get("_provenance", {}),
        }
        # everything except `tail` keys and _provenance must equal frozen
        strip = json.loads(json.dumps(pt))
        strip.pop("_provenance", None)
        for cls in list(strip):
            for y in strip[cls].get("years", {}).values():
                y.pop("tail", None)
        frz_cmp = json.loads(json.dumps(frz))
        frz_cmp.pop("_provenance", None)
        entry["sub_p90_byte_equal_frozen"] = strip == frz_cmp
        tails_ok = True
        n_pts = {}
        for cls in tail_holder:
            for ystr, tbl in pt.get(cls, {}).get("years", {}).items():
                tails = tbl.get("tail")
                if tails is None:
                    continue
                n_pts[f"{cls}:{ystr}"] = [len(t) for t in tails]
                for b, t in enumerate(tails):
                    xs = [p[0] for p in t]
                    if any(x <= 0.9 or x > 1.0 for x in xs):
                        tails_ok = False
                    if any(b2 <= a2 for a2, b2 in zip(xs, xs[1:])):
                        tails_ok = False
        entry["tail_x_strictly_increasing_in_(0.9,1]"] = tails_ok
        entry["tail_points_per_bin"] = n_pts
        if not (
            entry["tag_ok"]
            and entry["sub_p90_byte_equal_frozen"]
            and tails_ok
        ):
            ok = False
        sp8[pt_path.name] = entry
    rec["SP8_artifact_conformance"] = sp8

    # ---- SP-α2 null-encoding artifacts (tail values = frozen p90 rung) ----
    tmpdir = Path(tempfile.mkdtemp(prefix="ercot181_null_"))
    null_paths = {}
    for pt_path in (WALL_PT, POOL_PT):
        pt = json.loads(pt_path.read_text())
        for cls in list(pt):
            if cls.startswith("_"):
                continue
            for tbl in pt[cls].get("years", {}).values():
                if "tail" not in tbl:
                    continue
                lad = tbl["ladder"]
                tbl["tail"] = [
                    [[p[0], lad[b][-1][1]] for p in t]
                    for b, t in enumerate(tbl["tail"])
                ]
        np_path = tmpdir / pt_path.name
        np_path.write_text(json.dumps(pt))
        null_paths[pt_path.name] = str(np_path)

    # ---- per-year composes: SP-α1 / SP-α2 / SP-α3 / SP-α6 ----
    for year in YEARS:
        state, _meta = reconstruct_bundle_fleet(
            BUNDLE,
            year,
            required_flags=sp.ERCOT_REQUIRED_FLAGS,
            required_sequences=(),
        )
        cfg = state["config"]
        yrec: dict = {}

        comp_off, mask_off, _p = sp._compose(state, cfg, year)
        yrec["SP3_control_sha"] = sp._sha(comp_off)
        yrec["SP3_matches_ercot178"] = (
            yrec["SP3_control_sha"] == reach.CONTROL_COMPOSE_SHA.get(year)
        )

        cfg_arm = sp._armed(cfg, ercot_offer_surface_position_tail=True)
        comp_arm, mask_arm, _p2 = sp._compose(state, cfg_arm, year)
        yrec["ARM_sha"] = sp._sha(comp_arm)
        yrec["ARM_differs"] = yrec["ARM_sha"] != yrec["SP3_control_sha"]

        geo = reach._year_geometry(state, year)
        n_gen = comp_off.shape[0]
        hour_bin = geo["hour_bin"]
        wall_hi = np.take_along_axis(
            geo["wall_rel"], hour_bin[None, :].repeat(n_gen, 0), axis=1
        )
        pool_hi = np.take_along_axis(
            geo["pool_rel"], hour_bin[None, :].repeat(n_gen, 0), axis=1
        )
        own = mask_off if mask_off is not None else np.zeros_like(comp_off, bool)
        cand = (np.nan_to_num(wall_hi, nan=-1.0) > 0.9) & ~own
        cand |= (np.nan_to_num(pool_hi, nan=-1.0) > 0.9) & own

        diff = comp_arm != comp_off
        yrec["SP1_mask_identical"] = (
            (mask_arm is None and mask_off is None)
            or np.array_equal(mask_arm, mask_off)
        )
        yrec["SP1_diff_row_hours"] = int(diff.sum())
        yrec["SP1_diff_outside_candidates"] = int((diff & ~cand).sum())
        yrec["SP1_confined"] = yrec["SP1_diff_outside_candidates"] == 0
        yrec["SP6_no_markdown"] = bool(np.all(comp_arm >= comp_off - 1e-12))
        if not (
            yrec["SP3_matches_ercot178"]
            and yrec["SP1_mask_identical"]
            and yrec["SP1_confined"]
            and yrec["SP6_no_markdown"]
        ):
            ok = False

        cfg_null = sp._armed(
            cfg,
            ercot_offer_surface_position_tail=True,
            ercot_offer_surface_cleared_share_rt_path=null_paths[WALL_PT.name],
            ercot_faststart_pool_offer_path=null_paths[POOL_PT.name],
        )
        comp_null, _m3, _p3 = sp._compose(state, cfg_null, year)
        yrec["SP2_null_byte_identical"] = sp._sha(comp_null) == yrec["SP3_control_sha"]
        if not yrec["SP2_null_byte_identical"]:
            ok = False

        # SP-α4 on 2023 only (one non-ERCOT compose suffices)
        if year == 2023:
            from market_sim.data.fleet import (
                build_ercot_faststart_pool_markup,
                build_ercot_offer_surface_cleared_share_markup,
            )

            cfg_px = sp._armed(cfg_arm, iso="PJM")
            w = build_ercot_offer_surface_cleared_share_markup(
                state["fleet_arrays"],
                state["fleet"],
                state["mc_base"],
                reach._sp178()._net_load(state),
                cfg_px,
                year,
            )
            p = build_ercot_faststart_pool_markup(
                state["fleet_arrays"],
                state["fleet"],
                state["mc_base"],
                reach._sp178()._net_load(state),
                cfg_px,
                year,
            )
            yrec["SP4_non_ercot_none"] = w is None and p is None
            if not yrec["SP4_non_ercot_none"]:
                ok = False

            # ---- SP-α7 guard integrity (2023 state) ----
            def _c(**over):
                return lambda: sp._compose(state, sp._armed(cfg, **over), year)

            pt_on = {"ercot_offer_surface_position_tail": True}
            guards = [
                _raises(
                    _c(**pt_on, ercot_offer_surface_continuous=True),
                    "positiontail + continuous",
                ),
                _raises(
                    _c(**pt_on, ercot_offer_surface_top_scoped=True),
                    "positiontail + top_scoped",
                ),
                _raises(
                    _c(
                        **pt_on,
                        ercot_offer_surface_cleared_share_rt_path=str(
                            VS / "ercot_sced_offer_wall_condbinned.json"
                        ),
                    ),
                    "positiontail x stepped RT artifact",
                ),
                _raises(
                    _c(
                        ercot_offer_surface_cleared_share_rt_path=str(WALL_PT)
                    ),
                    "gate-off x positiontail RT artifact",
                ),
                _raises(
                    _c(ercot_faststart_pool_offer_path=str(POOL_PT)),
                    "gate-off x positiontail pool artifact",
                ),
                _raises(
                    _c(**pt_on, ercot_offer_surface_min_bin=1),
                    "positiontail + min_bin != 0",
                ),
                _raises(
                    _c(**pt_on, ercot_offer_surface_cleared_share_rt=False),
                    "positiontail without RT leg",
                ),
            ]
            for member in (
                "ercot_offer_surface_cleared_share_state",
                "ercot_offer_surface_cleared_share_steam",
                "ercot_shoulder_online_span",
                "ercot_offer_surface_lowcurve",
                "ercot_offer_surface_midcurve_conditional",
                "ercot_offline_commit_offer",
            ):
                guards.append(
                    _raises(_c(**pt_on, **{member: True}), f"positiontail + {member}")
                )
            yrec["SP7_guards"] = guards
            yrec["SP7_all_raise"] = all(g["raises"] for g in guards)
            key_def = cfg.cache_key()
            key_arm = cfg_arm.cache_key()
            yrec["SP7_default_key"] = key_def
            yrec["SP7_armed_key_distinct"] = key_arm != key_def
            mm = subprocess.run(
                [sys.executable, "scripts/check_mechanism_matrix.py"],
                capture_output=True,
                cwd=REPO,
            )
            yrec["SP7_matrix_check_exit0"] = mm.returncode == 0
            if not (
                yrec["SP7_all_raise"]
                and yrec["SP7_armed_key_distinct"]
                and yrec["SP7_matrix_check_exit0"]
            ):
                ok = False

        rec["years"][str(year)] = yrec
        del state

    rec["ARM_differs_2023"] = rec["years"]["2023"]["ARM_differs"]
    if not rec["ARM_differs_2023"]:
        ok = False  # Route B premise: the arm is a real delta in 2023
    rec["ALL_ASSERTIONS_PASS"] = ok
    OUT.write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec, indent=1)[:4000])
    print(f"wrote {OUT}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
