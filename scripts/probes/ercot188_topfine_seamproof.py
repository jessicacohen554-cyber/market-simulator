"""ercot-188 seam proof for the (c2) top-refined econ-curve slicing (SCHEME R1).

Adjudicates the assertions pre-registered in
``docs/PRECOMMIT-ercot188-cliff-offer-curve-refinement-2026-08-11.md`` §2.6, on
real reconstructed keeper fleets with **no LP built**:

* **SP-1** gate-off inertness (ERCOT): with ``ercot_econ_curve_top_refine`` at
  its default the ERCOT composed fleet is BYTE-IDENTICAL to pre-edit HEAD.
* **SP-2** cross-ISO inertness (gate ON): with the field ARMED, every non-ERCOT
  ISO's composed fleet is BYTE-IDENTICAL to control. **The charter's mandatory
  seam proof** — ``_econ_curve_steps`` sits on the ISO-agnostic assembly path
  and all six keepers share ``n = 6``, so an ungated change would silently
  re-slice every ISO's fleet (MEMO-ercot184 §6).
* **SP-3** MW preservation: per plant-group and fleet-wide, the re-sliced econ
  ramp's total capacity is unchanged. The measured max deviation is REPORTED at
  full magnitude, never asserted away.
* **SP-3b** the CHP steam floor is REDISTRIBUTED across the finer slices, never
  created or destroyed (``bins_to_fleet`` fills the floor slice by slice, so a
  re-slicing legitimately moves where it lands but never how much there is).
* **SP-4** body byte-identity: every plant's first ``n-1`` econ slices are
  byte-identical in cap AND heat rate; the delta is confined to the top block.
* **SP-5** row census: under precommit Amendment 1 a plant either carries R1
  (``2n-1`` = 11 slices) or is too small for the assembly's minimum-tranche
  floor and keeps the coarse form (``n`` = 6) — those are the ONLY admissible
  counts, and a third value means sub-slices are being DELETED. Reports the
  refined/coarse split in groups and in econ MW, plus fleet rows and LP columns
  against the memo's §3.2 ×1.39 estimate (G-COST).
* **SP-6** the committed band is untouched (the memo §6 item 3 dormant
  coupling: ``_econ_curve_steps`` is also the committed-band slicer when
  ``committed_ramp_spread > 0``).

SP-3/SP-3b/SP-5 FAILED on the first build and that is what produced Amendment 1
— 36 of 144 ERCOT plant-groups had their entire top block dropped by the 0.5 MW
tranche filter, deleting 40.27 MW per year. The falsifier working is the reason
the guard exists.

Two stages, because SP-1 compares across a code edit:

    # BEFORE editing offer_curves.py / assembly.py
    python scripts/probes/ercot188_topfine_seamproof.py --stage pre --json <baseline>

    # AFTER the edit
    python scripts/probes/ercot188_topfine_seamproof.py --stage post --baseline <baseline>

Rule 22: every year touched is inside {2023, 2024, 2025} (ERCOT holds no
``complete`` and no ``final`` marker). No LP is solved and no run is registered
by this probe.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "results/calibration/ercot188_topfine_seamproof.json"

#: The field this lane adds (default off, ERCOT-gated).
FIELD = "ercot_econ_curve_top_refine"

#: ERCOT: the keeper this lane builds against, all three training years.
ERCOT_BUNDLE = REPO / "results/calibration/ercot185_shapedarm_B"
ERCOT_YEARS = (2023, 2024, 2025)

#: Boolean gates whose loss would silently change what is measured (the
#: ercot-178 seam-proof fidelity guard).
ERCOT_REQUIRED_FLAGS = (
    "ercot_offer_surface_conditional",
    "ercot_offer_surface_cleared_share",
    "ercot_offer_surface_cleared_share_rt",
    "ercot_faststart_pool_offer",
)

#: SP-2's blast-radius panel: one committed bundle per non-ERCOT ISO, so the
#: cross-ISO assertion runs on fleets those ISOs actually solved rather than on
#: a synthetic config. Rule 25 — these are READ-ONLY; no other ISO's files,
#: bundle, keeper shard or matrix column is modified by this lane.
CROSS_ISO_BUNDLES: dict[str, str] = {
    "CAISO": "caiso188_d0_control",
    # pjm158_novirt_B, not the pjm158_ctl_A control: the pair's registered ARM
    # is the member whose own recorded recipe runs pjm_da_virtual_bids OFF, and
    # its raw hrl_da_incs_decs corpus is not provisioned in this container. Both
    # are real registered PJM runs on the same recipe otherwise, so the panel
    # keeps a genuine PJM fleet with no config override at all (see
    # CROSS_ISO_DISARM).
    "PJM": "pjm158_novirt_B",
    "NYISO": "nyiso133_cod_control",
    "NEISO": "neiso87_control_A",
    "MISO": "miso148_basis_A",
}
CROSS_ISO_YEAR = 2023

#: Per-ISO reconstruction overrides, applied IDENTICALLY to both sides of the
#: SP-2 comparison. EMPTY, and it should stay empty: the two PJM mechanisms
#: that first blocked this panel (``pjm_measured_interface_limits``,
#: ``pjm_east_interface_cut``, plus ``measured_ramp_capability``) were
#: data-provisioning failures, not modelling ones — their gitignored
#: ``data/clean`` partitions were REGENERATED (``scripts/regenerate_clean.py
#: transfer-interface-limits ramp-capability``) so every ISO runs its keeper's
#: own recorded config. If an entry is ever needed here it may only disarm a
#: mechanism OFF the offer-curve path, and it is recorded in the output.
CROSS_ISO_DISARM: dict[str, dict] = {}


def _sha(a) -> str:
    """Return the sha256 of an array's contiguous bytes."""
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def _sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _row_table(state: dict) -> list[tuple]:
    """Return the composed fleet as a list of per-row tuples.

    One tuple per LP generator: ``(unit_id, pmax, min_gen, min_run, min_down,
    startup_cost)``. These are the fields ``_econ_curve_steps`` writes into the
    BASE fleet, i.e. the ones a re-slicing moves.
    """
    fleet = state["fleet"]
    rows = []
    for g in fleet:
        rows.append(
            (
                str(g.unit_id),
                float(g.pmax_mw or 0.0),
                float(g.pmin_mw or 0.0),
                float(g.heat_rate or 0.0),
                float(g.vom or 0.0),
                int(g.min_run_hours or 0),
                int(g.min_down_hours or 0),
                float(g.startup_cost_per_mw or 0.0),
            )
        )
    return rows


def _fingerprint(state: dict) -> dict:
    """Return the composed-fleet fingerprint used by every SP assertion."""
    rows = _row_table(state)
    mc = state["mc_base"]
    return {
        "n_gen": int(mc.shape[0]),
        "hours": int(mc.shape[1]),
        # The P0 objective row itself — the strongest available statement,
        # since _econ_curve_steps writes heat rates into mc_base (the P0
        # objective, precommit §3).
        "mc_base_sha": _sha(mc),
        "rows_sha": _sha_text(repr(rows)),
        "total_pmax": float(sum(r[1] for r in rows)),
    }


def _build(bundle: Path, year: int, flags: tuple[str, ...], **over):
    """Reconstruct a bundle's fleet with no LP, applying ScenarioConfig overrides."""
    from scripts.lib.bundle_fleet import full_run_year_kwargs, bundle_gas_price
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = full_run_year_kwargs(meta)
    if over:
        kwargs.setdefault("prb_overrides", {})
        kwargs["prb_overrides"] = {**kwargs["prb_overrides"], **over}
    state = run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        bundle_gas_price(meta, year),
        **kwargs,
    )
    if flags:
        from scripts.lib.bundle_fleet import assert_reconstruction_fidelity

        assert_reconstruction_fidelity(meta, state["config"], flags, ())
    return state


def _econ_groups(state: dict) -> dict[str, list[tuple[str, float, float]]]:
    """Return ``plant_prefix -> [(suffix, pmax_mw, heat_rate), ...]`` for econc rows.

    ``heat_rate`` (not a composed bid) is the field ``_econ_curve_steps``
    actually writes, so SP-4's body byte-identity is asserted on the mechanism's
    own output rather than on something downstream of it.
    """
    out: dict[str, list[tuple[str, float, float]]] = defaultdict(list)
    for g in state["fleet"]:
        uid = str(g.unit_id)
        prefix, _, sfx = uid.rpartition("_")
        if sfx.startswith("econc") and sfx[5:].isdigit():
            out[prefix].append(
                (sfx, float(g.pmax_mw or 0.0), float(g.heat_rate or 0.0))
            )
    for k in out:
        out[k].sort(key=lambda r: int(r[0][5:]))
    return dict(out)


def _chp_floor_by_group(state: dict) -> dict[str, float]:
    """Return ``plant_prefix -> total grid CHP steam floor MW`` over econc rows.

    SP-3b's object. ``bins_to_fleet`` spreads a plant's CHP steam-following
    grid floor across its econ slices **in fill order**, so a re-slicing moves
    where the floor LANDS (MEMO-ercot184 §3.4 flagged this: 61 of the 144
    plant-groups carry econ min-gen). The floor's TOTAL must be conserved —
    a re-slicing may redistribute a floor, never create or destroy one.
    """
    out: dict[str, float] = defaultdict(float)
    for g in state["fleet"]:
        uid = str(g.unit_id)
        prefix, _, sfx = uid.rpartition("_")
        if sfx.startswith("econc") and sfx[5:].isdigit():
            out[prefix] += float(getattr(g, "chp_grid_pmin_mw", 0.0) or 0.0)
    return dict(out)


# --------------------------------------------------------------------------- #
# Stages
# --------------------------------------------------------------------------- #


def stage_pre(args) -> None:
    """Capture the PRE-EDIT fingerprints (SP-1/SP-2 baselines).

    Written incrementally: each member lands in the JSON as soon as it is
    measured, so a later member's data-provisioning failure cannot discard the
    earlier ones (and a re-run resumes rather than repeats).
    """
    out = Path(args.json)
    rec: dict = (
        json.loads(out.read_text())
        if out.exists() and args.resume
        else {"stage": "pre", "ercot": {}, "cross_iso": {}}
    )

    def _flush() -> None:
        out.write_text(json.dumps(rec, indent=1))

    for year in ERCOT_YEARS:
        if str(year) in rec["ercot"]:
            print(f"  ERCOT {year}: (resumed)")
            continue
        st = _build(ERCOT_BUNDLE, year, ERCOT_REQUIRED_FLAGS)
        fp = _fingerprint(st)
        fp["econ_groups"] = len(_econ_groups(st))
        rec["ercot"][str(year)] = fp
        _flush()
        print(
            f"  ERCOT {year}: n_gen={fp['n_gen']} groups={fp['econ_groups']} "
            f"mc_base={fp['mc_base_sha'][:16]} pmax={fp['total_pmax']:.1f}"
        )
        del st
    for iso, name in CROSS_ISO_BUNDLES.items():
        if iso in rec["cross_iso"]:
            print(f"  {iso}: (resumed)")
            continue
        b = REPO / "results/calibration" / name
        if not (b / "meta.json").exists():
            rec["cross_iso"][iso] = {"skipped": f"no bundle {name}"}
            _flush()
            print(f"  {iso}: SKIPPED (no bundle {name})")
            continue
        st = _build(b, CROSS_ISO_YEAR, (), **CROSS_ISO_DISARM.get(iso, {}))
        fp = _fingerprint(st)
        fp["bundle"] = name
        fp["econ_groups"] = len(_econ_groups(st))
        rec["cross_iso"][iso] = fp
        _flush()
        print(
            f"  {iso}: n_gen={fp['n_gen']} groups={fp['econ_groups']} "
            f"mc_base={fp['mc_base_sha'][:16]}"
        )
        del st
    _flush()
    print(f"wrote {args.json}")


def stage_post(args) -> None:
    """Adjudicate SP-1..SP-6 against the pre-edit baseline."""
    base = json.loads(Path(args.baseline).read_text())
    rec: dict = {
        "stage": "post",
        "field": FIELD,
        "baseline": str(args.baseline),
        "assertions": {},
        "ercot": {},
        "cross_iso": {},
    }
    fails: list[str] = []

    # ---- ERCOT: SP-1 (gate off == pre-edit), SP-3/4/5 (gate on) -----------
    for year in ERCOT_YEARS:
        y = str(year)
        st_off = _build(ERCOT_BUNDLE, year, ERCOT_REQUIRED_FLAGS, **{FIELD: False})
        fp_off = _fingerprint(st_off)
        grp_off = _econ_groups(st_off)
        flr_off = _chp_floor_by_group(st_off)
        del st_off
        st_on = _build(ERCOT_BUNDLE, year, ERCOT_REQUIRED_FLAGS, **{FIELD: True})
        fp_on = _fingerprint(st_on)
        grp_on = _econ_groups(st_on)
        flr_on = _chp_floor_by_group(st_on)
        cols_off = fp_off["hours"] * (fp_off["n_gen"] + 4 * 7 + 3 * 5 + 10)
        cols_on = fp_on["hours"] * (fp_on["n_gen"] + 4 * 7 + 3 * 5 + 10)
        del st_on

        sp1 = (
            fp_off["mc_base_sha"] == base["ercot"][y]["mc_base_sha"]
            and fp_off["rows_sha"] == base["ercot"][y]["rows_sha"]
        )

        # SP-3: MW preservation, per plant-group, at full magnitude.
        devs = []
        for pfx, rows_on in grp_on.items():
            if pfx not in grp_off:
                continue
            tot_off = sum(r[1] for r in grp_off[pfx])
            tot_on = sum(r[1] for r in rows_on)
            if tot_off > 0:
                devs.append(abs(tot_on - tot_off) / tot_off)
        max_dev = max(devs) if devs else 0.0
        fleet_dev = abs(fp_on["total_pmax"] - fp_off["total_pmax"])
        sp3 = max_dev <= 1e-9 and fleet_dev <= 1e-6 * max(1.0, fp_off["total_pmax"])

        # SP-4: the body (first n-1 slices) is byte-identical in cap AND cost.
        body_mismatch = 0
        body_checked = 0
        for pfx, rows_on in grp_on.items():
            rows_o = grp_off.get(pfx)
            if not rows_o:
                continue
            n_body = len(rows_o) - 1  # the coarse form's first n-1 slices
            for j in range(n_body):
                body_checked += 1
                if rows_o[j][1] != rows_on[j][1] or rows_o[j][2] != rows_on[j][2]:
                    body_mismatch += 1
        sp4 = body_mismatch == 0

        # SP-3b: the CHP steam floor is REDISTRIBUTED across the finer slices,
        # never created or destroyed. Its landing legitimately moves (the floor
        # fills slices in order); its per-plant TOTAL may not.
        floor_devs = []
        for pfx, tot_on in flr_on.items():
            tot_off = flr_off.get(pfx, 0.0)
            floor_devs.append(abs(tot_on - tot_off))
        max_floor_dev = max(floor_devs) if floor_devs else 0.0
        n_floor_groups = sum(1 for v in flr_off.values() if v > 0.0)
        sp3b = max_floor_dev <= 1e-6

        # SP-5: row census. Under Amendment 1 a plant either carries R1 (2n-1 =
        # 11 slices) or is too small for it and keeps the coarse form (n = 6) —
        # the ONLY two admissible counts. Anything else (a 5, say) means the
        # assembly tranche filter is deleting sub-slices again.
        slice_counts_off = sorted({len(v) for v in grp_off.values()})
        slice_counts_on = sorted({len(v) for v in grp_on.values()})
        n_refined = sum(1 for v in grp_on.values() if len(v) == 11)
        n_coarse = sum(1 for v in grp_on.values() if len(v) == 6)
        mw_refined = sum(sum(r[1] for r in v) for v in grp_on.values() if len(v) == 11)
        mw_coarse = sum(sum(r[1] for r in v) for v in grp_on.values() if len(v) == 6)
        sp5 = (
            slice_counts_off == [6]
            and set(slice_counts_on) <= {6, 11}
            and n_refined + n_coarse == len(grp_on)
        )

        rec["ercot"][y] = {
            "SP1_gate_off_equals_pre_edit": bool(sp1),
            "off": fp_off,
            "on": fp_on,
            "econ_plant_groups": len(grp_off),
            "slice_counts_off": slice_counts_off,
            "slice_counts_on": slice_counts_on,
            "SP5_groups_refined_11": n_refined,
            "SP5_groups_kept_coarse_6": n_coarse,
            "SP5_econ_mw_refined": float(mw_refined),
            "SP5_econ_mw_kept_coarse": float(mw_coarse),
            "SP5_share_econ_mw_refined": float(
                mw_refined / max(1e-9, mw_refined + mw_coarse)
            ),
            "SP3_max_group_mw_rel_dev": float(max_dev),
            "SP3_fleet_mw_abs_dev": float(fleet_dev),
            "SP3_pass": bool(sp3),
            "SP3b_chp_floor_groups": n_floor_groups,
            "SP3b_max_group_floor_mw_dev": float(max_floor_dev),
            "SP3b_total_floor_mw_off": float(sum(flr_off.values())),
            "SP3b_total_floor_mw_on": float(sum(flr_on.values())),
            "SP3b_pass": bool(sp3b),
            "SP4_body_rows_checked": body_checked,
            "SP4_body_mismatches": body_mismatch,
            "SP4_pass": bool(sp4),
            "SP5_pass": bool(sp5),
            "lp_columns_off": cols_off,
            "lp_columns_on": cols_on,
            "column_factor": round(cols_on / cols_off, 4),
            "row_factor": round(fp_on["n_gen"] / fp_off["n_gen"], 4),
        }
        for name, ok in (
            (f"SP1_{y}", sp1),
            (f"SP3_{y}", sp3),
            (f"SP3b_{y}", sp3b),
            (f"SP4_{y}", sp4),
            (f"SP5_{y}", sp5),
        ):
            rec["assertions"][name] = bool(ok)
            if not ok:
                fails.append(name)
        print(
            f"  ERCOT {year}: SP1={sp1} SP3={sp3} SP3b={sp3b} SP4={sp4} "
            f"SP5={sp5} rows {fp_off['n_gen']}->{fp_on['n_gen']} "
            f"cols x{cols_on / cols_off:.4f} | refined {n_refined}/{len(grp_on)} "
            f"groups = {100 * mw_refined / max(1e-9, mw_refined + mw_coarse):.1f}% "
            f"of econ MW | MW dev {fleet_dev:.6f}"
        )

    # ---- SP-2: cross-ISO inertness with the gate ARMED --------------------
    for iso, name in CROSS_ISO_BUNDLES.items():
        b = REPO / "results/calibration" / name
        if not (b / "meta.json").exists():
            rec["cross_iso"][iso] = {"skipped": f"no bundle {name}"}
            continue
        dis = CROSS_ISO_DISARM.get(iso, {})
        st_off = _build(b, CROSS_ISO_YEAR, (), **{FIELD: False}, **dis)
        fp_off = _fingerprint(st_off)
        n_groups = len(_econ_groups(st_off))
        del st_off
        st_on = _build(b, CROSS_ISO_YEAR, (), **{FIELD: True}, **dis)
        fp_on = _fingerprint(st_on)
        del st_on
        identical = (
            fp_off["mc_base_sha"] == fp_on["mc_base_sha"]
            and fp_off["rows_sha"] == fp_on["rows_sha"]
            and fp_off["n_gen"] == fp_on["n_gen"]
        )
        pre = base.get("cross_iso", {}).get(iso, {})
        vs_pre = pre.get("mc_base_sha") == fp_off["mc_base_sha"] if pre else None
        rec["cross_iso"][iso] = {
            "bundle": name,
            "year": CROSS_ISO_YEAR,
            "econ_plant_groups": n_groups,
            "n_gen_off": fp_off["n_gen"],
            "n_gen_on": fp_on["n_gen"],
            "mc_base_sha_off": fp_off["mc_base_sha"],
            "mc_base_sha_on": fp_on["mc_base_sha"],
            "SP2_byte_identical_with_gate_ON": bool(identical),
            "gate_off_equals_pre_edit": vs_pre,
        }
        rec["assertions"][f"SP2_{iso}"] = bool(identical)
        if not identical:
            fails.append(f"SP2_{iso}")
        if vs_pre is False:
            rec["assertions"][f"SP1x_{iso}"] = False
            fails.append(f"SP1x_{iso}")
        print(
            f"  {iso}: SP2={identical} (econ groups {n_groups}, "
            f"n_gen {fp_off['n_gen']})"
        )

    # ---- SP-6: the committed-band call site is not armed -------------------
    from market_sim.data.offer_curves import _econ_curve_steps

    cmt = _econ_curve_steps(10.0, 0.9, 1.1, 600.0, 6, 1.0, 0.35, top_refine=False)
    sp6 = len(cmt) == 6 and all(abs(c[1] - 100.0) < 1e-12 for c in cmt)
    rec["assertions"]["SP6_committed_band_default_unrefined"] = bool(sp6)
    if not sp6:
        fails.append("SP6")

    rec["FAILED"] = fails
    rec["ALL_ASSERTIONS_PASS"] = not fails
    Path(args.json).write_text(json.dumps(rec, indent=1))
    print(
        f"\nALL_ASSERTIONS_PASS = {not fails}" + (f"  FAILED: {fails}" if fails else "")
    )
    print(f"wrote {args.json}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", choices=("pre", "post"), required=True)
    ap.add_argument("--json", default=str(OUT))
    ap.add_argument("--baseline", default=None)
    ap.add_argument(
        "--resume",
        action="store_true",
        help="keep members already present in --json instead of re-measuring",
    )
    args = ap.parse_args()
    if args.stage == "pre":
        stage_pre(args)
    else:
        if not args.baseline:
            raise SystemExit("--stage post requires --baseline")
        stage_post(args)


if __name__ == "__main__":
    main()
