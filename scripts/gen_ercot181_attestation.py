"""Generate the ercot-181 pair attestations from the ercot-176 keeper base.

``results/calibration/ercot181_control_A`` is the run176 keeper recipe
replayed at the ercot-181 HEAD with zero deltas (its prices are array-equal
to the keeper's in all three years — the keeper's next consecutive
reproduction), so its attestation is the committed ercot176_control_A
attestation with the governance ``attested_by`` re-attested for this run and
the three ``price_tail`` model-class exception magnitudes re-confirmed at
this run's own tail counts.

``results/calibration/ercot181_positiontail_B`` is the control plus ONE
mechanism delta — ``ercot_offer_surface_position_tail=true`` (matrix §5.1
item 23, the pre-registered position-tail completion,
``docs/PRECOMMIT-ercot181-quantity-position-2026-08-09.md`` + its pre-solve
Amendment 1) — so its attestation additionally carries one ADDED measured
DOF-ledger entry (``n_scalars 0``, ``free_parameters_added: 0``: the tails
are the measured populations' own empirical quantile functions on their own
support; no grid, no clamp, no scalar was chosen), with the tail-count
magnitudes read from the ARM's own registered payload.

Reads committed artifacts only; no solve. Run AFTER both runs are registered:
    python scripts/gen_ercot181_attestation.py \
        --control-run-id 2026-08-09-run181-control-positiontail-pair \
        --arm-run-id 2026-08-09-run181-position-tail
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "results/calibration/ercot176_control_A/calibration_attestation.json"
BUNDLES = {
    "control": REPO / "results/calibration/ercot181_control_A",
    "arm": REPO / "results/calibration/ercot181_positiontail_B",
}
ACTUAL_TAIL = {2023: 181, 2024: 53, 2025: 31}  # committed actual_tail.json counts

NEW_ENTRY = {
    "name": "ercot_offer_surface_position_tail (position-tail completion of "
    "the measured offer surfaces' p90-truncated ladders)",
    "where": "run_config.scenario_config.ercot_offer_surface_position_tail",
    "identification": "measured",
    "n_scalars": 0,
    "source": (
        "PRECOMMIT-ercot181-quantity-position-2026-08-09.md §2-§3 + pre-solve "
        "Amendment 1: the wall (RT/SCED leg) and fast-start pool ladders' "
        "position axes completed above their frozen p90 grid point with THE "
        "SAME MW-weighted quantile statistic on each population's own "
        "measured support (every distinct cumulative-MW-fraction step point, "
        "HCAP-clipped by the parent segment construction — "
        "scripts/lib/positiontail.py); rows read at their own rel, the "
        "members' unchanged position mapping. No grid, level, conditioner, "
        "clamp or scalar was chosen; sub-p90 ladders byte-identical to the "
        "frozen artifacts; tails 2023-only (the frozen 2024/2025 anchors' "
        "source corpus was purged 2026-07-22 and cannot be reproduced — "
        "zero-support at year grain, arm byte-identical to control there). "
        "Derives: --position-tail modes of derive_ercot_sced_offer_wall / "
        "derive_ercot_faststart_pool, each asserting the re-derived ladder "
        "REPRODUCES the frozen artifact before appending tails (rule 23: new "
        "vintage for a new pre-registered gate). Seam proof: "
        "results/calibration/ercot181_positiontail_seamproof.json "
        "(ALL_ASSERTIONS_PASS true; SP-α1 delta confined to rel>0.9 "
        "row-hours; SP-α2 null encoding byte-identical — position, never "
        "level)."
    ),
    "free_parameters_added": 0,
}

ATTESTED_BY = {
    "control": (
        "ercot-181 {today} — the run176 keeper recipe REPLAYED AT HEAD with "
        "ZERO deltas (scripts/replay_keeper.py, no --set), solved in-session "
        "across the full 2023-2025 span as the pre-registered A/B control "
        "(docs/PRECOMMIT-ercot181-quantity-position-2026-08-09.md §9); its "
        "P1 price series are ARRAY-EQUAL to the run176 keeper's in all three "
        "years (the keeper's next consecutive reproduction at a new HEAD). "
        "The DOF ledger and the exceptions ledger are INHERITED UNCHANGED "
        "from the ercot176_control_A attestation because the recipe is "
        "unchanged — no parameter was added, removed, re-identified or "
        "re-tuned on this run; n_entries stays 13 with n_residual 6. The "
        "session's mechanism ercot_offer_surface_position_tail is "
        "DEFAULT-OFF and NOT armed here. Rule 22: 2023-2025 only; ERCOT "
        "holds no complete and no final marker and no out-of-training year "
        "was solved, scored, read or registered."
    ),
    "arm": (
        "ercot-181 {today} — the control plus ONE mechanism delta: "
        "ercot_offer_surface_position_tail=true (scripts/replay_keeper.py "
        "--set), the pre-registered position-tail completion of the wall/"
        "pool ladders' p90-truncated position axes "
        "(docs/PRECOMMIT-ercot181-quantity-position-2026-08-09.md + pre-"
        "solve Amendment 1; matrix §5.1 item 23). The completion appends the "
        "measured populations' own empirical quantile functions above p90 "
        "(2023 only — the 2024/2025 frozen anchors' source corpus is purged "
        "and unreproducible, so those years are byte-identical to control "
        "by the zero-support rule, verified array-equal at scoring). Zero "
        "fitted scalars; one measured DOF-ledger entry ADDED (n_scalars 0, "
        "free_parameters_added 0); n_residual unchanged at 6. Seam proof "
        "committed pre-solve (results/calibration/"
        "ercot181_positiontail_seamproof.json, ALL_ASSERTIONS_PASS true). "
        "Measured outcome: INERT-ON-THE-OBJECT — 22 spring hours move by "
        "+$0.006..+$0.57, annual lw +$0.0004/MWh, the summer object hours / "
        "tail counts / shed counts byte-unmoved (G-SHED 4/2/0 unchanged; "
        "every pre-registered gate PASSES). Rule 22: 2023-2025 only; no "
        "out-of-training year was solved, scored, read or registered."
    ),
}


def _tail_counts(run_id: str) -> dict[int, int]:
    """Model RT tail-hour counts from the REGISTERED payload (the judged
    quantity: ``years[y].ordc.hoursGt200.model``, exactly what C3c scores)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "cv", str(REPO / "scripts/calibration_verdict.py")
    )
    cv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cv)
    payload = cv._decode_run_js(
        (REPO / "frontend/data/backcast/runs" / f"{run_id}.js").read_text()
    )
    out: dict[int, int] = {}
    for y in (2023, 2024, 2025):
        out[y] = int(payload["years"][str(y)]["ordc"]["hoursGt200"]["model"])
    return out


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control-run-id", required=True)
    ap.add_argument("--arm-run-id", required=True)
    args = ap.parse_args()
    run_ids = {"control": args.control_run_id, "arm": args.arm_run_id}

    base = json.loads(BASE.read_text())
    today = date.today().isoformat()
    for kind, bundle in BUNDLES.items():
        att = json.loads(json.dumps(base))  # deep copy
        counts = _tail_counts(run_ids[kind])
        for exc in att.get("exceptions", []):
            y = exc.get("year")
            if exc.get("criterion") == "price_tail" and y in ACTUAL_TAIL:
                exc["magnitude"] = (
                    f"model {counts[y]} h vs actual RT {ACTUAL_TAIL[y]} h "
                    f"> $200/MWh (re-confirmed at ercot-181 {kind})"
                )
        if kind == "arm":
            fp = att["free_parameters"]
            fp["entries"] = fp["entries"] + [NEW_ENTRY]
            fp["n_entries"] = len(fp["entries"])
            # n_residual unchanged: the new entry is measured, not residual.
        att["governance"]["attested_by"] = ATTESTED_BY[kind].format(today=today)
        dest = bundle / "calibration_attestation.json"
        dest.write_text(json.dumps(att, indent=1))
        print(f"wrote {dest} (tail counts {counts})")


if __name__ == "__main__":
    main()
