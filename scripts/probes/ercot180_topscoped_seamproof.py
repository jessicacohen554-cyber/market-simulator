"""Seam proof for the ercot-180 TOP-SCOPED conditioning grain (form b).

**NEVER RUN IN ercot-180 — the session ended at §2 EXHAUSTED-AT-IDENTIFICATION**
(zero accepted edges: best candidate rank 0.9949, day-block permutation
p = 0.017 vs the pre-registered p < 0.01 bar —
``results/calibration/ercot180_edge_identification.json``), so no topscoped
artifact was ever derived and there was nothing to prove. Kept committed as
the complete, ready seam-proof for any FUTURE evidence-driven
re-identification (e.g. a full-year 2024/2025 NP3-965 intake changing the
identification corpus); running it requires the four ``*_topscoped.json``
artifacts to exist.

Executes, on the REAL keeper solve inputs for every scored year, the
assertions pre-registered in ``docs/PRECOMMIT-ercot180-top-scoped-grain-
2026-08-08.md`` §5:

* SP-1   — non-ERCOT ISOs: every builder returns None under the gate.
* SP-2   — gate OFF composes byte-identically to the control path.
* SP-3'  — THE FORM-(b) CORE PROOF: gate ON with the REAL topscoped
           artifacts, every solve hour whose within-year net-load rank is
           <= 0.97 carries composed ``mc_bid_adjust`` rows AND pool
           ``own_mask`` BYTE-IDENTICAL to the gate-off control (all years);
           and the arm differs somewhere above 0.97 in 2023 (else the arm is
           provably inert and is NOT solved — the ercot-176 Amendment-3
           precedent).
* SP-3'' — NULL ENCODING: topscoped tables carrying the new edges but the
           frozen parent top-bin value in EVERY sub-bin compose
           byte-identical to control EVERYWHERE — the added edges are GRAIN,
           never level.
* SP-4a  — exclusivity: every row-hour has exactly one owner.
* SP-4b  — owner-flip share vs control: disclosed; a flip on a sub-p97
           row-hour is an SP-3' failure (asserted).
* SP-5   — mechanism-internal no-markdown: every markup array >= 0.
* SP-6   — the four frozen STEPPED artifacts byte-identical to HEAD.
* SP-6'  — the four frozen form-(a) ``_contpct.json`` artifacts
           byte-identical to HEAD (the `R` record survives the new derives).
* SP-7   — every §3 forbidden combination raises loudly (min_bin != 0, each
           unmigrated member) under the NEW gate.
* SP-7'  — cross-gate exclusions raise: BOTH grain gates armed; the new gate
           against a stepped artifact and against a contpct artifact; the
           form-(a) gate against a topscoped artifact.
* SP-8   — artifact conformance: provenance edges == frozen legacy edges +
           the committed edge-identification record's accepted edges (count
           <= MAX_EDGES = 2); the sub-p97 node prefix byte-equals the pure
           step-encoding of the frozen stepped values; vintage tag correct.

Run BEFORE any solve. No LP is built.

Usage::

    python scripts/probes/ercot180_topscoped_seamproof.py
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
OUT = REPO / "results/calibration/ercot180_topscoped_seamproof.json"
VS = REPO / "data/raw/_validation-source"

STEPPED_ARTIFACTS = (
    "offer_curve_dam_hrmults_condbinned.json",
    "ercot_dam_cleared_share_condbinned.json",
    "ercot_sced_offer_wall_condbinned.json",
    "ercot_faststart_pool_condbinned.json",
)
CONTPCT_ARTIFACTS = (
    "offer_curve_dam_hrmults_contpct.json",
    "ercot_dam_cleared_share_contpct.json",
    "ercot_sced_offer_wall_contpct.json",
    "ercot_faststart_pool_contpct.json",
)
TOPSCOPED_ARTIFACTS = (
    "offer_curve_dam_hrmults_topscoped.json",
    "ercot_dam_cleared_share_topscoped.json",
    "ercot_sced_offer_wall_topscoped.json",
    "ercot_faststart_pool_topscoped.json",
)

ERCOT_REQUIRED_FLAGS = (
    "ercot_offer_surface_conditional",
    "ercot_offer_surface_cleared_share",
    "ercot_offer_surface_cleared_share_rt",
    "ercot_faststart_pool_offer",
)

P97 = 0.97
MAX_EDGES = 2


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


def _null_encode_tables(tmpdir: Path) -> dict:
    """SP-3'' tables: new edges present, EVERY sub-bin inheriting the parent.

    Built from the FROZEN stepped artifacts via the same shared encoder the
    derives use, with ``top_sub_rows`` all None — the pure grain-not-level
    null: identical values everywhere, only the edge geometry added.
    """
    from scripts.lib.topscoped_encode import (
        TOPSCOPED_TAG,
        encode_step_nodes,
        load_identified_edges,
        rows_from_pairs,
        split_top_bin,
    )

    new_edges = load_identified_edges()

    # conditional (pooled)
    cond = json.loads((VS / STEPPED_ARTIFACTS[0]).read_text())
    edges_c = [float(x) for x in cond["_provenance"]["netload_pct_edges"]]
    enc_cond: dict = {"_provenance": {"conditioning": TOPSCOPED_TAG}}
    for cls, entry in cond.items():
        if cls.startswith("_") or not entry.get("binned_ladder"):
            continue
        rows = rows_from_pairs(entry["binned_ladder"])
        if len(rows) != len(edges_c) + 1:
            continue
        e_all, r_all = split_top_bin(
            edges_c, rows, new_edges, [None] * (len(new_edges) + 1)
        )
        xs, ys = encode_step_nodes(e_all, r_all)
        enc_cond[cls] = {
            "base_hr": entry.get("base_hr"),
            "peak_p50": entry.get("peak_p50"),
            "cont": {
                "pct": xs,
                "mult": ys,
                "n_rungs": len(ys[0]),
                "n_nodes": len(xs),
            },
        }
    p_cond = tmpdir / "null_cond.json"
    p_cond.write_text(json.dumps(enc_cond))

    def _wall_like(src_name: str, out_name: str, with_share: bool, frac: bool) -> Path:
        src = json.loads((VS / src_name).read_text())
        edges_w = [float(x) for x in src["_provenance"]["netload_pct_edges"]]
        lq = [float(q) for q in src["_provenance"]["ladder_quantiles"]]
        enc: dict = {
            "_provenance": {"conditioning": TOPSCOPED_TAG, "ladder_quantiles": lq}
        }
        for cls, entry in src.items():
            if cls.startswith("_"):
                continue
            years_out: dict = {}
            for y, tbl in (entry.get("years") or {}).items():
                if int(y) not in YEARS:
                    continue  # training years only, as the real derive
                out_tbl: dict = {}
                rows = rows_from_pairs(tbl["ladder"])
                if not all(all(np.isfinite(v) for v in r) for r in rows):
                    continue
                e_all, r_all = split_top_bin(
                    edges_w, rows, new_edges, [None] * (len(new_edges) + 1)
                )
                xs, ys = encode_step_nodes(e_all, r_all)
                out_tbl["pct"], out_tbl["ladder"] = xs, ys
                if with_share:
                    sh = [[float(s)] for s in tbl["cleared_share"]]
                    e_s, r_s = split_top_bin(
                        edges_w, sh, new_edges, [None] * (len(new_edges) + 1)
                    )
                    xs_s, ys_s = encode_step_nodes(e_s, r_s)
                    out_tbl["share_pct"] = xs_s
                    out_tbl["share"] = [r[0] for r in ys_s]
                if frac:
                    fr = [[float(s)] for s in tbl["pool_frac"]]
                    e_f, r_f = split_top_bin(
                        edges_w, fr, new_edges, [None] * (len(new_edges) + 1)
                    )
                    xs_f, ys_f = encode_step_nodes(e_f, r_f)
                    out_tbl["frac_pct"] = xs_f
                    out_tbl["pool_frac"] = [r[0] for r in ys_f]
                years_out[y] = out_tbl
            if years_out:
                enc[cls] = {"years": years_out}
                if with_share and entry.get("pooled"):
                    tblp = entry["pooled"]
                    rows = rows_from_pairs(tblp["ladder"])
                    if all(all(np.isfinite(v) for v in r) for r in rows):
                        e_all, r_all = split_top_bin(
                            edges_w, rows, new_edges, [None] * (len(new_edges) + 1)
                        )
                        xs, ys = encode_step_nodes(e_all, r_all)
                        sh = [[float(s)] for s in tblp["cleared_share"]]
                        e_s, r_s = split_top_bin(
                            edges_w, sh, new_edges, [None] * (len(new_edges) + 1)
                        )
                        xs_s, ys_s = encode_step_nodes(e_s, r_s)
                        enc[cls]["pooled"] = {
                            "pct": xs,
                            "ladder": ys,
                            "share_pct": xs_s,
                            "share": [r[0] for r in ys_s],
                        }
        p = tmpdir / out_name
        p.write_text(json.dumps(enc))
        return p

    p_wall = _wall_like(STEPPED_ARTIFACTS[1], "null_wall.json", True, False)
    p_rt = _wall_like(STEPPED_ARTIFACTS[2], "null_rt.json", False, False)
    p_pool = _wall_like(STEPPED_ARTIFACTS[3], "null_pool.json", False, True)

    return {
        "ercot_offer_surface_binned_path": str(p_cond),
        "ercot_offer_surface_cleared_share_path": str(p_wall),
        "ercot_offer_surface_cleared_share_rt_path": str(p_rt),
        "ercot_faststart_pool_offer_path": str(p_pool),
    }


def run_year(year: int, tmpdir: Path) -> dict:
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, _meta = reconstruct_bundle_fleet(
        BUNDLE, year, required_flags=ERCOT_REQUIRED_FLAGS, required_sequences=()
    )
    cfg_off = state["config"]
    rec: dict = {"year": year, "n_gen": int(state["mc_base"].shape[0])}
    nl = _net_load(state)
    p_t = _rank_pct(nl)
    sub97 = p_t <= P97
    rec["n_hours_sub97"] = int(sub97.sum())

    # Control composition (gate off — the keeper's own path).
    composed_off, mask_off, parts_off = _compose(state, cfg_off, year)
    rec["SP2_control_composed_sha"] = _sha(composed_off)
    rec["SP2_gate_default_off"] = not bool(
        getattr(cfg_off, "ercot_offer_surface_top_scoped", False)
    )

    # ARM composition (real topscoped artifacts at their default paths).
    cfg_arm = _armed(cfg_off, ercot_offer_surface_top_scoped=True)
    composed_arm, mask_arm, parts_arm = _compose(state, cfg_arm, year)
    rec["ARM_composed_sha"] = _sha(composed_arm)

    # SP-3' — sub-p97 byte-identity of composed rows AND own_mask; and the
    # arm must differ somewhere above p97 (2023 asserts; other years record).
    both = composed_arm is not None and composed_off is not None
    if both:
        eq_sub = bool(
            np.array_equal(composed_arm[:, sub97], composed_off[:, sub97])
        )
    else:
        eq_sub = composed_arm is None and composed_off is None
    if mask_arm is not None and mask_off is not None:
        eq_mask_sub = bool(np.array_equal(mask_arm[:, sub97], mask_off[:, sub97]))
    else:
        eq_mask_sub = (mask_arm is None) == (mask_off is None)
    rec["SP3p_sub97_byte_identical"] = eq_sub and eq_mask_sub
    if both:
        rec["ARM_differs_above_p97"] = bool(
            not np.array_equal(composed_arm[:, ~sub97], composed_off[:, ~sub97])
            or (
                mask_arm is not None
                and mask_off is not None
                and not np.array_equal(mask_arm[:, ~sub97], mask_off[:, ~sub97])
            )
        )
    else:
        rec["ARM_differs_above_p97"] = False

    # SP-3'' — null encoding composes byte-identical to control EVERYWHERE.
    null_paths = _null_encode_tables(tmpdir)
    cfg_null = _armed(cfg_off, ercot_offer_surface_top_scoped=True, **null_paths)
    composed_null, mask_null, _parts_null = _compose(state, cfg_null, year)
    rec["SP3n_null_composed_sha"] = _sha(composed_null)
    rec["SP3n_byte_identical"] = rec["SP3n_null_composed_sha"] == _sha(composed_off)

    # SP-4a — exclusivity.
    ok_a = True
    if composed_arm is not None:
        base = np.zeros_like(composed_arm)
        if parts_arm["cond"] is not None:
            base += parts_arm["cond"]
        if parts_arm["wall"] is not None:
            base += parts_arm["wall"]
        if mask_arm is not None:
            ok_a = bool(
                np.array_equal(composed_arm[mask_arm], parts_arm["pool"][mask_arm])
                and np.array_equal(composed_arm[~mask_arm], base[~mask_arm])
            )
        else:
            ok_a = bool(np.array_equal(composed_arm, base))
    rec["SP4a_exclusivity"] = ok_a

    # SP-4b — owner-flip share (disclosed); sub-p97 flips asserted zero.
    if mask_arm is not None and mask_off is not None:
        rec["SP4b_owner_flip_share"] = float(np.mean(mask_arm != mask_off))
        rec["SP4b_owner_flip_share_sub97"] = float(
            np.mean(mask_arm[:, sub97] != mask_off[:, sub97])
        )
    else:
        rec["SP4b_owner_flip_share"] = None
        rec["SP4b_owner_flip_share_sub97"] = 0.0
    rec["SP4b_sub97_no_flip"] = rec["SP4b_owner_flip_share_sub97"] == 0.0

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

    # SP-7 / SP-7' — forbidden combinations raise loudly (checked once).
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
        # SP-7': cross-gate exclusions.
        try:
            bad = _armed(cfg_arm, ercot_offer_surface_continuous=True)
            build_ercot_offer_surface_cleared_share_markup(
                fa, fleet, mc_base, nl, bad, year
            )
            forbidden["both_grain_gates"] = "NO ERROR — FAIL"
        except (ValueError, FileNotFoundError) as e:
            forbidden["both_grain_gates"] = f"raised: {type(e).__name__}"
        try:
            bad = _armed(
                cfg_arm,
                ercot_offer_surface_cleared_share_path=str(
                    VS / STEPPED_ARTIFACTS[1]
                ),
            )
            build_ercot_offer_surface_cleared_share_markup(
                fa, fleet, mc_base, nl, bad, year
            )
            forbidden["topscoped_gate_x_stepped_artifact"] = "NO ERROR — FAIL"
        except (ValueError, FileNotFoundError) as e:
            forbidden["topscoped_gate_x_stepped_artifact"] = (
                f"raised: {type(e).__name__}"
            )
        try:
            bad = _armed(
                cfg_arm,
                ercot_offer_surface_cleared_share_path=str(
                    VS / CONTPCT_ARTIFACTS[1]
                ),
            )
            build_ercot_offer_surface_cleared_share_markup(
                fa, fleet, mc_base, nl, bad, year
            )
            forbidden["topscoped_gate_x_contpct_artifact"] = "NO ERROR — FAIL"
        except (ValueError, FileNotFoundError) as e:
            forbidden["topscoped_gate_x_contpct_artifact"] = (
                f"raised: {type(e).__name__}"
            )
        try:
            bad = _armed(
                cfg_off,
                ercot_offer_surface_continuous=True,
                ercot_offer_surface_cleared_share_path=str(
                    VS / TOPSCOPED_ARTIFACTS[1]
                ),
            )
            build_ercot_offer_surface_cleared_share_markup(
                fa, fleet, mc_base, nl, bad, year
            )
            forbidden["contpct_gate_x_topscoped_artifact"] = "NO ERROR — FAIL"
        except (ValueError, FileNotFoundError) as e:
            forbidden["contpct_gate_x_topscoped_artifact"] = (
                f"raised: {type(e).__name__}"
            )
        rec["SP7_forbidden_combos"] = forbidden
        rec["SP7_all_raise"] = all(v.startswith("raised") for v in forbidden.values())
    return rec


def _sp8_artifact_conformance() -> dict:
    """SP-8: edges match the committed record; sub-p97 prefix byte-equal."""
    from scripts.lib.topscoped_encode import (
        TOPSCOPED_TAG,
        encode_step_nodes,
        load_identified_edges,
        rows_from_pairs,
    )

    new_edges = load_identified_edges()
    rec: dict = {
        "accepted_edges": new_edges,
        "n_edges_ok": len(new_edges) <= MAX_EDGES,
    }

    def _prefix_ok(xs, ys, legacy_edges, legacy_rows) -> bool:
        """Topscoped nodes at x <= p97 == pure legacy step-encoding prefix."""
        exs, eys = encode_step_nodes(legacy_edges, legacy_rows)
        keep_e = [i for i, x in enumerate(exs) if x <= P97]
        keep_t = [i for i, x in enumerate(xs) if x <= P97]
        return [exs[i] for i in keep_e] == [xs[i] for i in keep_t] and [
            eys[i] for i in keep_e
        ] == [ys[i] for i in keep_t]

    checks: dict[str, bool] = {}
    # conditional
    fro = json.loads((VS / STEPPED_ARTIFACTS[0]).read_text())
    top = json.loads((VS / TOPSCOPED_ARTIFACTS[0]).read_text())
    checks["cond_tag"] = top["_provenance"]["conditioning"] == TOPSCOPED_TAG
    ec = [float(x) for x in fro["_provenance"]["netload_pct_edges"]]
    checks["cond_edges"] = [
        float(x) for x in top["_provenance"]["netload_pct_edges"]
    ] == ec + new_edges
    for cls, entry in top.items():
        if cls.startswith("_"):
            continue
        rows = rows_from_pairs(fro[cls]["binned_ladder"])
        checks[f"cond_{cls}_prefix"] = _prefix_ok(
            entry["cont"]["pct"], entry["cont"]["mult"], ec, rows
        )
    # wall / rt / pool
    for name_f, name_t, key in (
        (STEPPED_ARTIFACTS[1], TOPSCOPED_ARTIFACTS[1], "wall"),
        (STEPPED_ARTIFACTS[2], TOPSCOPED_ARTIFACTS[2], "rt"),
        (STEPPED_ARTIFACTS[3], TOPSCOPED_ARTIFACTS[3], "pool"),
    ):
        fro = json.loads((VS / name_f).read_text())
        top = json.loads((VS / name_t).read_text())
        checks[f"{key}_tag"] = top["_provenance"]["conditioning"] == TOPSCOPED_TAG
        ew = [float(x) for x in fro["_provenance"]["netload_pct_edges"]]
        checks[f"{key}_edges"] = [
            float(x) for x in top["_provenance"]["netload_pct_edges"]
        ] == ew + new_edges
        for cls, entry in top.items():
            if cls.startswith("_") or not isinstance(entry, dict):
                continue
            for y, tbl in (entry.get("years") or {}).items():
                fro_tbl = fro[cls]["years"][y]
                rows = rows_from_pairs(fro_tbl["ladder"])
                checks[f"{key}_{cls}_{y}_ladder_prefix"] = _prefix_ok(
                    tbl["pct"], tbl["ladder"], ew, rows
                )
    rec["checks"] = checks
    rec["all_ok"] = all(checks.values()) and rec["n_edges_ok"]
    return rec


def main() -> None:
    out: dict = {
        "precommit": "docs/PRECOMMIT-ercot180-top-scoped-grain-2026-08-08.md",
        "bundle": str(BUNDLE.relative_to(REPO)),
    }

    # SP-6 / SP-6' — frozen artifacts byte-identical to HEAD.
    for label, names in (
        ("SP6_stepped_artifacts", STEPPED_ARTIFACTS),
        ("SP6p_contpct_artifacts", CONTPCT_ARTIFACTS),
    ):
        block = {}
        for name in names:
            disk = hashlib.sha256((VS / name).read_bytes()).hexdigest()
            blob = subprocess.run(
                ["git", "show", f"HEAD:data/raw/_validation-source/{name}"],
                capture_output=True,
                cwd=REPO,
            )
            head = hashlib.sha256(blob.stdout).hexdigest()
            block[name] = {"disk": disk, "head": head, "identical": disk == head}
        out[label] = block
        out[label + "_all_identical"] = all(v["identical"] for v in block.values())

    # SP-8 — artifact conformance (pure JSON, no solve inputs needed).
    out["SP8"] = _sp8_artifact_conformance()

    tmpdir = OUT.parent / "_ercot180_null_tmp"
    tmpdir.mkdir(exist_ok=True)
    try:
        out["years"] = [run_year(y, tmpdir) for y in YEARS]
    finally:
        for p in tmpdir.glob("null_*.json"):
            p.unlink(missing_ok=True)
        tmpdir.rmdir()

    # check_mechanism_matrix exit 0 (SP-7 registry half).
    cm = subprocess.run(
        [sys.executable, "scripts/check_mechanism_matrix.py"],
        capture_output=True,
        cwd=REPO,
    )
    out["SP7_check_mechanism_matrix_exit0"] = cm.returncode == 0

    checks = [
        out["SP6_stepped_artifacts_all_identical"],
        out["SP6p_contpct_artifacts_all_identical"],
        out["SP8"]["all_ok"],
        out["SP7_check_mechanism_matrix_exit0"],
    ]
    for rec in out["years"]:
        checks += [
            rec["SP2_gate_default_off"],
            rec["SP3p_sub97_byte_identical"],
            rec["SP3n_byte_identical"],
            rec["SP4a_exclusivity"],
            rec["SP4b_sub97_no_flip"],
            rec["SP5_no_markdown"],
            rec["SP1_non_ercot_all_none"],
        ]
        if "SP7_all_raise" in rec:
            checks.append(rec["SP7_all_raise"])
    # The 2023 above-p97 difference is the inertness signal, asserted
    # separately: an all-years-identical arm is NOT an assertion failure but
    # the ercot-176 Amendment-3 inert outcome (recorded for the finding).
    out["ARM_inert_all_years"] = not any(
        r.get("ARM_differs_above_p97") for r in out["years"]
    )
    out["ALL_ASSERTIONS_PASS"] = bool(all(checks))

    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {OUT}")
    if not out["ALL_ASSERTIONS_PASS"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
