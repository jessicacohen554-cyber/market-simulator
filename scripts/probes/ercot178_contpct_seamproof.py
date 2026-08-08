"""Seam proof for the ERCOT-178 continuous net-load-percentile grain.

Executes, on the REAL keeper solve inputs for every scored year, the
assertions pre-registered in ``docs/PRECOMMIT-ercot178-continuous-netload-
grain-2026-08-08.md`` §5 (SP-4 as restated by its Amendment 1):

* SP-1  — non-ERCOT ISOs: every builder returns None under the gate.
* SP-2  — gate OFF composes byte-identically to the control path (sha
          recorded per year; the stepped code lines are untouched by the
          implementation, and the control solve replays run176 at this HEAD).
* SP-3  — THE CRITICAL PROOF: with the gate ON but each continuous artifact
          replaced by a STEP-ENCODED node table (nodes at the solve year's own
          hour ranks, each carrying the FROZEN stepped artifact's value for
          that hour's legacy bin), the composed ``mc_bid_adjust`` is
          BYTE-IDENTICAL (sha256) to the gate-OFF control — the machinery
          reproduces the step exactly when fed the step, so the arm's delta is
          GRAIN, never level.
* SP-4a — exclusivity: on pool-owned row-hours the composed adjust equals the
          pool markup alone; elsewhere the conditional + wall sum alone.
* SP-4b — boundary movement vs control own_mask: DISCLOSED, not gated.
* SP-5  — mechanism-internal no-markdown: every markup array >= 0.
* SP-6  — the four frozen stepped artifacts are byte-identical to their HEAD
          blobs after the --continuous derives ran.
* SP-7  — every §2 forbidden combination raises loudly.

Run BEFORE any solve. No LP is built.

Usage::

    python scripts/probes/ercot178_contpct_seamproof.py
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

BUNDLE = REPO / "results/calibration/ercot176_control_A"
YEARS = (2023, 2024, 2025)
OUT = REPO / "results/calibration/ercot178_contpct_seamproof.json"
VS = REPO / "data/raw/_validation-source"

STEPPED_ARTIFACTS = (
    "offer_curve_dam_hrmults_condbinned.json",
    "ercot_dam_cleared_share_condbinned.json",
    "ercot_sced_offer_wall_condbinned.json",
    "ercot_faststart_pool_condbinned.json",
)

ERCOT_REQUIRED_FLAGS = (
    "ercot_offer_surface_conditional",
    "ercot_offer_surface_cleared_share",
    "ercot_offer_surface_cleared_share_rt",
    "ercot_faststart_pool_offer",
)


def _sha(a: "np.ndarray | None") -> str:
    if a is None:
        return "None"
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def _armed(config, **over):
    if hasattr(config, "model_copy"):
        return config.model_copy(update=over)
    return dataclasses.replace(config, **over)


def _net_load(state: dict) -> np.ndarray:
    demand = state["demand"]
    return (
        demand.sum(axis=0)
        - (state["solar_cap"][:, None] * state["solar_cf"]).sum(axis=0)
        - (state["wind_cap"][:, None] * state["wind_cf"]).sum(axis=0)
    )


def _compose(state, cfg, year) -> "tuple[np.ndarray | None, np.ndarray | None, dict]":
    """Mirror run_calibration.py's composition: cond + wall, pool by mask."""
    from market_sim.data.fleet import (
        build_ercot_faststart_pool_markup,
        build_ercot_offer_surface_cleared_share_markup,
    )
    from market_sim.data.fleet.offer_surfaces import (
        build_offer_surface_conditional_markup,
    )

    fa, fleet, mc_base = state["fleet_arrays"], state["fleet"], state["mc_base"]
    fuel = state["fuel_prices"]
    nl = _net_load(state)
    cond = build_offer_surface_conditional_markup("ERCOT", fa, fleet, fuel, nl, cfg)
    wall = build_ercot_offer_surface_cleared_share_markup(
        fa, fleet, mc_base, nl, cfg, year
    )
    composed = None
    if cond is not None:
        composed = cond.copy()
    if wall is not None:
        composed = wall.copy() if composed is None else composed + wall
    pool = build_ercot_faststart_pool_markup(fa, fleet, mc_base, nl, cfg, year)
    own_mask = None
    if pool is not None:
        pmk, own_mask = pool
        if composed is None:
            composed = pmk
        else:
            composed = np.where(own_mask, pmk, composed)
    parts = {
        "cond": cond,
        "wall": wall,
        "pool": None if pool is None else pool[0],
        "own_mask": own_mask,
    }
    return composed, own_mask, parts


def _rank_pct(net_load: np.ndarray) -> np.ndarray:
    return pd.Series(np.asarray(net_load, dtype=float)).rank(pct=True).to_numpy()


def _dedupe(xs: np.ndarray, rows: np.ndarray) -> tuple[list, list]:
    """Sort by x and drop duplicate x (tied hours carry identical rows)."""
    order = np.argsort(xs, kind="stable")
    seen: dict[float, int] = {}
    keep: list[int] = []
    for i in order:
        x = float(xs[i])
        if x in seen:
            continue
        seen[x] = i
        keep.append(i)
    return [float(xs[i]) for i in keep], [rows[i].tolist() for i in keep]


def _encode_step_tables(state: dict, year: int, tmpdir: Path) -> dict:
    """Build step-ENCODED continuous artifacts from the FROZEN stepped ones.

    Nodes are placed at the solve year's own hour ranks; each node carries the
    stepped artifact's value for that hour's legacy bin, so interpolation hits
    every node exactly and the continuous machinery must reproduce the control
    byte-for-byte (SP-3). Returns the four override paths + coverage notes.
    """
    nl = _net_load(state)
    p_t = _rank_pct(nl)
    notes: dict = {}

    # --- conditional peak surface (config edges, 4 bins) -------------------
    cond = json.loads((VS / STEPPED_ARTIFACTS[0]).read_text())
    cfg = state["config"]
    edges_c = tuple(float(x) for x in cfg.ercot_offer_surface_netload_pcts)
    thr_c = np.quantile(nl, edges_c)
    bin_c = np.searchsorted(thr_c, nl, side="right")
    enc_cond: dict = {"_provenance": {"conditioning": "continuous-netload-pct"}}
    for cls, entry in cond.items():
        if cls.startswith("_"):
            continue
        lads = entry.get("binned_ladder") or []
        if len(lads) != len(edges_c) + 1 or any(len(l) != 5 for l in lads):
            notes[f"cond_{cls}_bins_incomplete"] = True
            continue
        vals = np.array([[pt[1] for pt in lad] for lad in lads])  # (4, 5)
        rows = vals[bin_c]  # (T, 5)
        xs, mult = _dedupe(p_t, rows)
        enc_cond[cls] = {
            "base_hr": entry.get("base_hr"),
            "peak_p50": entry.get("peak_p50"),
            "cont": {"pct": xs, "mult": mult, "n_rungs": 5, "n_nodes": len(xs)},
        }
    p_cond = tmpdir / f"enc_cond_{year}.json"
    p_cond.write_text(json.dumps(enc_cond))

    # --- cleared-share wall (artifact edges, 7 bins) -----------------------
    wall = json.loads((VS / STEPPED_ARTIFACTS[1]).read_text())
    prov = wall["_provenance"]
    edges_w = tuple(float(x) for x in prov["netload_pct_edges"])
    lq = [float(q) for q in prov["ladder_quantiles"]]
    thr_w = np.quantile(nl, edges_w)
    bin_w = np.searchsorted(thr_w, nl, side="right")
    enc_wall: dict = {
        "_provenance": {
            "conditioning": "continuous-netload-pct",
            "ladder_quantiles": lq,
        }
    }
    for cls in ("CC", "CT"):
        entry = wall.get(cls)
        if not entry:
            continue
        tbl = entry.get("years", {}).get(str(year)) or entry.get("pooled")
        share = np.asarray(tbl["cleared_share"], dtype=float)
        lad = np.array([[pt[1] for pt in lad_b] for lad_b in tbl["ladder"]])
        notes[f"wall_{cls}_share_finite"] = bool(np.isfinite(share).all())
        notes[f"wall_{cls}_ladder_finite"] = bool(np.isfinite(lad).all())
        sh_ok = np.isfinite(share[bin_w])
        xs_s, sh_rows = _dedupe(p_t[sh_ok], share[bin_w][sh_ok][:, None])
        ld_ok = np.isfinite(lad[bin_w]).all(axis=1)
        xs_l, ld_rows = _dedupe(p_t[ld_ok], lad[bin_w][ld_ok])
        enc_wall[cls] = {
            "years": {
                str(year): {
                    "share_pct": xs_s,
                    "share": [r[0] for r in sh_rows],
                    "pct": xs_l,
                    "ladder": ld_rows,
                }
            }
        }
    p_wall = tmpdir / f"enc_wall_{year}.json"
    p_wall.write_text(json.dumps(enc_wall))

    # --- RT / SCED leg (same bin geometry, year-scoped) --------------------
    rt = json.loads((VS / STEPPED_ARTIFACTS[2]).read_text())
    enc_rt: dict = {
        "_provenance": {
            "conditioning": "continuous-netload-pct",
            "ladder_quantiles": lq,
        }
    }
    for cls in ("CC", "CT"):
        tbl = rt.get(cls, {}).get("years", {}).get(str(year))
        if not tbl:
            notes[f"rt_{cls}_year_absent"] = True
            continue
        lad = np.array([[pt[1] for pt in lad_b] for lad_b in tbl["ladder"]])
        notes[f"rt_{cls}_ladder_finite"] = bool(np.isfinite(lad).all())
        ld_ok = np.isfinite(lad[bin_w]).all(axis=1)
        xs_l, ld_rows = _dedupe(p_t[ld_ok], lad[bin_w][ld_ok])
        enc_rt[cls] = {"years": {str(year): {"pct": xs_l, "ladder": ld_rows}}}
    p_rt = tmpdir / f"enc_rt_{year}.json"
    p_rt.write_text(json.dumps(enc_rt))

    # --- fast-start pool (same bin geometry, year-scoped, CT) --------------
    pool = json.loads((VS / STEPPED_ARTIFACTS[3]).read_text())
    enc_pool: dict = {
        "_provenance": {
            "conditioning": "continuous-netload-pct",
            "ladder_quantiles": lq,
        }
    }
    tbl = pool.get("CT", {}).get("years", {}).get(str(year))
    if tbl:
        frac = np.asarray(tbl["pool_frac"], dtype=float)
        lad = np.array([[pt[1] for pt in lad_b] for lad_b in tbl["ladder"]])
        notes["pool_CT_frac_finite"] = bool(np.isfinite(frac).all())
        notes["pool_CT_ladder_finite"] = bool(np.isfinite(lad).all())
        fr_ok = np.isfinite(frac[bin_w])
        xs_f, fr_rows = _dedupe(p_t[fr_ok], frac[bin_w][fr_ok][:, None])
        ld_ok = np.isfinite(lad[bin_w]).all(axis=1)
        xs_l, ld_rows = _dedupe(p_t[ld_ok], lad[bin_w][ld_ok])
        enc_pool["CT"] = {
            "years": {
                str(year): {
                    "frac_pct": xs_f,
                    "pool_frac": [r[0] for r in fr_rows],
                    "pct": xs_l,
                    "ladder": ld_rows,
                }
            }
        }
    else:
        notes["pool_CT_year_absent"] = True
    p_pool = tmpdir / f"enc_pool_{year}.json"
    p_pool.write_text(json.dumps(enc_pool))

    return {
        "ercot_offer_surface_binned_path": str(p_cond),
        "ercot_offer_surface_cleared_share_path": str(p_wall),
        "ercot_offer_surface_cleared_share_rt_path": str(p_rt),
        "ercot_faststart_pool_offer_path": str(p_pool),
        "_notes": notes,
    }


def run_year(year: int, tmpdir: Path) -> dict:
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, _meta = reconstruct_bundle_fleet(
        BUNDLE, year, required_flags=ERCOT_REQUIRED_FLAGS, required_sequences=()
    )
    cfg_off = state["config"]
    rec: dict = {"year": year, "n_gen": int(state["mc_base"].shape[0])}

    # Control composition (gate off — the keeper's own path).
    composed_off, mask_off, parts_off = _compose(state, cfg_off, year)
    rec["SP2_control_composed_sha"] = _sha(composed_off)
    rec["SP2_gate_default_off"] = not bool(
        getattr(cfg_off, "ercot_offer_surface_continuous", False)
    )

    # SP-3 — legacy-encoded continuous tables reproduce the control.
    enc = _encode_step_tables(state, year, tmpdir)
    rec["SP3_encoding_notes"] = enc.pop("_notes")
    cfg_enc = _armed(cfg_off, ercot_offer_surface_continuous=True, **enc)
    composed_enc, _mask_enc, _parts_enc = _compose(state, cfg_enc, year)
    rec["SP3_encoded_composed_sha"] = _sha(composed_enc)
    rec["SP3_byte_identical"] = rec["SP3_encoded_composed_sha"] == _sha(composed_off)

    # Arm composition (real continuous artifacts at their default paths).
    cfg_arm = _armed(cfg_off, ercot_offer_surface_continuous=True)
    composed_arm, mask_arm, parts_arm = _compose(state, cfg_arm, year)
    rec["ARM_composed_sha"] = _sha(composed_arm)
    rec["ARM_differs_from_control"] = rec["ARM_composed_sha"] != _sha(composed_off)

    # SP-4a — exclusivity: pool-owned row-hours carry the pool markup alone;
    # everywhere else the conditional + wall sum alone.
    ok_a = True
    if composed_arm is not None:
        base = np.zeros_like(composed_arm)
        if parts_arm["cond"] is not None:
            base += parts_arm["cond"]
        if parts_arm["wall"] is not None:
            base += parts_arm["wall"]
        if mask_arm is not None:
            ok_a = bool(
                np.array_equal(
                    composed_arm[mask_arm], parts_arm["pool"][mask_arm]
                )
                and np.array_equal(composed_arm[~mask_arm], base[~mask_arm])
            )
        else:
            ok_a = bool(np.array_equal(composed_arm, base))
    rec["SP4a_exclusivity"] = ok_a

    # SP-4b — ownership movement vs control (disclosed, not gated).
    if mask_arm is not None and mask_off is not None:
        rec["SP4b_owner_flip_share"] = float(
            np.mean(mask_arm != mask_off)
        )
        rec["SP4b_pool_rowhours_control"] = int(mask_off.sum())
        rec["SP4b_pool_rowhours_arm"] = int(mask_arm.sum())
    else:
        rec["SP4b_owner_flip_share"] = None
        rec["SP4b_pool_rowhours_control"] = (
            0 if mask_off is None else int(mask_off.sum())
        )
        rec["SP4b_pool_rowhours_arm"] = 0 if mask_arm is None else int(mask_arm.sum())

    # SP-5 — no markdown anywhere in the mechanism's own arrays.
    rec["SP5_no_markdown"] = all(
        p is None or float(np.nanmin(p)) >= 0.0
        for p in (parts_arm["cond"], parts_arm["wall"], parts_arm["pool"])
    )

    # SP-1 — non-ERCOT: every builder returns None under the gate.
    from market_sim.data.fleet import (
        build_ercot_faststart_pool_markup,
        build_ercot_offer_surface_cleared_share_markup,
    )
    from market_sim.data.fleet.offer_surfaces import (
        build_offer_surface_conditional_markup,
    )

    cfg_pjm = _armed(cfg_arm, iso="PJM")
    fa, fleet, mc_base = state["fleet_arrays"], state["fleet"], state["mc_base"]
    nl = _net_load(state)
    rec["SP1_non_ercot_all_none"] = all(
        x is None
        for x in (
            build_ercot_offer_surface_cleared_share_markup(
                fa, fleet, mc_base, nl, cfg_pjm, year
            ),
            build_ercot_faststart_pool_markup(fa, fleet, mc_base, nl, cfg_pjm, year),
            build_offer_surface_conditional_markup(
                "ERCOT", fa, fleet, state["fuel_prices"], nl, cfg_pjm
            ),
        )
    )

    # SP-7 — forbidden combinations raise loudly (checked once, on 2023).
    if year == YEARS[0]:
        forbidden = {}
        for field in (
            "ercot_offer_surface_cleared_share_state",
            "ercot_offer_surface_cleared_share_steam",
            "ercot_shoulder_online_span",
            "ercot_offer_surface_lowcurve",
            "ercot_offer_surface_lowcurve_floorscoped",
            "ercot_offer_surface_midcurve_conditional",
            "ercot_offline_commit_offer",
        ):
            try:
                bad = _armed(cfg_arm, **{field: True})
                build_ercot_offer_surface_cleared_share_markup(
                    fa, fleet, mc_base, nl, bad, year
                )
                forbidden[field] = "NO ERROR — FAIL"
            except (ValueError, FileNotFoundError) as e:
                forbidden[field] = f"raised: {type(e).__name__}"
        try:
            bad = _armed(cfg_arm, ercot_offer_surface_min_bin=1)
            build_offer_surface_conditional_markup(
                "ERCOT", fa, fleet, state["fuel_prices"], nl, bad
            )
            forbidden["ercot_offer_surface_min_bin"] = "NO ERROR — FAIL"
        except (ValueError, FileNotFoundError) as e:
            forbidden["ercot_offer_surface_min_bin"] = f"raised: {type(e).__name__}"
        rec["SP7_forbidden_combos"] = forbidden
        rec["SP7_all_raise"] = all(
            v.startswith("raised") for v in forbidden.values()
        )
    return rec


def main() -> None:
    out: dict = {
        "precommit": "docs/PRECOMMIT-ercot178-continuous-netload-grain-2026-08-08.md",
        "bundle": str(BUNDLE.relative_to(REPO)),
    }

    # SP-6 — the frozen stepped artifacts are byte-identical to HEAD.
    sp6 = {}
    for name in STEPPED_ARTIFACTS:
        disk = hashlib.sha256((VS / name).read_bytes()).hexdigest()
        blob = subprocess.run(
            ["git", "show", f"HEAD:data/raw/_validation-source/{name}"],
            capture_output=True,
            cwd=REPO,
        )
        head = hashlib.sha256(blob.stdout).hexdigest()
        sp6[name] = {"disk": disk, "head": head, "identical": disk == head}
    out["SP6_stepped_artifacts"] = sp6
    out["SP6_all_identical"] = all(v["identical"] for v in sp6.values())

    tmpdir = OUT.parent / "_ercot178_enc_tmp"
    tmpdir.mkdir(exist_ok=True)
    try:
        out["years"] = [run_year(y, tmpdir) for y in YEARS]
    finally:
        for p in tmpdir.glob("enc_*.json"):
            p.unlink(missing_ok=True)
        tmpdir.rmdir()

    checks = [out["SP6_all_identical"]]
    for rec in out["years"]:
        checks += [
            rec["SP2_gate_default_off"],
            rec["SP3_byte_identical"],
            rec["SP4a_exclusivity"],
            rec["SP5_no_markdown"],
            rec["SP1_non_ercot_all_none"],
        ]
        if "SP7_all_raise" in rec:
            checks.append(rec["SP7_all_raise"])
    out["ALL_ASSERTIONS_PASS"] = bool(all(checks))

    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {OUT}")
    if not out["ALL_ASSERTIONS_PASS"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
