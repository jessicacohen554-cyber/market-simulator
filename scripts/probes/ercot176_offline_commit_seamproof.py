"""Seam proof for the ERCOT-176 offline-increment SLOW-START tier.

Executes, on the REAL keeper solve inputs for every scored year, the six
assertions pre-registered in ``docs/PRECOMMIT-ercot176-offline-increment-
2026-08-07.md`` §4 (as corrected by its Amendment 1, which moved the tier from
an additive ``mc_bid_adjust`` markup to a bid-LEVEL ``p1_bid_max_target``
reconciliation), plus SP-7 — the inertness adjudication that the pre-registered
falsifier P-2 turns on.

Run BEFORE any solve. Every assertion is checked against the fleet, offer
surfaces and net load the LP itself would see, reconstructed from the keeper
bundle with no LP built.

Usage::

    python scripts/probes/ercot176_offline_commit_seamproof.py
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

BUNDLE = REPO / "results/calibration/ercot168_yearcurves_B"
YEARS = (2023, 2024, 2025)
OUT = REPO / "results/calibration/ercot176_offline_commit_seamproof.json"

# The committed CT sub-tree hash at HEAD BEFORE the CC extension
# (git show HEAD:data/raw/_validation-source/ercot_faststart_pool_condbinned.json).
# SP-6: the ERCOT-105 derive-integrity check, applied to the WHOLE CT sub-tree
# rather than only the years the extension did not touch.
CT_SHA256_BEFORE = "7f02b6f5183bca7a828e0d79656a0587a9716b82cd0deda296e9ca62595e32fe"

# The keeper's own armed gates, asserted on the reconstruction so the proof
# measures the keeper's surface and not a drifted one (the miso-116 trap).
ERCOT_REQUIRED_FLAGS = (
    "ercot_offer_surface_cleared_share",
    "ercot_offer_surface_cleared_share_rt",
    "ercot_faststart_pool_offer",
)

ARTIFACT = REPO / "data/raw/_validation-source/ercot_faststart_pool_condbinned.json"


def _net_load(state: dict) -> np.ndarray:
    """The LP-served net load the offer surfaces condition on."""
    demand = state["demand"]
    return (
        demand.sum(axis=0)
        - (state["solar_cap"][:, None] * state["solar_cf"]).sum(axis=0)
        - (state["wind_cap"][:, None] * state["wind_cf"]).sum(axis=0)
    )


def _armed(config, **over):
    """A copy of ``config`` with ``over`` applied (pydantic or dataclass)."""
    if hasattr(config, "model_copy"):
        return config.model_copy(update=over)
    return dataclasses.replace(config, **over)


def run_year(year: int) -> dict:
    """Return the seam-proof record for ``year``."""
    from market_sim.data.fleet import (
        build_ercot_faststart_pool_markup,
        build_ercot_offline_commit_target,
    )
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, _meta = reconstruct_bundle_fleet(
        BUNDLE, year, required_flags=ERCOT_REQUIRED_FLAGS, required_sequences=()
    )
    cfg_off = state["config"]
    fa, fleet, mc_base = state["fleet_arrays"], state["fleet"], state["mc_base"]
    nl = _net_load(state)
    rec: dict = {"year": year, "n_gen": int(mc_base.shape[0])}

    # SP-2a — gate OFF is a no-op (the control's own path).
    off = build_ercot_offline_commit_target(fa, fleet, mc_base, nl, cfg_off, year)
    rec["SP2a_gate_off_is_none"] = off is None

    cfg_on = _armed(cfg_off, ercot_offline_commit_offer=True)

    # SP-2b — year-scoping: a year absent from the artifact is byte-identical.
    # Proven by pointing the tier at an artifact whose CC block is empty.
    empty = json.loads(ARTIFACT.read_text())
    empty["CC"] = {"years": {}}
    tmp = OUT.parent / f"_ercot176_empty_cc_{year}.json"
    tmp.write_text(json.dumps(empty))
    try:
        cfg_empty = _armed(cfg_on, ercot_offline_commit_offer_path=str(tmp))
        rec["SP2b_year_absent_is_none"] = (
            build_ercot_offline_commit_target(fa, fleet, mc_base, nl, cfg_empty, year)
            is None
        )
    finally:
        tmp.unlink(missing_ok=True)

    # SP-1 — non-ERCOT ISOs never see the tier.
    rec["SP1_non_ercot_is_none"] = (
        build_ercot_offline_commit_target(
            fa, fleet, mc_base, nl, _armed(cfg_on, iso="PJM"), year
        )
        is None
    )

    # SP-7 — the inertness adjudication on the REAL fleet (falsifier P-2).
    on = build_ercot_offline_commit_target(fa, fleet, mc_base, nl, cfg_on, year)
    rec["SP7_armed_is_none"] = on is None

    # The measured boundary the adjudication turns on.
    art = json.loads(ARTIFACT.read_text())
    cc_tbl = art.get("CC", {}).get("years", {}).get(str(year), {})
    frac = [float(x) for x in cc_tbl.get("pool_frac", ())]
    rec["cc_pool_frac_by_bin"] = frac
    rec["cc_pool_frac_max"] = round(max(frac), 6) if frac else None
    rec["cc_ladder_p70_by_bin"] = [
        round(float(lad[3][1]), 3) for lad in cc_tbl.get("ladder", ())
    ]

    # The eligible row universe — so "inert" is distinguished from "no rows".
    from market_sim.config.constants import (
        OFFLINE_COMMIT_MIN_DOWN_HOURS_MAX,
        OFFLINE_COMMIT_MIN_DOWN_HOURS_MIN,
        OFFLINE_COMMIT_MIN_RUN_HOURS_MAX,
    )

    # Physics is recorded on the ``committed`` tranche only, so eligibility is
    # a PLANT property inherited by the plant's bid rows (Amendment 2).
    pmax = fa.pmax
    mean_mc = mc_base.mean(axis=1)
    cc_groups = {"CC_REGULAR"}
    prefixes: dict[str, list[int]] = {}
    for g, gen in enumerate(fleet):
        if (getattr(gen, "plant_group", None) or "") in cc_groups:
            prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)

    n_elig_plants = 0
    n_elig = 0
    n_excl_minrun = 0
    top_share = 0.0
    for rows in prefixes.values():
        md = max(float(getattr(fleet[g], "min_down_hours", 0) or 0) for g in rows)
        mr = max(float(getattr(fleet[g], "min_run_hours", 0) or 0) for g in rows)
        in_md = (
            OFFLINE_COMMIT_MIN_DOWN_HOURS_MIN <= md <= OFFLINE_COMMIT_MIN_DOWN_HOURS_MAX
        )
        if in_md and mr > OFFLINE_COMMIT_MIN_RUN_HOURS_MAX:
            n_excl_minrun += 1
        if not (in_md and mr <= OFFLINE_COMMIT_MIN_RUN_HOURS_MAX):
            continue
        n_elig_plants += 1
        n_elig += sum(
            1
            for g in rows
            if fleet[g].unit_id.rpartition("_")[2].startswith(("econ", "peak"))
        )
        arr = np.asarray(rows, dtype=int)
        order = arr[np.argsort(mean_mc[arr], kind="stable")]
        caps = pmax[order]
        tot = caps.sum()
        if tot <= 0:
            continue
        mids = (np.cumsum(caps) - 0.5 * caps) / tot
        top_share = max(top_share, float(mids.max()))
    rec["n_cc_plants"] = len(prefixes)
    rec["n_physics_eligible_plants"] = n_elig_plants
    rec["n_physics_eligible_rows"] = n_elig
    rec["n_plants_excluded_by_min_run"] = n_excl_minrun

    # The decisive geometry: a row is priced only if its within-plant share
    # midpoint exceeds 1 - pool_frac. Largest midpoint in the ELIGIBLE
    # universe against the loosest (largest) measured pool_frac.
    rec["max_within_plant_share_midpoint"] = round(top_share, 6)
    rec["boundary_min_over_bins"] = round(1.0 - max(frac), 6) if frac else None
    rec["geometry_priced_any_row"] = bool(
        frac and top_share > (1.0 - max(frac))
    )

    if on is None:
        # SP-3/4/5 are vacuous when the tier owns no row-hour — recorded as
        # such with the reason, never silently omitted.
        rec["SP3_disjoint_from_ct_pool"] = "VACUOUS (tier owns no row-hour)"
        rec["SP4_max_reconciliation"] = "VACUOUS (tier owns no row-hour)"
        rec["SP5_no_markdown"] = "VACUOUS (tier owns no row-hour)"
        return rec

    target, mask = on
    rec["n_priced_rows"] = int(mask.any(axis=1).sum())
    rec["n_priced_rowhours"] = int(mask.sum())

    # SP-3 — disjoint from the ERCOT-88 fast-start pool, by physics.
    fsp = build_ercot_faststart_pool_markup(fa, fleet, mc_base, nl, cfg_on, year)
    if fsp is None:
        rec["SP3_disjoint_from_ct_pool"] = "VACUOUS (CT pool owns no row-hour)"
    else:
        rec["SP3_disjoint_from_ct_pool"] = bool(not (mask & fsp[1]).any())

    # SP-4 — the composed P1 bid equals max(control bid, tier level) on the
    # tier's rows: reconciliation, NOT ladder + startup.
    from market_sim.pipeline.solve import apply_bid_max_target

    ctrl_bid = mc_base + 7.0  # a positive stand-in for markup + adjustments
    composed = apply_bid_max_target(ctrl_bid, target)
    rec["SP4_max_reconciliation"] = bool(
        np.allclose(composed[mask], np.maximum(ctrl_bid, target)[mask])
        and np.allclose(composed[~mask], ctrl_bid[~mask])
    )
    # SP-5 — never lowers a bid, anywhere.
    rec["SP5_no_markdown"] = bool((composed >= ctrl_bid - 1e-12).all())
    return rec


def main() -> None:
    """Run the seam proof over every scored year and write the record."""
    art = json.loads(ARTIFACT.read_text())
    ct_sha = hashlib.sha256(
        json.dumps(art["CT"], sort_keys=True).encode()
    ).hexdigest()
    record: dict = {
        "precommit": "docs/PRECOMMIT-ercot176-offline-increment-2026-08-07.md",
        "bundle": str(BUNDLE.relative_to(REPO)),
        "SP6_ct_subtree_sha256": ct_sha,
        "SP6_ct_subtree_sha256_before": CT_SHA256_BEFORE,
        "SP6_ct_byte_identical": ct_sha == CT_SHA256_BEFORE,
        "years": [],
    }
    for y in YEARS:
        rec = run_year(y)
        record["years"].append(rec)
        print(json.dumps(rec, indent=1))

    checks = [record["SP6_ct_byte_identical"]]
    for rec in record["years"]:
        checks += [
            rec["SP1_non_ercot_is_none"],
            rec["SP2a_gate_off_is_none"],
            rec["SP2b_year_absent_is_none"],
        ]
        for k in ("SP3_disjoint_from_ct_pool", "SP4_max_reconciliation", "SP5_no_markdown"):
            if isinstance(rec[k], bool):
                checks.append(rec[k])
    record["ALL_ASSERTIONS_PASS"] = all(checks)
    record["ARM_PROVABLY_INERT"] = all(r["SP7_armed_is_none"] for r in record["years"])
    OUT.write_text(json.dumps(record, indent=1))
    print(f"\nALL_ASSERTIONS_PASS = {record['ALL_ASSERTIONS_PASS']}")
    print(f"ARM_PROVABLY_INERT  = {record['ARM_PROVABLY_INERT']}")
    print(f"wrote {OUT}")
    if not record["ALL_ASSERTIONS_PASS"]:
        raise SystemExit("SEAM PROOF FAILED — stop the line")


if __name__ == "__main__":
    main()
